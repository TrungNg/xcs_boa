"""
Name:        boa_constants.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     August, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import------------------------------------------------

#------------------------------------------------------

class BoaConstants:
    def setConstants(self, params):
        """ General constants used for Bayesian Optimization Algorithm, which is collected from Configuration file. """
        self.error_boa = int(params['error_boa'])                                   #Saved as integer
        self.theta_boa = int(params['theta_boa'])                                   #Saved as integer
        self.pred_boa = int(params['pred_boa'])                                     #Saved as integer
        self.binary_coding = True if params['binaryCoding'].lower()=='true' else False    #whether using binary coding, if not, ternary coding is used.
        self.max_parents = int(params['maxParents'])
        self.min_pop_size = int(params['minPopulation'])
        self.A = int(params['localPopSize'])
        self.B = int(params['MCmcUpdates'])
        self.show_graph = True if params['showDecisionGraphs'] == 'True' else False


    def setLimitedValues(self, value_list):
        """ Set number of values for all variables in BN. """
        self.numb_values = []
        for i in range( len( value_list ) ):
            self.numb_values.append( len( value_list[ i ] ) )


    def setCycleTime(self, cycle_period):
        """ Set number of iterations for each time reconstruct the network. """
        self.cycle = cycle_period


    def setNumberOfVariables(self, number_of_vars):
        """ Set number of variables. """
        self.number_of_vars = number_of_vars


    def setComplexityPenalty(self, penalty):
        """ Set score metric penalty of model complexity, called every time building the Bayesian Network. """
        self.complex_penalty = penalty


bcons = BoaConstants()
