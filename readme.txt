Score = P(walk through arc|we are at start node of arc) 

To build the index for reference:
This will read from lib/ctms/reference.ctm to build an index in index/reference.json
python indexing.py reference

To perform the queries in lib/kws/queries.xml:
This will read the lib/kws/queries.xml, use the index located in index/reference.json and save the output in output/queries.xml (the output filename is from the queries file) 
python querying.py reference queries



To translate from word to morphs
python morph_decomp.py
This will use lib/dicts/morph.kwslist.dct to map lib/kws/queries.xml to output/queries_morph.kwslist.xml 
and use lib/dicts/morph.dct to map lib/ctms/reference.ctm to output/reference_morph.ctm

