import os, sys

if False:
    param_sets = os.listdir('param_search/')

    TWV_scores = []
    for params in param_sets:
        with open('param_search/'+params+'/scores.out') as f:
            l = f.read()
        TWV_scores.append(float(l.split('\n')[0].split(' ')[2][0:-1]))
    param_sets = [params.split('.')  for params in param_sets]
    param_sets = [(int(params[0]), float(params[1])+float('0.'+params[2]), float(params[3])+float('0.'+params[4]))  for params in param_sets]

    with open('param_search_out.txt','a') as f:
        for score, params in zip(TWV_scores, param_sets):
            line = '%f\t%f\t%f\t%f\n' % (params[0], params[1], params[2], score)
            f.write(line)

if True:
    with open('param_search_out.txt','r') as f:
        param_sets = []
        scores = []
        for line in f:
            score = float(line.split('\t')[-1][0:-1])
            params = line.split('\t')[0:3]
            params = [float(param) for param in params]
            scores.append(score)
            param_sets.append(params)
        del params, score, line
    # print max(scores)
    # print max(param_sets, key=lambda x: scores[param_sets.index(x)])
    param_sets_copy = param_sets[:]
    param_sets.sort(key=lambda x: scores[param_sets_copy.index(x)])
    scores.sort()
    del param_sets_copy
    print zip(param_sets, scores)[-5:]