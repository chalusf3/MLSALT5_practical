# -*- coding: utf-8 -*-
import sys, argparse, os
import xml.etree.ElementTree as ET

def query_type(map_file, idx):
    with open(map_file, 'r') as f:
        lines = f.readlines()
    return lines[idx].split(' ')[0]

def print_and_log(s):
    s = str(s)
    print s
    with open('comb_hits/ibm/stdout4.out','a') as f:
        f.write(s)
        f.write('\n')

def normalize(out_file_xml, tmp_file, gamma):
    print_and_log('Renormalizing %s %f' % (out_file_xml, gamma))
    hits = {}
    hits_tree = ET.parse(hits_file) # the hits_file 's XML hit tree
    hits_root = hits_tree.getroot() 
    kwids = []
    for query_node in hits_root:
        # we are at query level
        kwid = query_node.attrib['kwid']
        kwids.append(kwid)
        unnorm_hits = [unnorm_hit.attrib for unnorm_hit in query_node] 
        for unnorm_hit in unnorm_hits:
            unnorm_hit['score'] = float(unnorm_hit['score'])

        # normalize score of input
        score_renorm_cst = sum([unnorm_hit['score']**gamma for unnorm_hit in unnorm_hits])
        for unnorm_hit in unnorm_hits:
            unnorm_hit['score'] = unnorm_hit['score']**gamma / score_renorm_cst
        hits[kwid] = unnorm_hits
    
    new_hits_root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})
    for query_kwid in kwids:
        new_query_tree = ET.SubElement(new_hits_root, 'detected_kwlist', {'kwid': query_kwid, 'oov_count': '0', 'search_time': '0.0'})
        for hit in hits[query_kwid]:
            ET.SubElement(new_query_tree, 'kw', {key: str(hit[key]) for key in hit})
    ET.ElementTree(new_hits_root).write(tmp_file, encoding='UTF-8', xml_declaration=False)
    print_and_log('done normalizing %s ' % out_file_xml)
    return hits

def score(out_file_xml, scoring_dir=None):
    print_and_log('------------------------')
    print_and_log('scoring %s' % out_file_xml)
    if not scoring_dir: scoring_dir = 'comb_hits/scoring/'+'.'.join(out_file_xml.split('/')[-1].split('.')[0:-1])+'/'
    os.system('rm -r %s' % (scoring_dir))
    os.system('./scripts/score.sh %s %s' % (out_file_xml, scoring_dir))
    s_all = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s all' % (out_file_xml, scoring_dir)).read()
    s_iv = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s iv' % (out_file_xml, scoring_dir)).read()
    s_oov = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s oov' % (out_file_xml, scoring_dir)).read()
    TWVs = []
    numbers = []
    for s in [s_all, s_iv, s_oov]:
        s = s.split('=')
        TWV, threshold, number = [x.split(' ')[0]for x in s[1:]]
        TWVs.append(float(TWV))
        numbers.append(int(number))
    threshold = float(threshold)
    print_and_log('\t\tALL\t\tIV\t\tOOV')
    print_and_log('TWVs =      \t' + ''.join(['%.6f\t' % TWV for TWV in TWVs]))
    print_and_log('Threshold = \t%f' % threshold)
    print_and_log('Counts =    \t' + ''.join(['%d\t\t' % number for number in numbers]))
    print_and_log('---')
    res_cats = []
    for cat in range(1,5+1):
        res_cats.append(os.popen('./scripts/termselect.sh lib/terms/queries_length.map %s %s %d' % (out_file_xml, scoring_dir, cat)).read())
    TWVs = []
    numbers = []
    for s in [s_all] + res_cats:
        s = s.split('=')
        TWV, threshold, number = [x.split(' ')[0]for x in s[1:]]
        TWVs.append(float(TWV))
        numbers.append(int(number))
    threshold = float(threshold)
    print_and_log('\t\tALL\t\t1\t\t2\t\t3\t\t4\t\t5')
    print_and_log('TWVs =      \t' + ''.join(['%.6f\t' % TWV for TWV in TWVs]))
    print_and_log('Threshold = \t%f' % threshold)
    print_and_log('Counts =    \t' + ''.join(['%d\t\t' % number for number in numbers]))
    print_and_log('------------------------\n')

    return float(TWVs[0])

def similarity_test(hit1, hit2):
    ret = True
    for key in ['file', 'channel', 'decision', 'tbeg', 'dur']:
        ret = ret and hit1[key]==hit2[key]
    return ret

def combine_and_score(hits_files, gamma_output, gamma_inputs, weights):
    output_file = 'comb_hits/ibm/out.xml'

    kwids = ['KW202-'+str(n).zfill(5) for n in range(1,501)]
    hits = {kwid: [] for kwid in kwids} # to store the new combined hits

    # Combine hits. 
    # weightsiv = [1.5,1,0]
    # weightsoov = [0,0,1]
    # for hits_file, gamma_input, weightiv, weightoov in zip(hits_files, gamma_inputs, weightsiv, weightsoov):
    for hits_file, gamma_input, weight in zip(hits_files, gamma_inputs, weights):
        if gamma_input:
            print_and_log('Renormalizing %s %f' % (hits_file, gamma_input))
        
        hits_tree = ET.parse(hits_file) # the hits_file 's XML hit tree
        hits_root = hits_tree.getroot()
        for query_node in hits_root:
            # we are at query level
            kwid = query_node.attrib['kwid']            
            proposed_hits = [proposed_hit.attrib for proposed_hit in query_node] 
            for proposed_hit in proposed_hits:
                proposed_hit['score'] = float(proposed_hit['score'])

            # normalize score of input
            if gamma_input:
                score_renorm_cst = sum([proposed_hit['score']**gamma_input for proposed_hit in proposed_hits])
                for proposed_hit in proposed_hits:
                    proposed_hit['score'] = proposed_hit['score']**gamma_input / score_renorm_cst

            for proposed_hit in proposed_hits:
                proposed_hit['score'] = weight * proposed_hit['score'] 
                # proposed_hit['score'] = (weightiv if query_type('lib/terms/ivoov.map', int(kwid.split('-')[-1])-1)=='iiv' else weightoov) * proposed_hit['score'] 
            for proposed_hit in proposed_hits:
                similar_hits = [idx for idx, combined_hit in enumerate(hits[kwid]) if similarity_test(proposed_hit, combined_hit)]
                if len(similar_hits) == 1:
                    idx = similar_hits[0]
                    hits[kwid][idx]['score'] = hits[kwid][idx]['score'] + proposed_hit['score']
                elif len(similar_hits)==0:
                    hits[kwid].append(proposed_hit)
                else:
                    print_and_log('More than one similar hit-->review similarity_test')
            
    # Score normalize output
    if gamma_output:
        print_and_log('Renormalizing output %f' % gamma_output)
        for query_kwid in kwids:
            s = sum([hit['score']**gamma_output for hit in hits[query_kwid]])
            if s > 0:
                for hit in hits[query_kwid]:
                    hit['score'] = hit['score']**gamma_output / s

    # Save as a new XML
    new_hits_root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})
    for query_kwid in kwids:
        new_query_tree = ET.SubElement(new_hits_root, 'detected_kwlist', {'kwid': query_kwid, 'oov_count': '0', 'search_time': '0.0'})
        for hit in hits[query_kwid]:
            ET.SubElement(new_query_tree, 'kw', {key: str(hit[key]) for key in hit if key!='tend'})
    ET.ElementTree(new_hits_root).write(output_file, encoding='UTF-8', xml_declaration=False)
    print_and_log('done combining')

    return score(output_file)

if __name__ == "__main__":

    # Load and parse the XML hits list in dictionaries
    hits_files = ['output/decode-morph_unnorm_out.xml', 'output/decode_unnorm_out.xml']
    hits_files[1] = 'output/decode_out_cut.xml' # accelerate by dismissing all hits below threshold
    gamma_inputs = [1.75, 0.5]
    # gamma_inputs = [None, None]

    # hits_files = ['lib/kws/word.xml', 'lib/kws/word-sys2.xml', 'lib/kws/morph.xml']
    # hits_files = ['lib/kws/word.xml', 'output/decode_out_cut.xml', 'lib/kws/morph.xml']
    # gamma_inputs = [1.5, 1.5, 1]
    # weights = [1.15, 1.75] + [1]

    # # Raw performance
    # for hit_file in hits_files:
    #     score(hit_file)

    parser = argparse.ArgumentParser()
    # parser.add_argument('output_file', help="Output hits file (.xml)")
    parser.add_argument('--gamma_output', help="exponent to score normalize the output?")
    parser.add_argument('-gamma_inputs', '--gamma_inputs', nargs=len(hits_files), help='exponents to normalize the input systems score')
    parser.add_argument('-weights', '--weights', nargs=len(hits_files), help='weights to combine the input systems score')

    args = parser.parse_args()
    # output_file = args.output_file
    gamma_output = float(args.gamma_output) if args.gamma_output else None

    if args.gamma_inputs:
        gamma_inputs = [float(gamma_input) for gamma_input in args.gamma_inputs]
    else:
        gamma_inputs = [None] * len(hits_files)

    if args.weights:
        weights = [float(weight) for weight in args.weights]
    else:
        weights = [1.0] * len(hits_files)
    print_and_log(zip(hits_files, gamma_inputs, weights))

    # for hits_file, gamma_input in zip(hits_files, gamma_inputs):
    #     if gamma_input:
    #         hits_name = hits_file.split('/')[-1] 
    #         tmp_path = 'comb_hits/ibm/'+hits_name
    #         os.system('rm %s' % tmp_path)
    #         normalize(hits_file, tmp_path, gamma_input) 
    #         score(tmp_path)
    
    combine_and_score(hits_files, gamma_output, gamma_inputs, weights)

    # indices = [0,2]
    # combine_and_score([hits_files[indices[0]], hits_files[indices[1]]], gamma_output, [gamma_inputs[indices[0]], gamma_inputs[indices[1]]], [weights[indices[0]], weights[indices[1]]])


# Create good versions
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml output/decode_unnorm_out.xml scoring/decode_unnorm_out --n_best 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml output/decode-morph_unnorm_out.xml scoring/decode-morph_unnorm_out --n_best 1

# Unnormalized
# python combine_hits.py 

# Normalized
# python combine_hits.py --gamma_output 0.5
# python combine_hits.py --gamma_output 0.55
# python combine_hits.py --gamma_output 0.6
# python combine_hits.py --gamma_output 0.65
# python combine_hits.py --gamma_output 0.7
# python combine_hits.py --gamma_output 0.75
# python combine_hits.py --gamma_output 0.8 
# python combine_hits.py --gamma_output 0.85
# python combine_hits.py --gamma_output 0.9
# python combine_hits.py --gamma_output 0.95
# python combine_hits.py --gamma_output 1.0
# python combine_hits.py --gamma_output 1.05
# python combine_hits.py --gamma_output 1.10
# python combine_hits.py --gamma_output 1.15
# python combine_hits.py --gamma_output 1.20
# python combine_hits.py --gamma_output 1.25
# python combine_hits.py --gamma_output 1.30
# python combine_hits.py --gamma_output 1.35
# python combine_hits.py --gamma_output 1.40
# python combine_hits.py --gamma_output 1.45
# python combine_hits.py --gamma_output 1.50
# python combine_hits.py --gamma_output 1.55
# python combine_hits.py --gamma_output 1.60
# python combine_hits.py --gamma_output 1.65
# python combine_hits.py --gamma_output 1.70
# python combine_hits.py --gamma_output 1.75
# python combine_hits.py --gamma_output 1.80
# python combine_hits.py --gamma_output 1.85
# python combine_hits.py --gamma_output 1.90
# python combine_hits.py --gamma_output 1.95
# python combine_hits.py --gamma_output 2.00
# python combine_hits.py --gamma_output 2.05
# python combine_hits.py --gamma_output 2.10
# python combine_hits.py --gamma_output 2.15
# python combine_hits.py --gamma_output 2.20
# python combine_hits.py --gamma_output 2.25
# Unnorm inputs --> gamma = 1.0
# Norm inputs   --> gamma = 1.15

# python combine_hits.py --gamma_output 0.25 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 0.5 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 0.75 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 1.00 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 1.25 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 1.5 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 1.75 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 2.00 --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 2.25 --gamma_inputs 1.75 0.5


# Optimal systems
# python combine_hits.py 
# python combine_hits.py --gamma_inputs 1.75 0.5
# python combine_hits.py --gamma_output 1
# python combine_hits.py --gamma_inputs 1.75 0.5 --gamma_output 1
