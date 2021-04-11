"""
Name:        boa_graph_operator.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from boa_bayesian_network import BayesianNetwork
from boa_decisiongraph import DecisionGraph
from boa_graphnode import GraphElement
from boa_constants import bcons
from boa_computation_utilities import logGamma
import operator
import math
#------------------------------------------------------
#Constants---------------------------------------------
SPLITTER    = 0
MERGER      = 1
CUTTER      = 2
#------------------------------------------------------


# Graph Operator is chosen to be higher level than Decision Graph.
class Operator:
    def __init__(self, graph, nodes ):
        """ Initialize Operator. """
        self.decision_graph = graph
        self.nodes = nodes
        self.gain = -1


    def validate(self, _):
        """ Check if this operator is legal. """
        return True


    def computeGain(self):
        """ compute gain of the operator """
        raise RuntimeError( "Operator.computeGain: not implmented here" )


    def execute(self):
        """ compute gain of the operator """
        raise RuntimeError( "Operator.execute: not implmented here" )


    @staticmethod
    def computeNodeContribution( freqs ):
        """ Compute contribution of a node (leave) to BN scoring metric. """
        all_counts = 0
        score = 0
        prior = len( freqs )                    # Read BD metric for reference
        for f in freqs:
            all_counts += f
            score += logGamma( 1 + f )
        score += logGamma( prior ) - logGamma( prior + all_counts )
        return score


class Splitter( Operator ):
    def __init__(self, graph, nodes, label ):
        """ Initialize Splitter operator. """
        self.label = label
        self.type = SPLITTER
        super().__init__( graph, nodes )


    def validate(self, bn):
        """ Check if this operator is legal. """
        return ( bn.isEdge( self.label, self.decision_graph.target ) or bn.canAddEdge( self.label, self.decision_graph.target ) )


    def computeGain(self):
        """ compute gain of the operator. Hard-coded for binary and ternary variables. """
        self.new_contributions = {}
        score_before = self.nodes[ 0 ].getNodeScore()
        score_after = 0
        self.best_split = [ i for i in range( bcons.numb_values[ self.label ] ) ]               # Default split
        ###------------------this part is HARD-CODED to deal with both cases of base 2 and 3---------------###
        for i in range( bcons.numb_values[ self.label ] ):
            self.new_contributions[ i ] = Operator.computeNodeContribution( self.nodes[ 0 ].count[ self.label ][ i ] )
        if bcons.numb_values[ self.label ] == 2:
            for i in range( 2 ):
                score_after += self.new_contributions[ i ]
                self.gain = score_after - score_before - bcons.complex_penalty
        elif bcons.numb_values[ self.label ] == 3:
            ###----------------------complete split-------------------###
            for i in range( 3 ):
                score_after += self.new_contributions[ i ]
            self.gain = score_after - score_before - 2 * bcons.complex_penalty
            ###----------------------partial split--------------------###
            for i in range( 3 ):
                score_after = 0
                # one leaf for value ( i + 2 ) % 3 of self.label and one leaf for set(i, ( i + 1 ) % 3) of self.label
                score_after = self.new_contributions[ ( i + 2 ) % 3 ]
                tmp_freqs = [ self.nodes[ 0 ].count[ self.label ][ i ][ j ] + self.nodes[ 0 ].count[ self.label ][ ( i + 1 )%3 ][ j ] \
                             for j in range( self.nodes[ 0 ].nfreqs ) ]
                self.new_contributions[ i, ( i + 1 ) % 3 ] = Operator.computeNodeContribution( tmp_freqs )
                score_after += self.new_contributions[ i, ( i + 1 ) % 3 ]
                tmp_gain = score_after - score_before - bcons.complex_penalty
                if tmp_gain > self.gain:
                    self.gain = tmp_gain
                    self.best_split = [ ( i + 2 ) % 3, ( i, ( i + 1 ) % 3 ) ]


    def execute(self, bn):
        """ Execute Splitter. """
        #------------------changes on decision graph------------------#
        self.decision_graph.leaves.remove( self.nodes[ 0 ] )
        self.nodes[ 0 ].growNode( self.label, self.best_split )
        for i in self.best_split:
            child = self.nodes[ 0 ].childs[ i ]
            child.setNodeScore( self.new_contributions[ i ] )
            self.decision_graph.leaves.append( child )
        #------------------changes on bayesian network----------------#
        bn.addEgde( self.label, self.decision_graph.target )
        return self.nodes[ 0 ].getChildNodes()


class Merger( Operator ):
    def __init__(self, graph, nodes):
        """ Initialize Splitter operator. """
        self.type = MERGER
        super().__init__( graph, nodes )


    def computeGain(self):
        """ compute gain of the operator """
        score_before = 0
        for node in self.nodes:
            score_before += node.getNodeScore()
        new_freqs = [ self.nodes[ 0 ].freq[ i ] + self.nodes[ 1 ].freq[ i ] for i in range( self.nodes[ 0 ].nfreqs ) ]
        score_after = self.new_contribution = Operator.computeNodeContribution( new_freqs )
        self.gain = score_after - score_before + bcons.complex_penalty


    def execute(self, _):
        """ Apply Merger. """
        # Keep nodes[0] and remove nodes[1], point all nodes[1].parents (or ancestors if needed) to nodes[0].
        self.decision_graph.leaves.remove( self.nodes[ 1 ] )
        self.nodes[ 0 ].parents += self.nodes[ 1 ].parents
        self.nodes[ 0 ].ancestors |= self.nodes[ 1 ].ancestors
        ###--this part is for counting leaves by iterating from root node to leaves--###
        for parent in self.nodes[ 1 ].parents:
            for split_values, child in parent.childs.items():
                if child == self.nodes[ 1 ]:
                    parent.childs[ split_values ] = self.nodes[ 0 ]       # Redirect to self.nodes[0] from self.nodes[1]
                    break
        ###-------------------------------------end----------------------------------###
        for i in range( bcons.numb_values[ self.decision_graph.target ] ):
            self.nodes[ 0 ].freq[ i ] += self.nodes[ 1 ].freq[ i ]
        self.nodes[ 0 ].setNodeScore( self.new_contribution )
        return [ self.nodes[ 0 ] ]

