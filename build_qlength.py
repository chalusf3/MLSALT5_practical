import os, sys
import xml.etree.ElementTree as ET

queries_file = 'lib/kws/queries.xml'
counts = [0]*32
lines = []
hits_tree = ET.parse(queries_file)
hits_root = hits_tree.getroot()
for kwid, query_leaf in enumerate(hits_root):
    
    query = query_leaf[0].text.split(' ')
    query_length = len(query)
    lines.append('%d %s %s\n' % (query_length, str(kwid+1).zfill(5), str(counts[query_length]).zfill(4)))
    counts[query_length] += 1
with open('lib/terms/queries_length.map','w') as f:
    f.writelines(lines)

print counts

queries_file = 'output/queries_morph.kwslist.xml'
counts = [0]*32
lines = []
hits_tree = ET.parse(queries_file)
hits_root = hits_tree.getroot()
for kwid, query_leaf in enumerate(hits_root):
    query = query_leaf[0].text.split(' ')
    query_length = len(query)
    lines.append('%d %s %s\n' % (query_length, str(kwid+1).zfill(5), str(counts[query_length]).zfill(4)))
    counts[query_length] += 1
with open('lib/terms/queries_morph_length.map','w') as f:
    f.writelines(lines)

print counts
