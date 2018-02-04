import sys
import xml.etree.ElementTree as ET

# Load and parse the XML hits list in dictionaries
# queries_file = sys.argv[1]
nb_hits = len(sys.argv)-2
hits_files = [sys.argv[i+1] for i in range(0,nb_hits)]
output_file = sys.argv[-1]

kwids = ['KW202-'+str(n).zfill(5) for n in range(1,501)]
hits = {kwid: [] for kwid in kwids}

# parse the 1st file of hits
hits_tree = ET.parse(hits_files[0])
hits_root = hits_tree.getroot()
for query_node in hits_root:
    # Parse the query
    kwid = query_node.attrib['kwid']
#     hits[kwid] = []
    
    score_renorm_cst = 0
    for hit in query_node:
        # Parse the hit
        attributes = hit.attrib
        for key in ['score', 'tbeg', 'dur']:
            attributes[key] = float(attributes[key])
        attributes['tend'] = attributes['tbeg'] + attributes['dur']
        score_renorm_cst = score_renorm_cst + attributes['score']
        hits[kwid].extend([attributes])
    
    for hit in hits[kwid]:
        hit['score'] = hit['score'] / score_renorm_cst
    

for hits_file in hits_files[1:]:
    hits_tree = ET.parse(hits_file)
    hits_root = hits_tree.getroot()
    for query_node in hits_root:
        # at query level
        kwid = query_node.attrib['kwid']
        
        hit_leaf_parsed = []
        score_renorm_cst = 0
        
        for hit in query_node:
            attributes = hit.attrib
            for key in ['score', 'tbeg', 'dur']:
                attributes[key] = float(attributes[key])
            attributes['tend'] = attributes['tbeg'] + attributes['dur']
            hit_leaf_parsed.extend([attributes])
            score_renorm_cst = score_renorm_cst + attributes['score']
        
        if score_renorm_cst > 0:
            for hit in hit_leaf_parsed:
                hit['score'] = hit['score'] / score_renorm_cst
                
        for hit in hit_leaf_parsed:
            # look for a similar hit in hits[kwid]
            test_similarity = lambda tbeg1, tbeg2, dur1, dur2, tend1, tend2: (10*max(abs(tbeg1-tbeg2), abs(tend1-tend2))) < min(dur1,dur2)
            similar_hits = [idx for idx, old_hit in enumerate(hits[kwid]) if old_hit['file']==hit['file'] and test_similarity(hit['tbeg'], old_hit['tbeg'], hit['dur'], old_hit['dur'], hit['tend'], old_hit['tend'])]

            if len(similar_hits)==1:
                similar_hit_idx = similar_hits[0]
                similar_hit = hits[kwid][similar_hit_idx]
            
                # combine similar_hit and hit
                similar_hit['tbeg'] = min(hit['tbeg'], similar_hit['tbeg'])
                similar_hit['tend'] = max(hit['tend'], similar_hit['tend'])
                similar_hit['dur'] = similar_hit['tend']-similar_hit['tbeg']
                similar_hit['score'] = similar_hit['score'] + hit['score']
                hits[kwid][similar_hit_idx] = similar_hit
            elif len(similar_hits) > 1:
                print "Found more than one similar hit. May want to review similary test", hits_file, kwid

new_hits_root = ET.Element('kwslist', {'kwlist_filename': 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml', 'language': 'swahili', 'system_id': ''})

for query_kwid in kwids:
    new_query_tree = ET.SubElement(new_hits_root, 'detected_kwlist', {'kwid': query_kwid, 'oov_count': '0', 'search_time': '0.0'})
    
    for hit in hits[query_kwid]:
        
        ET.SubElement(new_query_tree, 'kw', {key: str(hit[key]) for key in hit if key!='tend'})

ET.ElementTree(new_hits_root).write(output_file, encoding='UTF-8', xml_declaration=False)

        