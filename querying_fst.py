# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pickle, json, sys, os, timeit
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
import pywrapfst as fst
import specializer
import math, string

from utilfst import printstrings

use_grapheme_confusion = False

if len(sys.argv)==1:
    print('Usage: python querying.py index_fst_file.fst index_arr_file.pd queries_file.xml output_file.xml OPT:n_best')
    sys.exit()
elif len(sys.argv)==5:
    index_fst_file = sys.argv[1]
    index_arr_file = sys.argv[2]
    queries_file = sys.argv[3]
    output_file = sys.argv[4]
elif len(sys.argv)==6:
    index_arr_file = sys.argv[1]
    index_fst_file = sys.argv[2]
    queries_file = sys.argv[3]
    output_file = sys.argv[4]
    use_grapheme_confusion = True
    n_best = int(sys.argv[5])
    # alpha = float(sys.argv[6])

# To inspect an XML file: "cat output/reference.xml | xmllint --format - "
# To inspect a JSON file: "python -m json.tool index/reference.json"
# python querying_fst.py index_fst/reference.fst index_fst/reference_arr.pd lib/kws/queries.xml output_fst/reference_fst_out.xml &
with open(index_arr_file,'rb') as f: # with open('testing/test.json','rb') as f:
    words = pickle.load(f)

index_fst = fst.Fst.read(index_fst_file)
printable_ST = fst.SymbolTable().read_text('FSTs/symbol_table.txt')
sigma_fst = fst.Fst.read('/home/fc443/MLSALT5/Practical/FSTs/sigma.fst')

# Load grapheme_confusion FST
if use_grapheme_confusion:
    printable_ST = fst.SymbolTable().read_text('FSTs/symbol_table.txt')
    grapheme_confusion = fst.Fst.read('FSTs/grapheme_confusion.fst')
    grapheme_confusion = grapheme_confusion.set_input_symbols(printable_ST)
    grapheme_confusion = grapheme_confusion.set_output_symbols(printable_ST)
    # print grapheme_confusion.num_arcs(0)
    grapheme_confusion.prune(weight = 10)
    # print grapheme_confusion.num_arcs(0)
    # grapheme_confusion.arcsort()

# index_name = '.'.join(index_file.split('/')[-1].split('.')[0:-1])
# fst_vocab = fst.Fst.read('FSTs/vocab_'+index_name+'.fst')
# fst_vocab = fst_vocab.set_input_symbols(printable_ST)
# fst_vocab = fst_vocab.set_output_symbols(printable_ST)

def save_autom(autom, name):
    path = '/home/fc443/MLSALT5/Practical/FSTs/'+name
    autom.draw(path+'.gv', title=name, portrait=True)
    os.system("dot -Teps %s.gv -o %s.eps" % (path, path))
    
    f = open(path+'.txt', 'w')
    for line in autom.text():
        f.write(line)

def alternatives(sequence):
    # sequence is a list of words
    # produces the n_best alternative to sequence made of sub-units that are in words
    
    # Build FST
    compiler_sequence = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
    c = 0
    for word in sequence:
        for char in word:
            print >> compiler_sequence, str(c) + ' ' + str(c + 1) + ' ' + char + ' ' + char
            c = c+1
        print >> compiler_sequence, str(c) + ' ' + str(c + 1) + ' </w> </w>'
        c = c+1
    print >> compiler_sequence, str(c)
    fst_sequence = compiler_sequence.compile()
    fst_sequence = fst_sequence.set_input_symbols(printable_ST)
    fst_sequence = fst_sequence.set_output_symbols(printable_ST)

    composition = fst.compose(fst_vocab, fst.compose(grapheme_confusion, fst_sequence)).rmepsilon().arcsort()
    # composition.prune(weight = 3)
    alters = printstrings(composition, nshortest=n_best, syms=printable_ST, weight=True)
    scores = []
    if alters:
        print alters
        scores = [float(alt[1]) for alt in alters]
        alters = [alt[0].split(' </w>')[:-1] for alt in alters]
        alters = [[''.join(word.split(' ')) for word in alt] for alt in alters]
    return alters, scores

def perform_query(query):
    # perform the query
    if query[0] in words:
        potential_hits = words[query[0]]
    else:   
        potential_hits = []
    hits = []
    for potential_hit in potential_hits:
        success = True
        
        dur = potential_hit['dur']
        score = potential_hit['score']
        scores = [score]
        
        word_in_index = potential_hit
        for word in query[1:]: #check if 'word' can be found on the path of potential_hit.
            if word_in_index['following_word'] and word == word_in_index['following_word'][0]:
                idx = word_in_index['following_word'][1]
                word_in_index = words[word][idx]
                dur = dur + word_in_index['dur']
                score = score * word_in_index['score']
                
                scores.extend([word_in_index['score']])
            else:
                success = False
                break

        if success:
            hits.extend([{'file': potential_hit['filename'], 
                          'channel': str(potential_hit['channel']), 
                          'tbeg': str(potential_hit['tbeg']), 
                          'dur': str(dur), 
                          'score': str(score),#**(1.0/(len(query)+1))), 
                          'decision': 'YES'}])
    return hits      

def format_fst_string(input):
    input = [int(c) for c in input.split(' ')]
    output = [input[0]]
    for c in input:
        if output[-1] != c:
            output.append(c)

    return output

def perform_query_fst(query):
    # print query
    # create a fsa for query
    query_compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
    # print >> query_compiler, '0 0 <eps> <eps>'
    state = 0
    for word in query:
        print >> query_compiler, '%d %d <w> <w>' % (state, state+1)
        state += 1
        for c in word:
            print >> query_compiler, '%d %d %s %s' % (state, state+1, c, c)
            state += 1
        print >> query_compiler, '%d %d </w> </w>' % (state, state+1)
        state += 1
    print >> query_compiler, str(state)
    query_fst = query_compiler.compile()

    query_fst.concat(sigma_fst)
    query_fst = sigma_fst.copy().concat(query_fst).rmepsilon()#.arcsort()

    compos_fst = fst.compose(index_fst, query_fst).rmepsilon()
    
    eps_rm_compos_compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
    s = compos_fst.text().split('\n')
    for line in s:
        new_line = line.split('\t')
        if len(new_line)==4 and new_line[3] == '<eps>':
            new_line[2] = '<eps>'
        print >> eps_rm_compos_compiler, '\t'.join(new_line)
    compos_fst = eps_rm_compos_compiler.compile().rmepsilon()

    # save_autom(compos_fst, 'trash/c'+query[0])
    # save_autom(query_fst, 'trash/q'+query[0])
    hits = printstrings(compos_fst, nshortest=2**10, syms=printable_ST, weight=True, project_output=False)
    print hits
    hits = [(format_fst_string(hit[0]), hit[1]) for hit in hits]
    
    out_hits = []

    for hit in hits:
        filename = words[hit[0][0]][0]
        channel = words[hit[0][0]][1]
        tbeg = float(words[hit[0][0]][2])
        dur = 0
        score = 1
        for idx in hit[0]:
            dur += float(words[idx][3])
            score *= float(words[idx][5])
        out_hits.append({'file': filename, 
                         'channel': str(channel), 
                         'tbeg': str(tbeg), 
                         'dur': str(dur), 
                         'score': str(score),#**(1.0/(len(query)))), 
                         'decision': 'YES'})
    # print len(out_hits)
    return out_hits

queries_tree = ET.parse(queries_file)
# queries_tree = ET.parse('testing/test_queries.xml')
queries_root = queries_tree.getroot()

root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})

for query_leaf in queries_root:
    # Parse the query
    kwid = query_leaf.attrib['kwid']
    print kwid
    query = query_leaf[0].text.split(' ')
    
    start_time = timeit.default_timer()
    hits = perform_query_fst(query)    
    elapsed = timeit.default_timer() - start_time

    ######
    # if not hits and use_grapheme_confusion:
    #     # print "No hits for query", kwid, query 
    #     alt_queries, scores = alternatives(query)
    #     for alt_query, score in zip(alt_queries, scores): 
    #         alt_hits = perform_query(alt_query)
    #         for alt_hit in alt_hits:
    #             alt_hit['score'] = str(float(alt_hit['score']) + alpha * score)
    #         hits.extend(alt_hits) 
    ######

    #####
    # save it in the XML tree
    query_tree = ET.SubElement(root, 'detected_kwlist', {'kwid': kwid, 'oov_count': '0', 'search_time': str(elapsed)})
    
    score_rn_cst = sum([float(hit['score']) for hit in hits]) # the score renormalization constant
    for hit in hits:
        # hit['score'] = str(float(hit['score'])/score_rn_cst)
        ET.SubElement(query_tree, 'kw', hit)
    #####

# save the XML tree
ET.ElementTree(root).write(output_file, encoding='UTF-8', xml_declaration=False)
# ET.ElementTree(root).write('testing/test_output.xml', encoding='UTF-8', xml_declaration=False)
