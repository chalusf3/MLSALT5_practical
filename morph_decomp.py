import sys
import xml.etree.ElementTree as ET

dictionnary = {}
with open('lib/dicts/morph.kwslist.dct') as f:
    for line in f:
        line_formatted = line[0:-1].split('\t') 
        dictionnary[line_formatted[0]] = line_formatted[1]#.split(' ')

tree = ET.parse('lib/kws/queries.xml')
root = tree.getroot()

for query_leaf in root:
    # Parse the query
    query = query_leaf[0].text.split(' ')
    translated_query = ' '.join([dictionnary[q] for q in query])
    query_leaf[0].text = ' '.join([dictionnary[q] for q in query])

ET.ElementTree(root).write('output/queries_morph.kwslist.xml', encoding='UTF-8', xml_declaration=False)







dictionnary = {}
with open('lib/dicts/morph.dct') as f:
    for line in f:
        line_formatted = line[0:-1].split('\t') 
        new_words = line_formatted[1].split(' ')
        while '' in new_words:
            new_words.pop(new_words.index(''))
        dictionnary[line_formatted[0]] = new_words
# print dictionnary
# file = sys.argv[1] #unnecessary
file = 'reference' 

translated_lines = []
with open('lib/ctms/'+file+'.ctm','r') as f:
    for line in f:
        line_formatted = line[0:-1].split(' ')
        while '' in line_formatted:
            line_formatted.pop(line_formatted.index(''))
        line_formatted[4] = line_formatted[4].lower()
        for j in [1,2,3,5]:
            line_formatted[j] = float(line_formatted[j])
        # file, channel, tbeg, dur, word, score
        
        if line_formatted[4] in dictionnary:
            words = dictionnary[line_formatted[4]]
        else:
            words = [line_formatted[4]]
        n_words = len(words)
        # generate an array of new lines and append them to new_lines (without \n at the end)
        new_lines = [[line_formatted[0], line_formatted[1], line_formatted[2]+c*line_formatted[3]/n_words, line_formatted[3]/n_words, w, line_formatted[5]**(1.0/n_words)] for c, w in enumerate(words)]
        new_lines = [' '.join([str(field) for field in new_line]) for new_line in new_lines]
        translated_lines.extend(new_lines) 

new_text = '\n'.join(translated_lines)

with open('output/'+file+'_morph.ctm','w') as f:
    f.write(new_text)
    f.write('\n')