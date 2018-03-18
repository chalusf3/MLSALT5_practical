# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import os
from combine_hits import score
hits_file = 'comb_hits/ibm/morph.xml'
output_file = 'comb_hits/morph_cut.xml'
scoring_dir = 'comb_hits/scoring/morph_cut/'
threshold = 0.019

hits_tree = ET.parse(hits_file) # the hits_file 's XML hit tree
hits_root = hits_tree.getroot() 

valid_hits_root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})
for query_node in hits_root:
    kwid = query_node.attrib['kwid']
    old_hits = [proposed_hit.attrib for proposed_hit in query_node] 
    valid_hits = []
    for old_hit in old_hits:
        if float(old_hit['score'])>threshold:
            valid_hits.append(old_hit)
    
    print kwid, len(old_hits), len(valid_hits)
    
    valid_query_tree = ET.SubElement(valid_hits_root, 'detected_kwlist', {'kwid': kwid, 'oov_count': '0', 'search_time': '0.0'})
    for valid_hit in valid_hits:
        ET.SubElement(valid_query_tree, 'kw', valid_hit)
ET.ElementTree(valid_hits_root).write(output_file, encoding='UTF-8', xml_declaration=False)
score(output_file, scoring_dir)
os.system('rm -r %s' % (scoring_dir))
os.system('./scripts/score.sh %s %s' % (output_file, scoring_dir))
s_all = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s all' % (output_file, scoring_dir)).read()
