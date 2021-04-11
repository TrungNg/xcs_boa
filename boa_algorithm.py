"""
Name:        boa_algorithm.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     September, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from boa_bayesian_network import BayesianNetwork
from boa_graph_operator import Operator, Splitter, Merger, MERGER, SPLITTER
from boa_computation_utilities import initializeLogGamma
from boa_constants import bcons
from xcs_constants import *
from xcs_classifier import Classifier
import math
import random
#------------------------------------------------------


class BOA:
    def __init__(self):
        if bcons.binary_coding == True:
            self.converter = BinaryConverterForBOA()
        else:
            self.converter = TernaryConverterForBOA()
        initializeLogGamma()
        self.operators = []


    def constructNetwork(self, population):
        """ construct or reconstruct a new Bayesian Network """
        self.pop = self.converter.encodePop( population )
        # math.log( len( self.pop ) )
        bcons.setComplexityPenalty( math.log2( len( self.pop ) ) * 0.5 )
        self.bn = BayesianNetwork( self.pop )
        self.computeInitialOperators()                                      # Compute all initial splitters on all "empty" decision graphs.
        self.selectOperator()
        # Loop until no good operator left.
        while len( self.operators ) > 0 and self.operators[ self.selected_idx ].gain > 0:
            new_leaves = self.operators[ self.selected_idx ].execute( self.bn )                 # Execute the best operator
            changed_graph = self.operators[ self.selected_idx ].decision_graph                  # the graph where selected operator executed.
            changed_nodes = self.operators[ self.selected_idx ].nodes                           # the leaves (nodes) where last operator executed.
            changed_graph.countLeaves( new_leaves )                                             # count the new leaves
            self.updateOperators( changed_graph, changed_nodes )                                # remove inappropriate operators
            self.computeMergers( changed_graph )                                                # Compute/recompute the merging operators in the affected decision graph
            self.computeSplitters( changed_graph, new_leaves )                                  # Compute possible splitters on new leaves
            self.selectOperator()                                                               # Compare to find the best operator
        self.bn.getTopologicalOdering()                     # Find the sampling order of the build Bayesian Network
        if bcons.show_graph:
            self.bn.showComponents()                        # (optional)Visualize all decision trees/graphs


    def updateOperators(self, changed_graph, changed_nodes):
        """ Update list of operators. Remove mergers of the graph and splitters on the leaves (nodes) where last operator executed. """
        for i in range( len( self.operators ) - 1, -1, -1 ):
            if ( self.operators[ i ].type == MERGER and self.operators[ i ].decision_graph == changed_graph ) \
            or ( self.operators[ i ].type == SPLITTER and self.operators[ i ].nodes[ 0 ] in changed_nodes ):
                self.operators.pop( i )                     # should remove best_operator from operators here.


    def selectOperator(self):
        """ Compare all legal operators of the BN and return the one giving the highest gain. """
        max_gain = -1
        # since all operators in self.operators must have positive gain and length of the list is always checked, below line is not needed.
        # self.selected_idx = -1
        for i in range( len( self.operators ) - 1, -1, -1 ):
            # Check if self.operators[ i ] is legal. Because of other splitters executed, previously added Splitters may become illegal.
            # If cutter is used, this should be changed!
            if self.operators[ i ].validate( self.bn ):
                if self.operators[ i ].gain > max_gain:
                    max_gain = self.operators[ i ].gain
                    self.selected_idx = i                                   # index of selected operator (to execute).
            else:
                # Remove illegal operator.
                self.operators.pop( i )
                self.selected_idx -= 1


    def computeInitialOperators(self):
        """ compute frequencies and split gains for all root nodes of decision graphs """
        for graph in self.bn.decision_graphs:
            graph.countLeaves()                                             # count all leaves as needed to find score_after for all operators.
            graph.computeFrequencies()                                      # Only need to compute freq for the first time.
            for leaf in graph.leaves:
                leaf.setNodeScore( Operator.computeNodeContribution( leaf.freq ) )
            self.computeSplitters( graph )


    def computeSplitters(self, decision_graph, leaves = None):
        """ Compute gains for all legal split operators in this decision graph and add to self.operators. """
        if leaves == None:
            leaves = decision_graph.leaves
        for leaf in leaves:
            for label in range( self.bn._n ):
                # avoid computing illegal split operators
                if label != decision_graph.target and ( not leaf.isAncestor( label ) ) \
                and ( self.bn.isEdge( label, decision_graph.target ) or self.bn.canAddEdge( label, decision_graph.target ) ):
                    new_splitter = Splitter( decision_graph, [ leaf ], label )
                    new_splitter.computeGain()
                    if new_splitter.gain > 0:
                        self.operators.append( new_splitter )               # Only add legal and positive-gain operators.


    def computeMergers(self, decision_graph, leaves = None):
        """ Compute gains for all legal merge operators in this decision graph and add to self.operators. """
        if leaves == None:
            leaves = decision_graph.leaves
        for i in range( len( leaves ) - 1 ):
            for j in range( i + 1, len( leaves ) ):
                if leaves[ i ].parents != leaves[ j ].parents:
                    new_merger = Merger( decision_graph, [ leaves[ i ], leaves[ j ] ] )
                    new_merger.computeGain()
                    if new_merger.gain > 0:
                        self.operators.append( new_merger )                 # Only add positive-gain operators. All mergers are legal.


""" Class used to convert population, in which instances might not be encoded as integer, to fit in BOA. """
class ConverterForBOA:
    def encodePop(self, xcs_pop):
        """ Encode list of instances to format fitting the implementation of BOA, all variables of each instance are discrete and should have max 3 values. """
        encoded_pop = []
        for xcs_cl in xcs_pop:
            encoded_pop.append( self.encode( xcs_cl ) )
        return encoded_pop


    def flipValue(self, boa_cl, index):
        """ Randomly choose a value from self.value_list[ index ] that differs from current value at "index" of boa_cl. """
        current_value = boa_cl[ index ]
        boa_cl[ index ] = random.choice( [ val for val in self.value_list[ index ] if val != current_value ] )


""" Class used to convert population, using ternary coding for BOA. Hard-coded """
class TernaryConverterForBOA(ConverterForBOA):
    def __init__(self):
        """ """
        self.value_list = [ [ 0, 1, 2 ] ] * cons.env.format_data.numb_attributes
        self.value_list.append( [ 0, 1 ] )
        bcons.setLimitedValues( self.value_list )
        bcons.setNumberOfVariables( cons.env.format_data.numb_attributes + 1 )


    def encode(self, xcs_cl):
        """ Convert to a filled list. This was written when condition and phenotype were both saved as string. """
        boa_cl = []
        for i in range( cons.env.format_data.numb_attributes ):
            if i in xcs_cl.specified_attributes:
                boa_cl.append( int( xcs_cl.condition[ xcs_cl.specified_attributes.index( i ) ] ) )
            else:
                boa_cl.append( 2 )
        boa_cl.append( int( xcs_cl.action ) )
        return boa_cl


    def decode(self, boa_cl, xcs_cl):
        """ Convert from a filled list to classifier. This was written when condition and phenotype were both saved as string. """
        xcs_cl.specified_attributes = []
        xcs_cl.condition = []
        for i in range( cons.env.format_data.numb_attributes ):
            if boa_cl[i] == 0:
                xcs_cl.specified_attributes.append(i)
                xcs_cl.condition.append( str(0) )
            elif boa_cl[i] == 1:
                xcs_cl.specified_attributes.append(i)
                xcs_cl.condition.append( str(1) )
        xcs_cl.action = str( boa_cl[ -1 ] )


""" Class used to convert population, using binary coding for BOA. Hard-coded """
class BinaryConverterForBOA(ConverterForBOA):
    def __init__(self):
        """ """
        self.value_list = [ [ 0, 1 ] ] * ( cons.env.format_data.numb_attributes * 2 + 1 )
        bcons.setLimitedValues( self.value_list )
        bcons.setNumberOfVariables( cons.env.format_data.numb_attributes * 2 + 1 )


    def encode(self, xcs_cl):
        """ Convert to a filled list. This was written when condition and action were both saved as string. """
        boa_cl = []
        for i in range( cons.env.format_data.numb_attributes ):
            if i in xcs_cl.specified_attributes:
                specified_value = int( xcs_cl.condition[ xcs_cl.specified_attributes.index( i ) ] )
                boa_cl.append( 0 )
                boa_cl.append( specified_value )
            else:
                boa_cl.append( 1 )
                if random.random() < 0.5:
                    boa_cl.append( 0 )
                else:
                    boa_cl.append( 1 )
        boa_cl.append( int( xcs_cl.action ) )
        return boa_cl


    def decode(self, boa_cl, xcs_cl):
        """ Convert from a filled list of int to classifier. This was written when condition and action were both saved as string. """
        xcs_cl.specified_attributes = []
        xcs_cl.condition = []
        for i in range( cons.env.format_data.numb_attributes ):
            if boa_cl[ 2*i ] == 0:
                xcs_cl.specified_attributes.append(i)
                xcs_cl.condition.append( str( boa_cl[ 2*i+1 ] ) )
        xcs_cl.action = str( boa_cl[ -1 ] )
