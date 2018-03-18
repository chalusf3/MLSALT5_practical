# -*- coding: utf-8 -*-
import sys, os, json
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
sys.path.append('/home/wjb31/MLSALT/util/python/')
import pywrapfst as fst
import specializer
import utilfst
import math, string
# export PATH=/home/wjb31/src/openfst/openfst-1.6.3/INSTALL_DIR/bin/:$PATH

index_file = sys.argv[1]

def save_autom(autom, name):
    path = '/home/fc443/MLSALT5/Practical/FSTs/'+name
    autom.draw(path+'.gv', title=name, portrait=True)
    os.system("dot -Teps %s.gv -o %s.eps" % (path, path))
    
    f = open(path+'.txt', 'w')
    for line in autom.text():
        f.write(line)

special_characters = ["'",'-','_',':','</w>','<','>','(',')']
characters = ['sil'] + list(string.ascii_lowercase) + special_characters

# build the confusion matrix
index = dict(zip(characters, range(len(characters))))
confusion_matrix = [[0 for x in range(len(characters))] for y in range(len(characters))] # confusion_matrix[a][b] = #times a was recognized as b
confusion_matrix_alt = [[0 for x in range(len(characters))] for y in range(len(characters))] 
with open('lib/kws/grapheme.map') as f:
    for line in f:
        formatted_line = line[0:-1].split(' ')
        # print formatted_line, index[formatted_line[0]], index[formatted_line[1]], float(formatted_line[2])
        confusion_matrix[index[formatted_line[0]]][index[formatted_line[1]]] = float(formatted_line[2])
        confusion_matrix_alt[index[formatted_line[0]]][index[formatted_line[1]]] = float(formatted_line[2])

for b in range(len(characters)):
    s = sum([confusion_matrix[a][b] for a in range(len(characters))])  
    if s!=0.0:
        for a in range(len(characters)):
            confusion_matrix[a][b] = confusion_matrix[a][b] / s
    else:
        for a in range(len(characters)):
            confusion_matrix[a][b] = 0.0
        confusion_matrix[b][b] = 1.0
# NOW: confusion_matrix[a][b] = proba(a was recognized as b) = P(true = a|recognized = b)

for a in range(len(characters)):
    s = sum(confusion_matrix_alt[a]) # s = #times the true a was seen
    if s != 0.0:
        confusion_matrix_alt[a] = [x/s for x in confusion_matrix_alt[a]]
    else:
        confusion_matrix_alt[a] = [0.0]*len(characters)
        confusion_matrix_alt[a][a] = 1.0
# NOW: confusion_matrix_alt[a][b] = P(recognized = b | true = a), recognized is a sort of confuser: it creates the confusion

# Rename sil by <eps> in those tables
index['<eps>'] = index['sil']
del index['sil']

# Create the symbol table
printable_ST = fst.SymbolTable()
printable_ST.add_symbol('<eps>')
for c in index.keys():
    if c != '<eps>':
        printable_ST.add_symbol(c)
# save the symbol table
printable_ST.write_text('FSTs/symbol_table.txt')

# Build a sigma FST: accepting any and outputting epsilon
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
        # score = confusion_matrix[index[estim]][index[truth]]
        if score > 0: 
            print >> compiler, '0 0 '+estim+' '+truth+' '+str(-math.log(score))
for c in special_characters:
    print >> compiler, '0 0 '+c+' '+c
print >> compiler, '0'
confuser = compiler.compile()
confuser = confuser.rmepsilon().arcsort()
save_autom(confuser, 'grapheme_confusion')
confuser.write('FSTs/grapheme_confusion.fst')

# Build an FST which makes the errors: maps <truth> to <estim> with probability P[estim|truth] = confusion_matrix_alt[truth][estim] = P(recognized = estim | true = truth)
compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)
for truth in index.keys():
    for estim in index.keys():
        score = confusion_matrix_alt[index[truth]][index[estim]]
        if score > 0:
            print >> compiler, '0 0 '+truth+' '+estim+' '+str(-math.log(score))
for c in special_characters:
    print >> compiler, '0 0 '+c+' '+c
print >> compiler, '0'
error_maker_fst = compiler.compile().rmepsilon().arcsort()
save_autom(error_maker_fst, 'error_maker_fst')
error_maker_fst.write('FSTs/error_maker.fst')

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

fst_vocab = compiler_accept_vocab.compile()
# save_autom(fst_vocab.arcsort(), 'vocab')
fst_vocab = fst.determinize(fst_vocab.rmepsilon()).minimize().arcsort()
index_name = '.'.join(index_file.split('/')[-1].split('.')[0:-1])
fst_vocab.write('FSTs/vocab_'+index_name+'.fst')

# erroneous_vocab = fst.compose(error_maker_fst, fst_vocab).project(project_output=False).rmepsilon()
# erroneous_vocab = fst.determinize(erroneous_vocab).minimize()
# erroneous_vocab.write('FSTs/erroneous_vocab_'+index_name+'.fst')











