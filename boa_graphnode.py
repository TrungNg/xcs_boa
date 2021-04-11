"""
Name:        boa_graphnode.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from boa_constants import bcons
from boa_computation_utilities import logGamma
import copy
#------------------------------------------------------


class GraphElement:
    def __init__(self, number_of_frequencies, parent = None, value = None):
        """ Init a new graph leaf. """
        self.nfreqs = number_of_frequencies
        self.is_leaf = True                     # this element can be applied split operator
        self.cuttable = False                   # for cutting operator
        self.freq = [ 0 ] * self.nfreqs         # All nodes in same decision graph should have same number of frequencies.
        if parent == None:
            self.parents = []
            self.ancestors = set()
        else:
            self.ancestors = copy.deepcopy( parent.ancestors )
            self.ancestors.add( parent.label )
            self.parents = [ parent ]
            for i in range( self.nfreqs ):
                #- Number/frequency of instances going through self.parent,
                #- having the parent.label variable equal to value and target variable (of this graph) i.
                if isinstance( value, tuple ):
                    for val in value:
                        self.freq[ i ] += parent.count[ parent.label ][ val ][ i ]
                else:
                    self.freq[ i ] += parent.count[ parent.label ][ value ][ i ]


    def getNodeAncestors(self):
        """ get ancestors of this leaf. """
        return self.ancestors


    def growNode(self, label, value_split):
        """ split decision graph by make this leaf a node and develop 2 child leaves. """
        self.label = label
        self.childs = {}
        # Create child leaves, i corresponds to value of this node's label varaible
        for value in value_split:
            self.childs[ value ] = GraphElement( self.nfreqs, self, value )
        self.is_leaf = False                                      # Already splitted
        self.cuttable = True
        for parent in self.parents:
            parent.cuttable = False
        return


    def isAncestor(self, label):
        """ check whether label is one of the ancestors of this leaf/node. """
        return ( label in self.ancestors )


    def getChildNodes(self):
        """ Return list of all child nodes. """
        return list( self.childs.values() )


    def getLabel(self):
        """ return label of this node. """
        return self.label


    def resetFreq(self):
        """ Reset frequencies of target value of this leaf to 0. """
        # conditional probability of targeted variable to be 0/1 when travel through graph to this leaf
        numb = len( self.freq )
        self.freq = [ 0 ] * numb


    def resetCount(self):
        """ Reset counts of target value of this leaf to 0. """
        self.count = [ [ ( [ 0 ] * len( self.freq ) ) for _ in range( bcons.numb_values[ i ] ) ] for i in range( bcons.number_of_vars ) ]


    def incrementCount(self, label, label_value, target_value):
        """ Increase count of target value of this leaf by 1. """
        self.count[ label ][ label_value ][ target_value ] += 1


    def incrementFreq(self, target_value):
        """ Increase count of target value of this leaf by 1. """
        self.freq[ target_value ] += 1


    def setFreq(self, freq, target_value = None):
        """ Set frequency of target value of this leaf. """
        if target_value != None:
            self.freq[ target_value ] = freq
        else:
            self.freq = freq


    def getFreq(self, target_value = None):
        """ return frequency of target value of this leaf. """
        if target_value != None:
            return self.freq[ target_value ]
        return self.freq


    def gainFreq(self, delta, target_value):
        """ Set frequency of target value of this leaf. """
        self.freq[ target_value ] += delta


    def setNodeScore(self, score):
        """ Set score contribution of this node to value score. """
        self.score = score


    def getNodeScore(self):
        """ Get score contribution of this node to value score. """
        return self.score

