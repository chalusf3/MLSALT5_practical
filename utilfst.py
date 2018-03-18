import sys,os 
sys.path.append('/home/wjb31//src/openfst//openfst-1.6.3/INSTALL_DIR/lib/python2.7/site-packages/')
sys.path.append('/home/wjb31//src/openfst//specializer-master/')
import pywrapfst as fst
import specializer
import math, string


def printstrings(a, nshortest=1, project_output=False, syms=None, weight=False):
    """
    Return the nshortest unique input strings in the FST a.  The FST a is projected 
    onto the input or output prior to finding the shortest paths. An optional symbol 
    table syms can be provided.  Results are returned as strings; if the weight 
    flag is specified, the path scores are included
    """
    import pywrapfst as fst
    b = a.copy().project(project_output=project_output)
    if nshortest == 1:
        c = fst.shortestpath(b)
    else:
        c = fst.shortestpath(b, nshortest=nshortest, unique=True)
    nba = fst.push(c,push_weights=True).rmepsilon() 
    nb = []
    if nba.start() != -1:
        for arc1 in nba.arcs(nba.start()):
            w = arc1.weight
            nextstate = arc1.nextstate
            nbi = []
            if syms:
                nbi.append( syms.find(arc1.ilabel) )
            else:
                nbi.append( str(arc1.ilabel) )
            while nba.arcs(nextstate):
                try:
                    nextarc = nba.arcs(nextstate).next()
                except StopIteration:
                    break
                if syms:
                    nbi.append( syms.find(nextarc.ilabel) )
                else:
                    nbi.append( str(nextarc.ilabel) )
                nextstate = nextarc.nextstate
            if weight:
                nb.append( (' '.join(nbi), w.to_string()) )
            else:
                nb.append( ' '.join(nbi) )
    return nb
