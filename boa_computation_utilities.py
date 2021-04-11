"""
Name:        boa_computation_utilities.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from xcs_constants import cons
import math
#------------------------------------------------------


def getPrecomputedCummulativeLog(i, j):
    return float ( precomputedCummulativeLogarithm[ j ]-precomputedCummulativeLogarithm[ i-1 ] )


def preComputeCummulativeLog( N ):
    res = [ 0 ]
    for i in range(N):
        res.append( math.log( float( i + 1 ) ) + res[i] )
    return res


def logGamma( n ):
    """ Compute log of gamma function of n. """
    if n == 1:
        return 0
    else:
        return getPrecomputedCummulativeLog( 1, n - 1 )


def initializeLogGamma():
    """ Precompute all cummulative logarithms. """
    global precomputedCummulativeLogarithm
    precomputedCummulativeLogarithm = preComputeCummulativeLog( cons.N + 3 )
