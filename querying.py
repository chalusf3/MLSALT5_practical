import xml.etree.ElementTree as ET
import json, sys, os#, time
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
import pywrapfst as fst
import specializer
import math, string

from utilfst import printstrings

use_grapheme_confusion = False

if len(sys.argv)==1:
    print('Usage: python querying.py index_file.json queries_file.xml output_file.xml OPT:n_best')
    sys.exit()
elif len(sys.argv)==4:
    index_file = sys.argv[1]
    queries_file = sys.argv[2]
    output_file = sys.argv[3]
elif len(sys.argv)==6:
    index_file = sys.argv[1]
    queries_file = sys.argv[2]
    output_file = sys.argv[3]
    use_grapheme_confusion = True
    n_best = int(sys.argv[4])
    alpha = float(sys.argv[5])


with open(index_file,'rb') as f: # with open('testing/test.json','rb') as f:
    words = json.load(f)

# To inspect an XML file: "cat output/reference.xml | xmllint --format - "
# To inspect a JSON file: "python -m json.tool index/reference.json"

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

index_name = '.'.join(index_file.split('/')[-1].split('.')[0:-1])
fst_vocab = fst.Fst.read('FSTs/vocab_'+index_name+'.fst')
fst_vocab = fst_vocab.set_input_symbols(printable_ST)
fst_vocab = fst_vocab.set_output_symbols(printable_ST)

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
#     composition.prune(weight = 3)
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

queries_tree = ET.parse(queries_file)
# queries_tree = ET.parse('testing/test_queries.xml')
queries_root = queries_tree.getroot()

root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})

for query_leaf in queries_root:
    # Parse the query
    kwid = query_leaf.attrib['kwid']
    print kwid
    query = query_leaf[0].text.split(' ')
    
    # save it in the XML tree
    query_tree = ET.SubElement(root, 'detected_kwlist', {'kwid': kwid, 'oov_count': '0', 'search_time': '0.0'})
        
    hits = perform_query(query)    
    
    if not hits and use_grapheme_confusion:
#         print "No hits for query", kwid, query 
        alt_queries, scores = alternatives(query)
        for alt_query, score in zip(alt_queries, scores): 
            alt_hits = perform_query(alt_query)
            for alt_hit in alt_hits:
                alt_hit['score'] = str(float(alt_hit['score']) + alpha * score)
            hits.extend(alt_hits) 

    score_rn_cst = sum([float(hit['score']) for hit in hits]) # the score renormalization constant
    for hit in hits:
        hit['score'] = str(float(hit['score'])/score_rn_cst)
        ET.SubElement(query_tree, 'kw', hit)

# save the XML tree
ET.ElementTree(root).write(output_file, encoding='UTF-8', xml_declaration=False)
# ET.ElementTree(root).write('testing/test_output.xml', encoding='UTF-8', xml_declaration=False)
