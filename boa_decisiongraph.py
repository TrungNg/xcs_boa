"""
Name:        boa_decisiongraph.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------
from boa_graphnode import GraphElement
from boa_constants import bcons
#------------------------------------------------------


class DecisionGraph:
	def __init__(self, population, target):
		self.population = population
		self.target = target				# target variable of the decision graph
		self.root_node = GraphElement( bcons.numb_values[ target ], None )
		self.best_operator = None
		self.leaves = [ self.root_node ]


	def iterateFromRoot(self, inst):
		""" Traverse a data instance from root to leaf. """
		node = self.root_node
		while node.is_leaf == False:
			for split_value, child in node.childs.items():
				if inst[ node.label ] == split_value or ( isinstance( split_value, tuple ) and ( inst[ node.label ] in split_value ) ):
					node = child
					break
		return node


	def countFrequencies(self, population = None,leaves = None):
		""" Count frequencies for all leaves. """
		if population == None:
			population = self.population
		if leaves == None:
			leaves = self.leaves
		for leaf in leaves:
			# initialize/reset the counters
			leaf.resetFreq()
		# compute the frequencies
		for inst in population:
			leaf = self.iterateFromRoot( inst )
			leaf.incrementFreq( inst[ self.target ] )


	def countLeaves(self, leaves = None):
		""" Count all counts for all leaves. """
		if leaves == None:
			leaves = self.leaves
		for leaf in leaves:
			# initialize/reset the counters
			leaf.resetCount()
		# count all the leaves
		for inst in self.population:
			# get the leaf node that this instance falls on
			leaf = self.iterateFromRoot( inst )
			if leaf in leaves:
				for label in range( bcons.number_of_vars ):
					leaf.incrementCount( label, inst[ label ], inst[ self.target ] )


	def computeFrequencies(self):
		""" Calibrate frequencies of all leaves. """
		for leaf in self.leaves:
			leaf.resetFreq()
			for target_value in range( bcons.numb_values[ self.target ] ):
				# Choose label 0 to compute frequencies, any label should give the same frequencies.
				for val_of_label_0 in range( bcons.numb_values[ 0 ] ):
					leaf.gainFreq( leaf.count[ 0 ][ val_of_label_0 ][ target_value ], target_value )


	def printGraph(self, shift_step = 3, node_list = []):
		""" Print/Visualize decision graph recursively. """
		child_node_list = []
		if node_list == []:
			node_list = [ self.root_node ]
		for node in node_list:
			print( " "*shift_step, end = '' )
			if node == None:
				print( " "*shift_step, end = '' )
			elif node.is_leaf == True:
				print("(-", end = '')
				for val in bcons.numb_values[ self.target ]:
					print( "%.2f" % node.freq[ val ], end ='-' )
				print(")", end = '')
			else:
				print("|X" + str( node.label ) + "|")
				child_node_list += node.getChildNodes()
		if len( child_node_list ) > 0:
			self.printGraph( shift_step, child_node_list )

