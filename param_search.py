import os, sys
sys.path.append("./")

# ctm_file = 'lib/ctms/decode.ctm'
# index_file = 'index/decode.json'
# queries_file = 'lib/kws/queries.xml'
ctm_file = 'lib/ctms/decode-morph.ctm'
index_file = 'index/decode-morph.json'
queries_file = 'output/queries_morph.kwslist.xml'


os.system('python grapheme_confusion.py %s' % index_file)
os.system('python indexing.py %s %s' % (ctm_file, index_file))
print 'Done indexing'

def objective_function(n_best, alpha, gamma):

    n_best = int(round(n_best))
    working_dir = 'param_search/tmp'+str(alpha)+str(n_best)+str(gamma)+'/'
    os.system('rm -rf %s' % (working_dir))
    os.system('mkdir '+working_dir)
    output_file = working_dir + '/output.xml'
    scoring_dir = working_dir + '/scoring/'
    n_best_arg = " --n_best "+str(n_best)
    alpha_arg = " --alpha "+str(alpha)
    gamma_arg = " --gamma "+str(gamma) if gamma else ""

    os.system('python querying.py %s %s %s %s %s %s' % (index_file, queries_file, output_file, n_best_arg, alpha_arg, gamma_arg)) 
    os.system('./scripts/score.sh %s %s' % (output_file, scoring_dir))
    s_all = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s all' % (output_file, scoring_dir)).read()
    s_iv = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s iv' % (output_file, scoring_dir)).read()
    s_oov = os.popen('./scripts/termselect.sh lib/terms/ivoov.map %s %s oov' % (output_file, scoring_dir)).read()

    TWVs = []
    numbers = []
    for s in [s_all, s_iv, s_oov]:
        s = s.split('=')
        TWV, threshold, number = [float(x.split(' ')[0]) for x in s[1:]]
        number = int(number)

        TWVs.append(TWV)
        numbers.append(number)
    if not gamma:
        gamma = 0
    with open('param_search_morph.out','a') as f:
        line = 'n_best = %d,\t\talpha = %f,\tgamma = %f,\tTWVs = %f, %f, %f,\tthreshold = %f,\tALL/IV/OOV = %d, %d, %d\n' % (int(n_best), alpha, gamma, TWVs[0], TWVs[1], TWVs[2], threshold, numbers[0], numbers[1], numbers[2])
        f.write(line)
    os.system('rm -rf %s/*' % (working_dir))

    return TWVs[0]

# n_best_range = (10,2000) # continuous
# alpha_range = (0.1, 10) # continuous
# gamma_range = (1,2.5) # continuous
# from bayes_opt import BayesianOptimization
# bo = BayesianOptimization(objective_function, {'n_best': n_best_range, 'alpha': alpha_range, 'gamma': gamma_range})
# bo.maximize(init_points=1, n_iter=50, kappa=2)
# print(bo.res['max'])
# print(bo.res['all'])

import joblib
n_bests = [1,2,5,10,100,250,500,750,1000]
alphas = [0.25, 0.5, 0.75, 1, 1.5, 2, 3]
gammas = alphas
if True:
    scores = [[0]*len(alphas) for _ in n_bests]
    for i,n_best in enumerate(n_bests):
        # scores[i] = joblib.Parallel(n_jobs=len(alphas))(joblib.delayed(objective_function)(n_best, alpha, None) for alpha in alphas)
        for j,alpha in enumerate(alphas):
                scores[i][j] = objective_function(n_best, alpha, None)
                print scores
    print scores
if True:
    scores = [[0]*len(gammas) for _ in n_bests]
    for i,n_best in enumerate(n_bests):
        for j,gamma in enumerate(gammas):
                scores[i][j] = objective_function(n_best, 1, gamma)
                print scores
    print scores