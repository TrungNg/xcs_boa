"""
Name:        xcs_outputfile_manager.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------
XCS: Michigan-style Learning Classifier System - A LCS for Reinforcement Learning.  This XCS follows the version descibed in "An Algorithmic Description of XCS" published by Martin Butz and Stewart Wilson (2002).

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules--------------
from xcs_constants import *
import copy
#-------------------------------------

class OutputFileManager:
    def writePopStats(self, out_file, train_eval, test_eval, iteration, pop, correct):
        """ Makes output text file which includes all of the evaluation statistics for a complete analysis of all training and testing data on the current XCS rule population. """
        try:
            pop_stats = open(out_file + '_'+ str(iteration)+'_PopStats.txt','w')
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', out_file + '_'+ str(iteration)+'_PopStats.txt')
            raise
        else:
            print("Writing Population Statistical Summary File...")

        #Evaluation of pop
        pop_stats.write("Performance Statistics:------------------------------------------------------------------------\n")
        pop_stats.write("Training Accuracy\tTesting Accuracy\tTraining Coverage\tTesting Coverage\n")

        if cons.test_file != 'None':
            pop_stats.write(str(train_eval[0])+"\t")
            pop_stats.write(str(test_eval[0])+"\t")
            pop_stats.write(str(train_eval[1]) +"\t")
            pop_stats.write(str(test_eval[1])+"\n\n")
        elif cons.train_file != 'None':
            pop_stats.write(str(train_eval[0])+"\t")
            pop_stats.write("NA\t")
            pop_stats.write(str(train_eval[1]) +"\t")
            pop_stats.write("NA\n\n")
        else:
            pop_stats.write("NA\t")
            pop_stats.write("NA\t")
            pop_stats.write("NA\t")
            pop_stats.write("NA\n\n")

        pop_stats.write("Population Characterization:------------------------------------------------------------------------\n")
        pop_stats.write("MacroPopSize\tMicroPopSize\tGenerality\n")
        pop_stats.write(str(len(pop.pop_set))+"\t"+ str(pop.micro_size)+"\t"+str(pop.ave_generality)+"\n\n")

        pop_stats.write("SpecificitySum:------------------------------------------------------------------------\n")
        headers = cons.env.format_data.train_headers #preserve order of original dataset

        for i in range(len(headers)):
            if i < len(headers)-1:
                pop_stats.write(str(headers[i])+"\t")
            else:
                pop_stats.write(str(headers[i])+"\n")

        # Prints out the Specification Sum for each attribute
        for i in range(len(pop.attribute_spec_list)):
            if i < len(pop.attribute_spec_list)-1:
                pop_stats.write(str(pop.attribute_spec_list[i])+"\t")
            else:
                pop_stats.write(str(pop.attribute_spec_list[i])+"\n")

        pop_stats.write("\nAccuracySum:------------------------------------------------------------------------\n")
        for i in range(len(headers)):
            if i < len(headers)-1:
                pop_stats.write(str(headers[i])+"\t")
            else:
                pop_stats.write(str(headers[i])+"\n")

        # Prints out the Accuracy Weighted Specification Count for each attribute
        for i in range(len(pop.attribute_acc_list)):
            if i < len(pop.attribute_acc_list)-1:
                pop_stats.write(str(pop.attribute_acc_list[i])+"\t")
            else:
                pop_stats.write(str(pop.attribute_acc_list[i])+"\n")

        #Time Track ---------------------------------------------------------------------------------------------------------
        pop_stats.write("\nRun Time(in minutes):------------------------------------------------------------------------\n")
        pop_stats.write(cons.timer.reportTimes())
        pop_stats.write("\nCorrectTrackerSave:------------------------------------------------------------------------\n")
        for i in range(len(correct)):
            pop_stats.write(str(correct[i])+"\t")

        pop_stats.close()


    def writePop(self, out_file, iteration, pop):
        """ Writes a tab delimited text file outputting the entire evolved rule population, including conditions, phenotypes, and all rule parameters. """
        try:
            rule_pop = open(out_file + '_'+ str(iteration)+'_RulePop.txt','w')
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', out_file + '_'+ str(iteration)+'_RulePop.txt')
            raise
        else:
            print("Writing Population as Data File...")

        #Write Header-----------------------------------------------------------------------------------------------------------------------------------------------
        data_link = cons.env.format_data
        headers = data_link.train_headers
        for i in range(len(headers)):
            rule_pop.write(str(headers[i])+"\t")
        rule_pop.write("Action\tPredict\tError\tFitness\tNumer\tGACount\tActionSetSize\tTimeStampGA\tInitTimeStamp\tSpecificity\tDeletionProb\tActionCount\n")

        #sort classifiers based on numerosity-----------------------------------------------------------------------------------------------------------------------
        sorted_pop = sorted(pop.pop_set, key=lambda x: x.numerosity, reverse=True)
        #Write each classifier--------------------------------------------------------------------------------------------------------------------------------------
        for cl in sorted_pop:
            rule_pop.write(str(cl.printClassifier()))

        rule_pop.close()
