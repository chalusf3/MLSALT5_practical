# -*- coding: utf-8 -*-
import pickle, json, sys, os#, time
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
import pywrapfst as fst
import specializer
import math, string

ctm_file = sys.argv[1]
index_fst_file = sys.argv[2]
index_arr_file = sys.argv[3]

def save_autom(autom, name):
    path = '/home/fc443/MLSALT5/Practical/FSTs/'+name
    autom.draw(path+'.gv', title=name, portrait=True)
    os.system("dot -Teps %s.gv -o %s.eps" % (path, path))
    
    f = open(path+'.txt', 'w')
    for line in autom.text():
        f.write(line)

def format_line(line):
    line = line[0:-1].split(' ')
    while '' in line:
        line.pop(line.index(''))
    for j in [1,2,3,5]:
        line[j] = float(line[j])
    line[4] = line[4].lower()
    filename, channel, tbeg, dur, word, score = line
    return filename, int(channel), tbeg, dur, word, score 

printable_ST = fst.SymbolTable().read_text('FSTs/symbol_table.txt')
index_compiler = fst.Compiler(isymbols=printable_ST, osymbols=printable_ST, keep_isymbols=True, keep_osymbols=True)

words = []

with open(ctm_file,'r') as f:
# with open('testing/test.ctm', 'r') as f:
    from_state = -1 # state FROM which the last word's arc will go
    to_state = 0 # index of state TO which the last word's arc will go
    # print >> index_compiler, '0' 

    # prev_fn, _, prev_tend = format_line(f[0]) # those variables always store the filename of the previous word and time at which it ended. 
    prev_fn = None
    prev_tend = 0
    ###
    # last_word = None #store the (word, index) coordinates of the previous line. 
    # filename = None
    ###
    for idx, line in enumerate(f):
        # Format the current line
        filename, channel, tbeg, dur, word, score = format_line(line)
        # decide whether the previous word was a terminal word
        # print (tbeg, prev_tend), (prev_fn != filename, tbeg > prev_tend+0.5)
        if (idx != 0) and (prev_fn != filename or tbeg > prev_tend+0.5):
            # the previous state was terminal. make its final state terminal and make the next arc go from 0 to to_state + 1
            print >> index_compiler, str(to_state)
            from_state = 0
            to_state = to_state + 1
        else: # the previous word wasn't terminal. we can just append the next arc as a chain  
            from_state = to_state
            to_state = to_state + 1
        
        # from_state and to_state are now the states for the first letter of current word
        print >> index_compiler, '%d %d %d <w> %f' % (from_state, to_state, idx, -math.log(score))
        from_state = to_state
        to_state = to_state + 1

        for idx_char, c in enumerate(word):
            print >> index_compiler, '%d %d %d %s %f' % (from_state, to_state, idx, c, 0)
            from_state = to_state
            to_state = to_state + 1
        print >> index_compiler, '%d %d %d </w> %f' % (from_state, to_state, idx, 0)

        words.append([filename, channel, tbeg, dur, word, score])
        
        # prepare for next loop
        prev_fn = filename
        prev_tend = tbeg+dur
        # if idx > 100:
        #     break

# print >> index_compiler, '%d' % to_state

fst_index = index_compiler.compile()

# print fst_index.text()[0:1000]

fst_index = fst.determinize(fst_index.rmepsilon()).minimize().arcsort()

# save_autom(fst_index, 'fst_index')

with open(index_arr_file,'wb') as f:
    pickle.dump(words, f)
fst_index.write(index_fst_file)