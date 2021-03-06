"""
Name:        xcs_constants.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------
XCS: Michigan-style Learning Classifier System - A LCS for Reinforcement Learning.  This XCS follows the version descibed in "An Algorithmic Description of XCS" published by Martin Butz and Stewart Wilson (2002).

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

class Constants:
    def setConstants(self,par):
        """ Takes the parameters parsed as a dictionary from config_parser and saves them as global constants. """

        # Major Run Parameters -----------------------------------------------------------------------------------------
        self.online_data_generator = False if par[ 'onlineProblem' ].lower()=='false' else True     # Saved as Boolean
        if self.online_data_generator == True:
            self.problem_type = par[ 'onlineProblem' ]
            sizes = par[ 'problemSizes' ].split( '.' )
            self.problem_sizes = [ 0 ] * 3
            for i in range( len( sizes ) ):
                self.problem_sizes[ i ] = int( sizes[ i ] )

        self.train_file = par['trainFile']                                      #Saved as text
        self.test_file = par['testFile']                                        #Saved as text
        self.original_out_file = str(par['outFileName'])                        #Saved as text
        self.out_file = str(par['outFileName'])                                 #Saved as text
        self.learning_iterations = par['learningIterations']                    #Saved as text
        self.is_boa = True if par['usingBOA']=='True' else False                #Saved as Boolean
        self.N = int(par['N'])                                                  #Saved as integer
        self.p_spec = float(par['p_spec'])                                      #Saved as float
        self.multiple_runs = int(par['multipleRuns'])                           #Saved as integer

        # Logistical Run Parameters ------------------------------------------------------------------------------------
        if par['randomSeed'] == 'False' or par['randomSeed'] == 'false':
            self.use_seed = False                                               #Saved as Boolean
        else:
            self.use_seed = True                                                #Saved as Boolean
            self.random_seed = int(par['randomSeed'])                           #Saved as integer

        self.label_ID = par['labelInstanceID']                                  #Saved as text
        self.label_class = par['labelPhenotype']                            #Saved as text
        self.label_missing_data = par['labelMissingData']                       #Saved as text
        self.discrete_attribute_limit = int(par['discreteAttributeLimit'])      #Saved as integer
        self.tracking_frequency = int(par['trackingFrequency'])                 #Saved as integer

        # Supervised Learning Parameters -------------------------------------------------------------------------------
        self.nu = int(par['nu'])                                                #Saved as integer
        self.chi = float(par['chi'])                                            #Saved as float
        self.phi = float(par['phi'])                                            #Saved as float
        self.mu = float(par['mu'])                                              #Saved as float
        self.offset_epsilon = float(par['offset_epsilon'])                      #Saved as float
        self.alpha = float(par['alpha'])                                        #Saved as float
        self.gamma = float(par['gamma'])                                        #Saved as float
        self.theta_GA = int(par['theta_GA'])                                    #Saved as integer
        self.theta_mna = int(par['theta_mna'])                                  #Saved as integer
        self.theta_del = int(par['theta_del'])                                  #Saved as integer
        self.theta_sub = int(par['theta_sub'])                                  #Saved as integer
        self.err_sub = float(par['error_sub'])                                  #Saved as float
        self.beta = float(par['beta'])                                          #Saved as float
        self.delta = float(par['delta'])                                        #Saved as float
        self.init_pred = float(par['init_pred'])                                #Saved as float
        self.init_err = float(par['init_err'])                                  #Saved as float
        self.init_fit = float(par['init_fit'])                                  #Saved as float
        self.fitness_reduction = float(par['fitnessReduction'])                 #Saved as float
        self.exploration = float(par['exploration'])                            #Saved as float

        # Algorithm Heuristic Options -------------------------------------------------------------------------------
        self.do_ga_subsumption = bool(int(par['doGASubsumption']))
        self.do_actionset_subsumption = bool(int(par['doActionsetSubsumption']))    #Saved as Boolean
        self.selection_method = par['selectionMethod']                          #Saved as text
        self.theta_sel = float(par['theta_sel'])                                #Saved as float
        self.crossover_method = par['crossoverMethod']                          #Saved as text

        # PopulationReboot -------------------------------------------------------------------------------
        self.do_population_reboot = bool(int(par['doPopulationReboot']))        #Saved as Boolean
        self.pop_reboot_path = par['popRebootPath']                             #Saved as text


    def referenceTimer(self, timer):
        """ Store reference to the timer object. """
        self.timer = timer


    def referenceEnv(self, e):
        """ Store reference to environment object. """
        self.env = e


    def parseIterations(self):
        """ Parse the 'learningIterations' string to identify the maximum number of learning iterations as well as evaluation checkpoints. """
        checkpoints = self.learning_iterations.split('.')
        for i in range(len(checkpoints)):
            checkpoints[i] = int(checkpoints[i])

        self.learning_checkpoints = checkpoints
        self.max_iterations = self.learning_checkpoints[(len(self.learning_checkpoints)-1)]

        if self.tracking_frequency == 0:
            self.tracking_frequency = self.env.format_data.numb_train_instances  #Adjust tracking frequency to match the training data size - learning tracking occurs once every epoch

#To access one of the above constant values from another module, import GHCS_Constants * and use "cons.something"
cons = Constants()