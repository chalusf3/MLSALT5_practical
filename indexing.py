import json, sys, argparse

words = {}
# Format: words = {'word1': [{'filename': BLABLA, 'channel': 1, ..., 'score': 1, 'following_word': (wordlabel, idx in the wordlabel array)}, {}], 
#                  'word2': [{'filename': LABLAB, 'channel': 1, ..., 'score': 1, 'following_word': (wordlabel, idx in the wordlabel array)}]}

parser = argparse.ArgumentParser()
parser.add_argument('ctm_file', help="ASR output file (.ctm)")
parser.add_argument('index_file', help="Output index file (.json)")

args = parser.parse_args()
ctm_file = args.ctm_file
index_file = args.index_file

# if len(sys.argv) == 3:
#     ctm_file = sys.argv[1]
#     index_file = sys.argv[2]
# else:
#     print "Usage: python indexing.py ASR_output.ctm index_file.json"
#     sys.exit()

with open(ctm_file,'r') as f:
# with open('testing/test.ctm', 'r') as f:
    last_word = None #store the (word, index) coordinates of the previous line. 
    filename = None
    for line in f:  
        # Format the current line
        # split word by word
        line_formatted = line[0:-1].split(' ')
        while '' in line_formatted:
            line_formatted.pop(line_formatted.index(''))
        for j in [1,2,3,5]:
            line_formatted[j] = float(line_formatted[j])
        line_formatted[4] = line_formatted[4].lower()
        
        # add it to the dictionnary at the position "word" if existent
        if not line_formatted[4] in words:
            words[line_formatted[4]] = []
        
        new_entry = {'filename': line_formatted[0],
                     'channel': int(line_formatted[1]),
                     'tbeg': line_formatted[2],
                     'dur': line_formatted[3],
                     'score': line_formatted[5],
                     'following_word': None}
        
        index = len(words[line_formatted[4]]) # the index of new_entry in the array words[line_formatted[4]]
        words[line_formatted[4]].extend([new_entry])
        
        follower_ID = (line_formatted[4], index) #the ID we will put in the next iteration' following_word entry
        
        if line_formatted[0] != filename:
            last_word = None
        filename = line_formatted[0]
        
        # update the entry saved in last_word: add new_entry as its following_word (specified via the follower_ID variable)
        if last_word:
            last_word_entry = words[last_word[0]][last_word[1]]
            if new_entry['tbeg'] - (last_word_entry['tbeg'] + last_word_entry['dur'])<0.5:
                words[last_word[0]][last_word[1]]['following_word'] = follower_ID
        last_word = follower_ID
        
                
# save the dictionary as a JSON
with open(index_file,'wb') as f:
# with open('testing/test.json','wb') as f:
    json.dump(words, f)
