"""
Name:        xcs_run.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------
XCS: Michigan-style Learning Classifier System - A LCS for Reinforcement Learning.  This XCS follows the version descibed in "An Algorithmic Description of XCS" published by Martin Butz and Stewart Wilson (2002).

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules------------------------------------
from xcs_timer import Timer
from config_parser import ConfigParser
from xcs_offline_environment import Offline_Environment
from xcs_online_environment import Online_Environment
from xcs_constants import cons
from boa_constants import bcons
from sys import argv
import random
#-----------------------------------------------------------


def getOptions( argv ):
    """ Get arguments by command line and assign them to Constant object. """
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0][1:]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    if 'seed' in opts:
        cons.random_seed = int( opts['seed'] )
    if 'N' in opts:
        cons.N = int( opts['N'] )
    if 'MCMC' in opts:
        bcons.B = int( opts['MCMC'] )
    if 'minPop' in opts:
        bcons.min_pop_size = int( opts['minPop'] )
    if 'maxParents' in opts:
        bcons.max_parents = int( opts['maxParents'] )
    if 'localPopSize' in opts:
        bcons.A = int( opts['localPopSize'] )
    if 'binaryBOA' in opts:
        bcons.binary_coding = True if opts['binaryBOA'].lower() == 'true' else False
    if 'useBOA' in opts:
        # True by default
        if opts['useBOA'].lower() == 'true':
            cons.is_boa = True
        else:
            cons.is_boa = False
    return opts

helpstr = """Failed attempt to run e-LCS.  Please ensure that a configuration file giving all run parameters has been specified."""

#Specify the name and file path for the configuration file.
configurationFile = "XCS_Configuration_File.txt"

#Obtain all run parameters from the configuration file and store them in the 'Constants' module.
ConfigParser(configurationFile)

#Initialize the 'Timer' module which tracks the run time of algorithm and it's different components.
timer = Timer()
cons.referenceTimer(timer)
getOptions( argv )

#Set random seed if specified.-----------------------------------------------
if cons.use_seed:
    random.seed(cons.random_seed)
else:
    random.seed(None)

if cons.online_data_generator:
    env = Online_Environment( cons.problem_type, cons.problem_sizes )
else:
    #Initialize the 'Environment' module which manages the data presented to the algorithm.  While e-LCS learns iteratively (one inistance at a time
    env = Offline_Environment()
cons.referenceEnv(env) #Passes the environment to 'Constants' (cons) so that it can be easily accessed from anywhere within the code.
cons.parseIterations() #Identify the maximum number of learning iterations as well as evaluation checkpoints.


from xcs_algorithm import XCS

#Run the e-LCS algorithm.
XCS()
