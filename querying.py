# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import joblib, pickle
import json, sys, os, argparse#, time
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
import pywrapfst as fst
import specializer
import math, string
from utilfst import printstrings

# To inspect an XML file: "cat output/reference.xml | xmllint --format - "
# To inspect a JSON file: "python -m json.tool index/reference.json"

# python -m cProfile querying.py index/decode.json lib/kws/queries.xml tmp.xml --n_best 1 --alpha 1 --gamma 2

parser = argparse.ArgumentParser()
parser.add_argument('index_file', help='Index file (.ctm)')
parser.add_argument('queries_file', help='Queries file (.xml)')
parser.add_argument('output_file', help='Output hits file (.xml)')
parser.add_argument('--n_best', help='Number of alternatives for OOV')
parser.add_argument('--alpha', help='combination of grapheme score and confidence score')
parser.add_argument('--gamma', help='exponent for score normalization')
parser.add_argument('--rerun', help='boolean on whether compositions should be reperformed')

use_grapheme_confusion = False

args = parser.parse_args()
index_file = args.index_file
queries_file = args.queries_file
output_file = args.output_file
alpha = float(args.alpha) if args.alpha else 1.0
if args.n_best:
    use_grapheme_confusion = True
    if not args.alpha:
        print "querying.py Argument warning: alpha was defaulted to %.2f" % alpha
    n_best = int(args.n_best)
if args.gamma:
    gamma = float(args.gamma)
else:
    gamma = None # don't perform score renormalization

if args.rerun:
    rerun = bool(int(args.rerun))
else:
    rerun = False

with open(index_file,'rb') as f: # with open('testing/test.json','rb') as f:
    words = json.load(f)

# Load grapheme_confusion FST
if use_grapheme_confusion:
    printable_ST = fst.SymbolTable().read_text('FSTs/symbol_table.txt')
    grapheme_confusion = fst.Fst.read('FSTs/grapheme_confusion.fst')
    index_name = '.'.join(index_file.split('/')[-1].split('.')[0:-1])
    fst_vocab = fst.Fst.read('FSTs/vocab_'+index_name+'.fst')
    error_maker_fst = fst.Fst.read('FSTs/error_maker.fst')

    # print "start"
    # compos_graph_vocab = fst.compose(grapheme_confusion.invert(), fst_vocab)
    # tmp_compos = fst.compose(error_maker_fst, fst_vocab).rmepsilon()
    # print "end"

    # print "start"
    # erroneous_vocab = fst.Fst.read('FSTs/erroneous_vocab'+index_name+'.fst')
    # print "end"

def alternatives(sequence):
    # sequence is a list of words
    # this function produces the n_best IV alternatives to sequence by replacing graphemes
    filename = index_name+'_'+'_'.join(sequence)
    filename = filename.replace("'", "")
    file_path = 'FSTs/compositions/'+filename+'.pd'

    if rerun:
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

        # composition occurs in tropical semiring
        # composition = fst.compose(fst_vocab, fst.compose(grapheme_confusion, fst_sequence)).rmepsilon().arcsort()

        composition = fst.intersect(fst.compose(fst_sequence, error_maker_fst).project(project_output=True), fst_vocab).rmepsilon().arcsort()
        # composition = fst.compose(fst_sequence, compos_graph_vocab).rmepsilon().arcsort()

        # composition = fst.compose(fst.compose(fst_sequence, error_maker_fst).project(project_output=True).rmepsilon(), fst_vocab).rmepsilon().arcsort()
        # composition = fst.compose(fst_sequence, tmp_compos).project(project_output=True).rmepsilon().arcsort()
        # composition = fst.compose(fst_sequence, error_maker_fst).project(project_output=True).rmepsilon().arcsort()
        alters = printstrings(composition, nshortest=n_best, syms=printable_ST, weight=True, project_output=False)
        scores = []
        if alters:
            scores = [math.exp(-float(alt[1])) for alt in alters]
            alters = [alt[0].split(' </w>')[:-1] for alt in alters]
            alters = [[''.join(word.split(' ')) for word in alt] for alt in alters]
            # print query, alters
        # print alters
        pickle.dump({'alters': alters, 'scores': scores}, open(file_path,'w'))
    else:
        d = pickle.load(open(file_path))
        alters = d['alters']
        scores = d['scores']
        alters = alters[0:n_best]
        scores = scores[0:n_best]
    
    return alters, scores

def perform_query(query):    
    potential_hits = words.get(query[0], [])

    hits = []
    for potential_hit in potential_hits:
        success = True
        
        dur = potential_hit['dur']
        score = potential_hit['score']
        scores = [score]
        
        word_in_index = potential_hit
        for word in query[1:]: #check if 'word' can be found on the path of potential_hit.
            # print word
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
            score = score**(1.0 / len(query))

            hits.extend([{'file': potential_hit['filename'], 
                          'channel': str(potential_hit['channel']), 
                          'tbeg': str(potential_hit['tbeg']), 
                          'dur': str(dur), 
                          'score': str(score),
                          'decision': 'YES'}])
    return hits      

def perform_query_with_alt(query):
    hits = perform_query(query)
    if not hits and use_grapheme_confusion:
        alt_queries, scores = alternatives(query)
        # print alt_queries
        for alt_query, score in zip(alt_queries, scores): 
            alt_hits = perform_query(alt_query)
            for alt_hit in alt_hits:
                alt_hit['score'] = str(float(alt_hit['score'])*float(score)**float(alpha))
            hits.extend(alt_hits)
    if gamma:
        score_rn_cst = sum([float(hit['score'])**gamma for hit in hits]) # the score renormalization constant
        for hit in hits:
            hit['score'] = str(float(hit['score'])**gamma/score_rn_cst)
    return hits

queries_tree = ET.parse(queries_file)
# queries_tree = ET.parse('testing/test_queries.xml')
queries_root = queries_tree.getroot()
queries = []
for query_leaf in queries_root:
    query = query_leaf[0].text.split(' ')
    kwid = query_leaf.attrib['kwid']
    queries.append(query)

root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})

if False:
    hits_list = []
    for query in queries:
        hits_list.append(perform_query_with_alt(query))
else:
    def monitor_perf(idx, query):
        hits = perform_query_with_alt(query)
        return hits
    hits_list = joblib.Parallel(n_jobs=12)(joblib.delayed(perform_query_with_alt)(query) for idx, query in enumerate(queries))

for idx, hits in enumerate(hits_list):
    kwid = 'KW202-'+str(idx+1).zfill(5)
    query_tree = ET.SubElement(root, 'detected_kwlist', {'kwid': kwid, 'oov_count': '0', 'search_time': '0.0'})
    for hit in hits:
        ET.SubElement(query_tree, 'kw', hit)


# save the XML tree
ET.ElementTree(root).write(output_file, encoding='UTF-8', xml_declaration=False)
# ET.ElementTree(root).write('testing/test_output.xml', encoding='UTF-8', xml_declaration=False)
