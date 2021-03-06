"""
Name:        xcs_algorithm.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules-------------------------------
from xcs_constants import *
from xcs_classifierset import ClassifierSet
from xcs_prediction import *
from xcs_class_accuracy import ClassAccuracy
from xcs_outputfile_manager import OutputFileManager
import copy
import random
import math
from boa_algorithm import BOA
from boa_constants import bcons
from xcs_classifier import Classifier
#------------------------------------------------------

class XCS:
    def __init__(self):
        """ Initializes the XCS algorithm """
        if cons.is_boa == True:
            algorithm = "XCS/BOA"
        else:
            algorithm = "XCS"
        print(algorithm + ": Running " + str( cons.multiple_runs ) + " times")
        #Global Parameters-------------------------------------------------------------------------------------
        self.population = None          # The rule population (the 'solution/model' evolved by XCS)
        self.learn_track = None       # Output file that will store tracking information during learning
        #self.previousState = None              # states received from environment from last time step

        for count in range( cons.multiple_runs ):
            print("Time " + str( count ) + ": Initializing Algorithm...")
            #-------------------------------------------------------
            # POPULATION REBOOT - Begin XCS learning from an existing saved rule population
            #-------------------------------------------------------
            if cons.do_population_reboot:
                self.populationReboot( count )
            #-------------------------------------------------------
            # NORMAL XCS - Run XCS from scratch on given data
            #-------------------------------------------------------
            else:
                try:
                    self.learn_track = open(cons.out_file+str(count)+'_LearnTrack.txt','w')
                except Exception as inst:
                    print(type(inst))
                    print(inst.args)
                    print(inst)
                    print('cannot open', cons.out_file+str(count)+'_LearnTrack.txt')
                    raise
                else:
                    self.learn_track.write("Explore_Iteration\tMacroPopSize\tMicroPopSize\tAccuracy_Estimate\tAveGenerality\tExpRules\tTime(min)\n")

                # Instantiate Population---------
                self.population = ClassifierSet()
                self.explore_iter = 0
                self.tracked_results  = [0] * cons.tracking_frequency
                self.exploit_iters = 0

            #Run the XCS/BOA algorithm--------------------------------------------------------------------------
            self.boa = None
            bcons.setCycleTime( int( cons.N/2 ) )
            self.run_XCS_BOA( count )


    def run_XCS_BOA(self, expriment_count):
        """ Runs the initialized XCS algorithm. """
        #--------------------------------------------------------------
        print("Learning Checkpoints: " +str(cons.learning_checkpoints))
        print("Maximum Iterations: " +str(cons.max_iterations))
        print("Beginning XCS learning iterations.")
        print("------------------------------------------------------------------------------------------------------------------------------------------------------")

        #-------------------------------------------------------
        # MAJOR LEARNING LOOP
        #-------------------------------------------------------
        while self.explore_iter < cons.max_iterations:
            #-------------------------------------------------------
            # GET NEW INSTANCE AND RUN A LEARNING ITERATION
            #-------------------------------------------------------
            state_phenotype = cons.env.getTrainInstance()
            self.runIteration(state_phenotype, self.explore_iter)
            #-------------------------------------------------------------------------------------------------------------------------------
            # EVALUATIONS OF ALGORITHM
            #-------------------------------------------------------------------------------------------------------------------------------
            cons.timer.startTimeEvaluation()
            #-------------------------------------------------------
            # TRACK LEARNING ESTIMATES
            #-------------------------------------------------------
            if (self.explore_iter%cons.tracking_frequency) == (cons.tracking_frequency - 1) and self.explore_iter > 0:
                self.population.runPopAveEval()
                tracked_accuracy = sum( self.tracked_results )/float( self.exploit_iters ) #Accuracy over the last "tracking_frequency" number of iterations.
                self.exploit_iters = 0
                self.tracked_results  = [0] * cons.tracking_frequency
                self.learn_track.write(self.population.getPopTrack(tracked_accuracy, self.explore_iter+1,cons.tracking_frequency)) #Report learning progress to standard out and tracking file.
            cons.timer.stopTimeEvaluation()

            #-------------------------------------------------------
            # CHECKPOINT - COMPLETE EVALUTATION OF POPULATION - strategy different for discrete vs continuous phenotypes
            #-------------------------------------------------------
            if (self.explore_iter + 1) in cons.learning_checkpoints:
                cons.timer.startTimeEvaluation()
                print("------------------------------------------------------------------------------------------------------------------------------------------------------")
                print("Running Population Evaluation after " + str(self.explore_iter + 1)+ " iterations.")

                self.population.runPopAveEval( )
                self.population.runAttGeneralitySum(True)
                cons.env.startEvaluationMode()  #Preserves learning position in training data
                if cons.test_file != 'None': #If a testing file is available.
                    if cons.env.format_data.discrete_action:
                        train_eval = self.doPopEvaluation(True)
                        test_eval = self.doPopEvaluation(False)
                    else:
                        train_eval = self.doContPopEvaluation(True)
                        test_eval = self.doContPopEvaluation(False)
                else:  #Only a training file is available
                    if cons.env.format_data.discrete_action:
                        train_eval = self.doPopEvaluation(True)
                        test_eval = None
                    else:
                        train_eval = self.doContPopEvaluation(True)
                        test_eval = None

                cons.env.stopEvaluationMode() #Returns to learning position in training data
                cons.timer.stopTimeEvaluation()
                cons.timer.returnGlobalTimer()

                #Write output files----------------------------------------------------------------------------------------------------------
                OutputFileManager().writePopStats(cons.out_file+str(expriment_count), train_eval, test_eval, self.explore_iter + 1, self.population, self.tracked_results)
                OutputFileManager().writePop(cons.out_file+str(expriment_count), self.explore_iter + 1, self.population)
                #----------------------------------------------------------------------------------------------------------------------------

                print("Continue Learning...")
                print("------------------------------------------------------------------------------------------------------------------------------------------------------")

            #-------------------------------------------------------
            # ADJUST MAJOR VALUES FOR NEXT ITERATION
            #-------------------------------------------------------
            self.explore_iter += 1       # Increment current learning iteration

        # Once XCS has reached the last learning iteration, close the tracking file
        self.learn_track.close()
        print("XCS Run Complete\n-----------------------------------------------\n\n")


    def runIteration(self, state_phenotype, explore_iter):
        """ Run a single XCS learning iteration. """
        reward = 0
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # FORM A MATCH SET - includes covering
        #-----------------------------------------------------------------------------------------------------------------------------------------
        self.population.makeMatchSet(state_phenotype[0], explore_iter)
        if self.population.match_set == []:
            return
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # MAKE A PREDICTION - utilized here for tracking estimated learning progress.  Typically used in the explore phase of many LCS algorithms.
        #-----------------------------------------------------------------------------------------------------------------------------------------
        cons.timer.startTimeEvaluation()
        prediction = Prediction(self.population)
        selected_phenotype = prediction.getDecision()
        #-------------------------------------------------------
        # DISCRETE PHENOTYPE PREDICTION
        #-------------------------------------------------------
        if cons.env.format_data.discrete_action:
            if selected_phenotype == state_phenotype[1]:
                reward = 1000
            if prediction.is_exploit:
                self.exploit_iters += 1
                if reward == 1000:
                    self.tracked_results[ explore_iter%cons.tracking_frequency ] = 1
        #-------------------------------------------------------
        # CONTINUOUS PHENOTYPE PREDICTION
        #-------------------------------------------------------
        else:
            prediction_error = math.fabs( selected_phenotype - float( state_phenotype[ 1 ] ) )
            phenotype_range = cons.env.format_data.action_list[ 1 ] - cons.env.format_data.action_list[ 0 ]
            accuracy_estimate = 1.0 - ( prediction_error / float( phenotype_range ) )
            self.tracked_results[ explore_iter%cons.tracking_frequency ] = accuracy_estimate
            reward = 1000 * accuracy_estimate
        cons.timer.stopTimeEvaluation()
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # FORM AN ACTION SET
        #-----------------------------------------------------------------------------------------------------------------------------------------
        #self.population.makeActionSet(state_phenotype[1])    # make Action Set for XCS
        self.population.makeActionSet( selected_phenotype )
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # UPDATE PARAMETERS
        #-----------------------------------------------------------------------------------------------------------------------------------------
        self.population.updateSets( reward )
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # SUBSUMPTION - APPLIED TO MATCH SET - A heuristic for addition additional generalization pressure to XCS
        #-----------------------------------------------------------------------------------------------------------------------------------------
        if cons.do_actionset_subsumption:
            cons.timer.startTimeSubsumption()
            self.population.doActionSetSubsumption()
            cons.timer.stopTimeSubsumption()
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # BUILD A GLOBAL BAYESIAN NETWORK IF CONDITIONS MET
        #-----------------------------------------------------------------------------------------------------------------------------------------
        if cons.is_boa:
            if explore_iter % bcons.cycle == 0:
                population_boa = self.population.makeBOAPopulation()# explore_iter )
                if len( population_boa ) > bcons.min_pop_size:
                    if self.boa == None:
                        self.boa = BOA()
                    self.boa.constructNetwork( population_boa )
            if self.boa == None or ( self.boa != None and self.population.samplingOffspring( self.boa, state_phenotype[ 0 ], explore_iter ) == False ):
                self.population.runGA( explore_iter, state_phenotype[ 0 ] )
        else:
            #-----------------------------------------------------------------------------------------------------------------------------------------
            # RUN THE GENETIC ALGORITHM - Discover new offspring rules from a selected pair of parents
            #-----------------------------------------------------------------------------------------------------------------------------------------
            self.population.runGA( explore_iter, state_phenotype[ 0 ] )
        #-----------------------------------------------------------------------------------------------------------------------------------------
        # SELECT RULES FOR DELETION - This is done whenever there are more rules in the population than 'N', the maximum population size.
        #-----------------------------------------------------------------------------------------------------------------------------------------
        #self.population.deletion(explore_iter)
        self.population.clearSets() #Clears the match and action sets for the next learning iteration


    def doPopEvaluation(self, is_train):
        """ Performs a complete evaluation of the current rule population.  The population is unchanged throughout this evaluation. Works on both training and testing data. """
        if is_train:
            my_type = "TRAINING"
        else:
            my_type = "TESTING"
        no_match = 0                     # How often does the population fail to have a classifier that matches an instance in the data.
        tie = 0                         # How often can the algorithm not make a decision between classes due to a tie.
        cons.env.resetDataRef( is_train ) # Go to the first instance in dataset
        phenotype_list = cons.env.format_data.action_list
        #----------------------------------------------
        class_accuracies = {}
        for each in phenotype_list:
            class_accuracies[each] = ClassAccuracy()
        #----------------------------------------------
        if is_train:
            instances = cons.env.format_data.numb_train_instances
        else:
            instances = cons.env.format_data.numb_test_instances
        #----------------------------------------------------------------------------------------------
        for _ in range(instances):
            if is_train:
                state_action = cons.env.getTrainInstance()
            else:
                state_action = cons.env.getTestInstance()
            #-----------------------------------------------------------------------------
            self.population.makeEvalMatchSet(state_action[0])
            prediction = Prediction(self.population, True)
            selected_action = prediction.getDecision()
            #-----------------------------------------------------------------------------

            if selected_action == None:
                no_match += 1
            elif selected_action == 'Tie':
                tie += 1
            else: #Instances which failed to be covered are excluded from the accuracy calculation
                for each in phenotype_list:
                    is_correct = False
                    accurate_action = False
                    right_action = state_action[1]
                    if each == right_action:
                        is_correct = True
                    if selected_action == right_action:
                        accurate_action = True
                    class_accuracies[each].updateAccuracy(is_correct, accurate_action)

            self.population.clearSets()
        #----------------------------------------------------------------------------------------------
        #Calculate Standard Accuracy--------------------------------------------
        correct_cases = class_accuracies[phenotype_list[0]].T_myClass + class_accuracies[phenotype_list[0]].T_otherClass
        incorrect_cases = class_accuracies[phenotype_list[0]].F_myClass + class_accuracies[phenotype_list[0]].F_otherClass
        accuracy = float(correct_cases) / float(correct_cases + incorrect_cases)

        #Calculate Balanced Accuracy---------------------------------------------
        T_mySum = 0
        T_otherSum = 0
        F_mySum = 0
        F_otherSum = 0
        for each in phenotype_list:
            T_mySum += class_accuracies[each].T_myClass
            T_otherSum += class_accuracies[each].T_otherClass
            F_mySum += class_accuracies[each].F_myClass
            F_otherSum += class_accuracies[each].F_otherClass
        balanced_accuracy = ((0.5*T_mySum / (float(T_mySum + F_otherSum)) + 0.5*T_otherSum / (float(T_otherSum + F_mySum)))) # BalancedAccuracy = (Specificity + Sensitivity)/2

        #Adjustment for uncovered instances - to avoid positive or negative bias we incorporate the probability of guessing a phenotype by chance (e.g. 50% if two phenotypes)
        prediction_fail = float(no_match)/float(instances)
        prediction_ties = float(tie)/float(instances)
        covered_instances = 1.0 - prediction_fail
        prediction_made = 1.0 - (prediction_fail + prediction_ties)

        adjusted_accuracy = (accuracy * prediction_made) + ((1.0 - prediction_made) * (1.0 / float(len(phenotype_list))))
        adjusted_balanced_accuracy = (balanced_accuracy * prediction_made) + ((1.0 - prediction_made) * (1.0 / float(len(phenotype_list))))

        #Adjusted Balanced Accuracy is calculated such that instances that did not match have a consistent probability of being correctly classified in the reported accuracy.
        print("-----------------------------------------------")
        print(str(my_type)+" Accuracy Results:-------------")
        print("Instance Coverage = "+ str(covered_instances*100.0)+ '%')
        print("Prediction Ties = "+ str(prediction_ties*100.0)+ '%')
        print(str(correct_cases) + ' out of ' + str(instances) + ' instances covered and correctly classified.')
        print("Standard Accuracy (Adjusted) = " + str(adjusted_accuracy))
        print("Balanced Accuracy (Adjusted) = " + str(adjusted_balanced_accuracy))
        #Balanced and Standard Accuracies will only be the same when there are equal instances representative of each phenotype AND there is 100% covering.
        result = [adjusted_balanced_accuracy, covered_instances]
        return result


    def doContPopEvaluation(self, is_train):
        """ Performs evaluation of population via the copied environment. Specifically developed for continuous phenotype evaulation.
        The population is maintained unchanging throughout the evaluation.  Works on both training and testing data. """
        if is_train:
            my_type = "TRAINING"
        else:
            my_type = "TESTING"
        no_match = 0 #How often does the population fail to have a classifier that matches an instance in the data.
        cons.env.resetDataRef(is_train) #Go to first instance in data set
        accuracy_estimate_sum = 0

        if is_train:
            instances = cons.env.format_data.numb_train_instances
        else:
            instances = cons.env.format_data.numb_test_instances
        #----------------------------------------------------------------------------------------------
        for _ in range(instances):
            if is_train:
                state_action = cons.env.getTrainInstance()
            else:
                state_action = cons.env.getTestInstance()
            #-----------------------------------------------------------------------------
            self.population.makeEvalMatchSet(state_action[0])
            prediction = Prediction(self.population)
            selected_action = prediction.getDecision()
            #-----------------------------------------------------------------------------
            if selected_action == None:
                no_match += 1
            else: #Instances which failed to be covered are excluded from the initial accuracy calculation
                prediction_err = math.fabs(float(selected_action) - float(state_action[1]))
                action_range = cons.env.format_data.action_list[1] - cons.env.format_data.action_list[0]
                accuracy_estimate_sum += 1.0 - (prediction_err / float(action_range))

            self.population.clearSets()
        #----------------------------------------------------------------------------------------------
        #Accuracy Estimate
        if instances == no_match:
            accuracy_estimate = 0
        else:
            accuracy_estimate = accuracy_estimate_sum / float(instances - no_match)

        #Adjustment for uncovered instances - to avoid positive or negative bias we incorporate the probability of guessing a phenotype by chance (e.g. 50% if two phenotypes)
        covered_instances = 1.0 - (float(no_match)/float(instances))
        adjusted_accuracy_estimate = accuracy_estimate_sum / float(instances) #no_matchs are treated as incorrect predictions (can see no other fair way to do this)

        print("-----------------------------------------------")
        print(str(my_type)+" Accuracy Results:-------------")
        print("Instance Coverage = "+ str(covered_instances*100.0)+ '%')
        print("Estimated Prediction Accuracy (Ignore uncovered) = " + str(accuracy_estimate))
        print("Estimated Prediction Accuracy (Penalty uncovered) = " + str(adjusted_accuracy_estimate))
        #Balanced and Standard Accuracies will only be the same when there are equal instances representative of each phenotype AND there is 100% covering.
        result_list = [adjusted_accuracy_estimate, covered_instances]
        return result_list


    def populationReboot(self, experiment_count):
        """ Manages the reformation of a previously saved XCS classifier population. """
        cons.timer.setTimerRestart(cons.pop_reboot_path) #Rebuild timer objects
        #--------------------------------------------------------------------
        try: #Re-open track learning file for continued tracking of progress.
            self.learn_track = open(cons.out_file+str(experiment_count)+'_LearnTrack.txt','a')
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', cons.out_file+str(experiment_count)+'_LearnTrack.txt')
            raise

        #Extract last iteration from file name---------------------------------------------
        temp = cons.pop_reboot_path.split('_')
        iter_ref = len(temp)-1
        completed_iterations = int(temp[iter_ref])
        print("Rebooting rule population after " +str(completed_iterations)+ " iterations.")
        self.explore_iter = completed_iterations-1
        for i in range(len(cons.learning_checkpoints)):
            cons.learning_checkpoints[i] += completed_iterations
        cons.max_iterations += completed_iterations

        #Rebuild existing population from text file.--------
        self.population = ClassifierSet(cons.pop_reboot_path)
        #---------------------------------------------------
        try: #Obtain correct track
            f = open(cons.pop_reboot_path+"_PopStats.txt", 'r')
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', cons.pop_reboot_path+"_PopStats.txt")
            raise
        else:
            correct_ref = 26 #File reference position
            temp_line = None
            for i in range(correct_ref):
                temp_line = f.readline()
            temp_list = temp_line.strip().split('\t')
            self.tracked_results = temp_list
            if cons.env.format_data.discrete_action:
                for i in range( len( self.tracked_results ) ):
                    self.tracked_results[i] = int( self.correct[i] )
            else:
                for i in range( len( self.tracked_results ) ):
                    self.tracked_results[i] = float( self.tracked_results[i] )
            f.close()
