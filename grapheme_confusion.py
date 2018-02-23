import sys, os, json
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
sys.path.append('/home/wjb31/MLSALT/util/python/')
import pywrapfst as fst
import specializer
import utilfst
import math, string

index_file = sys.argv[1]

def save_autom(autom, name):
    path = '/home/fc443/MLSALT5/Practical/FSTs/'+name
    autom.draw(path+'.gv', title=name, portrait=True)
    os.system("dot -Teps %s.gv -o %s.eps" % (path, path))
    
    f = open(path+'.txt', 'w')
    for line in autom.text():
        f.write(line)

def count_paths(autom):
    autom = autom.copy().topsort()
    l = [0]*autom.num_states()
    l[autom.start()] = 1
    for s in autom.states():
        for a in autom.arcs(s):
            l[a.nextstate]+=l[s]
    return l[-1]
def total_num_arcs(autom):
    s = 0
    for state in autom.states():
        s += autom.num_arcs(state)
    return s
def minimize_and_print_stat(autom):
    print(autom.num_states(), total_num_arcs(autom))
    autom = fst.determinize(autom.copy().minimize().rmepsilon())
    print(autom.num_states(), total_num_arcs(autom))
    return autom    
def print_unique_string_in_language(message):
    message_lines = message.text().split('\n')[0:-2]
    message_chars = [line.split('\t')[2] for line in message_lines]
    for ii in range(0,len(message_chars)):
        if message_chars[ii] == '<space>':
            message_chars[ii] = ' '
    s = ''.join(message_chars)
    return s

special_characters = ["'",'-','_',':','</w>','<','>','(',')']
characters = ['sil'] + list(string.ascii_lowercase) + special_characters

# build the confusion matrix
index = dict(zip(characters, range(len(characters))))
confusion_matrix = [[0 for x in range(len(characters))] for y in range(len(characters))] # confusion_matrix[a][b] = #times a was recognized as b
with open('lib/kws/grapheme.map') as f:
    for line in f:
        formatted_line = line[0:-1].split(' ')
        # print formatted_line, index[formatted_line[0]], index[formatted_line[1]], float(formatted_line[2])
        confusion_matrix[index[formatted_line[0]]][index[formatted_line[1]]] = float(formatted_line[2])

for b in range(len(characters)):
    s = sum([confusion_matrix[a][b] for a in range(len(characters))])  
    if s!=0.0:
        for a in range(len(characters)):
            confusion_matrix[a][b] = confusion_matrix[a][b] / s
    else:
        for a in range(len(characters)):
            confusion_matrix[a][b] = 0
        confusion_matrix[b][b] = 1
# NOW: confusion_matrix[a][b] = proba(a was recognized as b) = P(true = a|recognized = b)

# Rename sil by <sil>
index['<sil>'] = index['sil']
del index['sil']

printable_ST = fst.SymbolTable()
for c in ['<eps>']+index.keys():
    printable_ST.add_symbol(c)

# for c in range(0,2**20):
#     printable_ST.add_symbol(str(c))

# save the symbol table
printable_ST.write_text('FSTs/symbol_table.txt')

# build a sigma FST: accepting any and outputting epsilon
compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
for c in index.keys():
    print >> compiler, '0 0 %s <eps>' % c
print >> compiler, '0'
compiler.compile().write('FSTs/sigma.fst') 

# Build an FST which corrects the errors: maps <estim> to <truth> with probability confusion_matrix[<truth>][<estim>]
compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
for truth in index.keys():#[0:4]:
    for estim in index.keys():#[0:4]:
        score = confusion_matrix[index[truth]][index[estim]]
        if score > 0: 
            print >> compiler, '0 0 '+estim+' '+truth+' '+str(-math.log(score))
for c in special_characters:
    print >> compiler, '0 0 '+c+' '+c
print >> compiler, '0'
confuser = compiler.compile()
confuser = confuser.rmepsilon().arcsort()
save_autom(confuser, 'grapheme_confusion')
confuser.write('FSTs/grapheme_confusion.fst')

# Build an FSA which only accepts sequences of terms in index_file (a vocabulary acceptor)
with open(index_file,'rb') as f:
# with open('testing/test.json','rb') as f:
    words = json.load(f)

vocab_words = {word: set() for word in words.keys()} # a dictionnary which maps each word to the words that followed it
for word in words.keys():
    followers = set([w['following_word'][0] for w in words[word] if w['following_word']])
    vocab_words[word] = vocab_words[word].union(followers)
del words
word_nodes = {word: (None,None) for word in vocab_words.keys()} # to record from which state to which state word spanned. 

# Create FSA accepting only those words in the index
compiler_accept_vocab = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
c = 0
print >> compiler_accept_vocab, '0'
for word in word_nodes.keys():
    word_begin = c
    print >> compiler_accept_vocab, '0 ' + str(c) + ' <eps> <eps>'
    for char in word:
        print >> compiler_accept_vocab, str(c) + ' ' + str(c + 1) + ' ' + char + ' ' + char
        c = c+1
    print >> compiler_accept_vocab, str(c) + ' ' + str(c + 1) + ' </w> </w>'
    c = c+1
    print >> compiler_accept_vocab, str(c)
    word_nodes[word] = (word_begin, c)
    c = c+1

for word in word_nodes.keys():
    for follower in vocab_words[word]: # add an arc from last state of word to first state of follower
        print >> compiler_accept_vocab, str(word_nodes[word][1]) + ' ' + str(word_nodes[follower][0]) + ' <eps> <eps>'

for c in special_characters:#+['<sil>']:
    print >> compiler, '0 0 '+c+' '+c

fst_vocab = compiler_accept_vocab.compile().arcsort()
index_name = '.'.join(index_file.split('/')[-1].split('.')[0:-1])
fst_vocab.write('FSTs/vocab_'+index_name+'.fst')
















