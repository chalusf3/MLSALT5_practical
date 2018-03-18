import os
import combine_hits

hits_files = ['lib/kws/word.xml', 'lib/kws/word-sys2.xml', 'lib/kws/morph.xml']

indices = [[0,1], [0,2], [1,2]]
gamma_inputs = [1.5, 1.5, 1]
# gamma_inputs = [1]*3
# gamma_inputs = [None]*3
gamma_output = None

del gamma_inputs
gammas = [0.8, 1, 1.2, 1.4, 1.6]
gamma_inputs_list = [(x,y,z) for x in gammas for y in gammas for z in gammas]

# gamma_inputs_list = [gamma_inputs]

for gamma_inputs in gamma_inputs_list:
    for ind in indices:
        combine_hits.combine_and_score([hits_files[ind[0]], hits_files[ind[1]]], None, (gamma_inputs[ind[0]], gamma_inputs[ind[1]]), [1.0, 1.0])
    combine_hits.combine_and_score(hits_files, None, gamma_inputs, [1.0, 1.0, 1.0])

# gamma_range = (0.5,3) # continuous
# weight_range = (0.5, 3) # continuous
# from bayes_opt import BayesianOptimization
# hits_files = [hits_files[0], hits_files[1]]
# bo = BayesianOptimization(lambda gi_0, gi_1, w: combine_hits.combine_and_score(hits_files, None, (gi_0, gi_1), [w, 1.0]), {'gi_0': gamma_range, 'gi_1': gamma_range, 'w': weight_range})
# bo.maximize(init_points=10, n_iter=50, kappa=2)
# print(bo.res['max'])
# print(bo.res['all'])
