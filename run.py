# -*- coding: utf-8 -*-

import os, argparse

# python run.py lib/ctms/reference.ctm    index/reference.json    lib/kws/queries.xml              run_output/reference_out.xml       run_scoring/reference_out     --n_best 100 --alpha 1 --gamma 1
# python run.py lib/ctms/decode.ctm       index/decode.json       lib/kws/queries.xml              run_output/decode_out.xml          run_scoring/decode_out        --n_best 100 --alpha 1 --gamma 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml    run_scoring/decode-morph_out  --n_best 100 --alpha 1 --gamma 1

# python run.py output/reference_morph.ctm index/reference_morph.json output/queries_morph.kwslist.xml run_output/reference_morph_out.xml run_scoring/reference_morph_out 
# python run.py output/decode_morph.ctm    index/decode_morph.json    output/queries_morph.kwslist.xml run_output/decode_morph_out.xml    run_scoring/decode_morph_out 

parser = argparse.ArgumentParser()
parser.add_argument('ctm_file', help="ASR output file (.ctm)")
parser.add_argument('index_file', help="Index file (.ctm)")
parser.add_argument('queries_file', help="Queries file (.xml)")
parser.add_argument('output_file', help="Output hits file (.xml)")
parser.add_argument('scoring_dir', help="Scoring directory")
parser.add_argument('--n_best', help="Number of alternatives for OOV")
parser.add_argument('--alpha', help="weight of alternative query score")
parser.add_argument('--gamma', help="exponent for score normalization")
parser.add_argument('--rerun', help='boolean on whether compositions should be reperformed')

args = parser.parse_args()
ctm_file = args.ctm_file
index_file = args.index_file
queries_file = args.queries_file
output_file = args.output_file
scoring_dir = args.scoring_dir
n_best = " --n_best "+args.n_best if args.n_best else ""
alpha = " --alpha "+args.alpha if args.alpha else ""
gamma = " --gamma "+args.gamma if args.gamma else ""
rerun = " --rerun "+args.rerun if args.rerun else ""

os.system('python indexing.py %s %s' % (ctm_file, index_file))
os.system('python grapheme_confusion.py %s' % index_file)
print 'Done indexing and building grapheme confusion FST'
os.system('python querying.py %s %s %s %s %s %s %s' % (index_file, queries_file, output_file, n_best, alpha, gamma, rerun)) 
print 'Done querying'
os.system('rm -r %s' % (scoring_dir))
os.system('./scripts/score.sh %s %s' % (output_file, scoring_dir))
s_all = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s all' % (output_file, scoring_dir)).read()
s_iv = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s iv' % (output_file, scoring_dir)).read()
s_oov = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s oov' % (output_file, scoring_dir)).read()

TWVs = []
numbers = []
for s in [s_all, s_iv, s_oov]:
    s = s.split('=')
    TWV, threshold, number = [x.split(' ')[0]for x in s[1:]]
    TWVs.append(TWV)
    numbers.append(number)
numbers = [int(number) for number in numbers]
TWVs = [float(TWV) for TWV in TWVs]
threshold = float(threshold)
print index_file, n_best, alpha, gamma
print 'TWVs = \t%.6f\t%.6f\t%.6f' % (TWVs[0], TWVs[1], TWVs[2])
print 'threshold = %f' % threshold
print 'ALL = \t%df\t%d\t%d' % (numbers[0], numbers[1], numbers[2])


# part 3
# python run.py lib/ctms/reference.ctm index/reference.json lib/kws/queries.xml run_output/reference_out.xml run_scoring/reference_out 
# python run.py output/reference_morph.ctm index/reference_morph.json output/queries_morph.kwslist.xml run_output/reference_morph_out.xml run_scoring/reference_morph_out 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml output/decode_nograph_out.xml scoring/decode_nograph_out 
# python run.py output/decode_morph.ctm index/decode_morph.json output/queries_morph.kwslist.xml run_output/decode_morph_out.xml run_scoring/decode_morph_out 
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out 

# part 4
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 0.6
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 1
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 1.5
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 2.5
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 3
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 3.5
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 4
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --gamma 5

# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 0.6 
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.5
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 2 
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 3 
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 5

# part 5
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1 --alpha 1 --gamma 2 # 0.360383
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 2 --alpha 1 --gamma 2 # 0.362287
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 3 --alpha 1 --gamma 2 # 0.365003
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 5 --alpha 1 --gamma 2 # 0.362649
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 10 --alpha 1 --gamma 2 # 0.362057
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 25 --alpha 1 --gamma 2 # 0.361600
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 50 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 100 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 250 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 500 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1000 --alpha 1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1500 --alpha 1 --gamma 2
####--> best is n_best = 1

# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1 --alpha 0.01 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1 --alpha 0.1 --gamma 2
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 1 --alpha 1 --gamma 2
###-> alpha does not seem to matter if we score normalize...

# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 1 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 2 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 5 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 10 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 50 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 100 --alpha 1

# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 1 --alpha 0.1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 1 --alpha 1
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml run_output/decode-morph_out.xml run_scoring/decode-morph_out --gamma 1.75 --n_best 1 --alpha 10

# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 0.5 -->0.363833
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 0.75 -->0.374368
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 1 -->0.382017
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 1.5 -->0.373239
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 2 -->0.367792
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5 --gamma 3 -->0.358182
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.5  --gamma 0.5 ->0.363833
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 0.75 --gamma 0.5 ->0.374295
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 1    --gamma 0.5 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 1.5  --gamma 0.5 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 2    --gamma 0.5 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml run_output/decode_out.xml run_scoring/decode_out --n_best 750 --alpha 3    --gamma 0.5 

# part 3.3.1
# combine the best from decode+grapheme confusion and the best from decode-morph w/out grapheme confusion
########################### RUN THIS ##############################
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml output/decode-morph_out.xml scoring/decode-morph_out --gamma 1.75 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml output/decode_out.xml scoring/decode_out --n_best 750 --gamma 0.25 --alpha 1.0
# python run.py lib/ctms/decode-morph.ctm index/decode-morph.json output/queries_morph.kwslist.xml output/decode-morph_unnorm_out.xml scoring/decode-morph_unnorm_out 
# python run.py lib/ctms/decode.ctm index/decode.json lib/kws/queries.xml output/decode_unnorm_out.xml scoring/decode_unnorm_out --n_best 750 --alpha 1.0
