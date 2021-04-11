"""
Name:        boa_bayesian_network.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from boa_decisiongraph import DecisionGraph
#from boa_graphnode import GraphElement
from boa_constants import bcons
import math
import random
#------------------------------------------------------
#Constants---------------------------------------------

#------------------------------------------------------


class BayesianNetwork:
    def __init__(self, population):
        self._max_incoming_edges = bcons.max_parents
        self._n =  bcons.number_of_vars                      # number of vertices (nodes)
        self.initEdges()
        self.decision_graphs = [ DecisionGraph( population, i ) for i in range( self._n ) ]
        self.best_operator = None


    def initEdges(self):
        """ Initialize variables of edges in BN. """
        self.num_in = [ 0 ] * self._n
        self.num_out = [ 0 ] * self._n
        self.parent_list = [ [] for _ in range( self._n ) ]
        self.path = set()
        self.edge = set()
        for i in range( self._n ):
            self.path.add(( i, i ))
            self.edge.add(( i, i ))


    def addEgde(self, dep, des):
        """ Mark a direct or indirect path between 2 nodes in BN. """
        if ( dep, des ) in self.edge:
            return
        else:
            self.edge.add(( dep, des ))
        self.path.add(( dep, des ))
        self.num_in[ des ] += 1
        self.num_out[ dep ] += 1
        self.parent_list[ des ].append( dep )
        for i in range( self._n ):
            if ( i, dep ) in self.path:
                for j in range( self._n ):
                    if ( ( des, j ) in self.path ) and j != i:
                        self.path.add(( i, j ))


    def showComponents(self):
        """ Display all Decision graphs of current Bayesian Network. """
        for graph in self.decision_graphs:
            graph.printGraph()


    def canAddEdge(self, dep, des):
        """ Check if expected edge not created cirle and not exceed max number of parents for node des. """
        return ( ( ( dep, des ) not in self.edge ) and ( self.num_in[ des ] < self._max_incoming_edges ) and ( ( des, dep ) not in self.path ) )


    def isExistingPath(self, dep, des):
        """ Check if there is a path from dep to des. """
        return ( ( dep, des ) in self.path )


    def isEdge(self, dep, des):
        """ Check if there is a path from dep to des. """
        return ( ( dep, des ) in self.edge )


    def getTopologicalOdering(self):
        """ Get ordering of variables for generating new instances. """
        self.index = []
        added = [ False for i in range( self._n ) ]
        added_counter = 0
        while added_counter < self._n:
            for i in range( self._n ):
                if not added[ i ]:
                    is_addable = True
                    for j in range( self.num_in[ i ] ):
                        if not added[ self.parent_list[ i ][ j ] ]:
                            is_addable = False
                            break
                    if is_addable:
                        self.index.append( i )
                        added_counter += 1
                        added[ i ] = True


    def getInstanceLikelihood(self, inst):
        """ Calculate likelihood of an instance. """
        likelihood = 1
        for i in range( self._n ):
            leaf = self.decision_graphs[ i ].iterateFromRoot( inst )
            freq_sum = float( sum( leaf.freq ) )
            if freq_sum != 0:
                # likelihood is production of all conditional probabilities (normalized to 0.05 to 0.95 to avoid 0)
                likelihood *= ( ( leaf.freq[ inst[ i ] ] / freq_sum ) * 0.9 + 0.05 )
            else:
                likelihood *= 0.05
                #likelihood *= ( 0.9 / len( leaf.freq ) + 0.05)
        return likelihood


    def generateInstance(self, n):
        """ Generate n new instance(s) from Bayesian Network. """
        instances = [ [ None for _ in range( self._n ) ] for _ in range( n ) ]
        for j in range( n ):
            for i in range( self._n ):
                position = self.index[ i ]
                leaf = self.decision_graphs[ position ].iterateFromRoot( instances[ j ] )
                fsum = sum( leaf.freq )
                if fsum == 0:
                    # If all frequencies of the leaf are 0, then the later part of choosing value doesn't work. Then randomly choose a value.
                    instances[ j ][ position ] = random.choice( range( bcons.numb_values[ position ] ) )
                    continue
                random_point = random.uniform( 0, fsum )
                accumulated_prob = 0
                for val in range( bcons.numb_values[ position ] ):
                    accumulated_prob += leaf.freq[ val ]
                    if accumulated_prob >= random_point:
                        instances[ j ][ position ] = val
                        break
        return instances
