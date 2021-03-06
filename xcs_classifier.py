"""
Name:        xcs_classifier.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:

---------------------------------------------------------------------------------------------------------------------------------------------------------
XCS: Michigan-style Learning Classifier System - A LCS for Reinforcement Learning.  This XCS follows the version descibed in "An Algorithmic Description of XCS" published by Martin Butz and Stewart Wilson (2002).

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules---------------
from xcs_constants import *
import random
import copy
import math
#--------------------------------------

class Classifier:
    def __init__(self,a=None,b=None,c=None):
        #Major Parameters --------------------------------------------------
        self.specified_attributes = []      # Attribute Specified in classifier: Similar to Bacardit 2009 - ALKR + GABIL, continuous and discrete rule representation
        self.condition = []                 # States of Attributes Specified in classifier: Similar to Bacardit 2009 - ALKR + GABIL, continuous and discrete rule representation
        self.action = None                  # Class if the endpoint is discrete, and a continuous phenotype if the endpoint is continuous

        self.prediction = cons.init_pred    # Classifier payoff - initialized to a constant initial payoff value
        self.error = cons.init_err          # Classifier error - initialized to a constant initial error value
        self.fitness = cons.init_fit        # Classifier fitness - initialized to a constant initial fitness value
        self.accuracy = 0.0                 # Classifier accuracy - Accuracy calculated using only instances in the dataset which this rule matched.
        self.numerosity = 1                 # The number of rule copies stored in the population.  (Indirectly stored as incremented numerosity)
        self.mean_actionset_sz = 1.0        # A parameter used in deletion which reflects the size of match sets within this rule has been included.
        self.delete_vote = 0.0              # The current deletion weight for this classifier.

        #Experience Management ---------------------------------------------
        self.ga_timestamp = None            # Time since rule last in a match set.
        self.init_timestamp = None          # Iteration in which the rule first appeared.

        #Classifier Accuracy Tracking --------------------------------------
        self.ga_count = 0
        self.action_cnt = 0                 # The total number of times this classifier was chosen in action set

        if isinstance(b,list):
            self.classifierCovering(a,b,c)
        elif isinstance(a,Classifier):
            self.classifierCopy(a, b)
        elif isinstance(a,list) and b == None:
            self.rebootClassifier(a)
        else:
            print("Classifier: Error building classifier.")

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # CLASSIFIER CONSTRUCTION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def classifierCovering(self, explore_iter, state, action):
        """ Makes a new classifier when the covering mechanism is triggered.  The new classifier will match the current training instance.
        Covering will NOT produce a default rule (i.e. a rule with a completely general condition). """
        #Initialize new classifier parameters----------
        self.ga_timestamp = explore_iter
        self.init_timestamp = explore_iter
        data_info = cons.env.format_data
        #-------------------------------------------------------
        # DISCRETE PHENOTYPE
        #-------------------------------------------------------
        if data_info.discrete_action:
            if action != None:
                self.action = action
            else:
                self.action = random.choice(cons.env.format_data.action_list)
        #-------------------------------------------------------
        # CONTINUOUS PHENOTYPE
        #-------------------------------------------------------
        else:
            action_range = data_info.action_list[1] - data_info.action_list[0]
            range_radius = random.randint(25,75)*0.01*action_range / 2.0 #Continuous initialization domain radius.
            if action == None:
                action = data_info.action_list[0] + range_radius + random.random() * ( action_range - 2 * range_radius )
            low = float(action) - range_radius
            high = float(action) + range_radius
            self.action = [ low, high ] #ALKR Representation, Initialization centered around training instance  with a range between 25 and 75% of the domain size.
        #-------------------------------------------------------
        # GENERATE MATCHING CONDITION
        #-------------------------------------------------------
        while len(self.specified_attributes) < 1:
            for att in range(len(state)):
                if random.random() < cons.p_spec and state[att] != cons.label_missing_data:
                    self.specified_attributes.append(att)
                    self.condition.append(self.buildMatch(att, state))


    def classifierCopy(self, old_cl, explore_iter):
        """  Constructs an identical Classifier.  However, the experience of the copy is set to 0 and the numerosity
        is set to 1 since this is indeed a new individual in a population. Used by the genetic algorithm to generate
        offspring based on parent classifiers."""
        self.specified_attributes = copy.deepcopy(old_cl.specified_attributes)
        self.condition = copy.deepcopy(old_cl.condition)
        self.action = copy.deepcopy(old_cl.action)
        self.ga_timestamp = explore_iter
        self.init_timestamp = explore_iter
        self.prediction = old_cl.prediction
        self.error = old_cl.error
        self.fitness = old_cl.fitness


    def rebootClassifier(self, classifier_list):
        """ Rebuilds a saved classifier as part of the population Reboot """
        numb_attributes = cons.env.format_data.numb_attributes
        att_info = cons.env.format_data.attribute_info
        for att in range(0,numb_attributes):
            if classifier_list[att] != '#':  #Attribute in rule is not wild
                if att_info[att][0]: #Continuous Attribute
                    val_range = classifier_list[att].split(';')
                    self.condition.append(val_range)
                    self.specified_attributes.append(att)
                else:
                    self.condition.append(classifier_list[att])
                    self.specified_attributes.append(att)
        #-------------------------------------------------------
        # DISCRETE PHENOTYPE
        #-------------------------------------------------------
        if cons.env.format_data.discrete_action:
            self.action = str(classifier_list[numb_attributes])
        #-------------------------------------------------------
        # CONTINUOUS PHENOTYPE
        #-------------------------------------------------------
        else:
            self.action = classifier_list[numb_attributes].split(';')
            for i in range(2):
                self.action[i] = float(self.action[i])

        self.prediction = float(classifier_list[numb_attributes+1])
        self.error = float(classifier_list[numb_attributes+2])
        self.fitness = float(classifier_list[numb_attributes+3])
        self.numerosity = int(classifier_list[numb_attributes+4])
        self.ga_count = float(classifier_list[numb_attributes+5])
        self.mean_actionset_sz = float(classifier_list[numb_attributes+6])
        self.ga_timestamp = int(classifier_list[numb_attributes+7])
        self.init_timestamp = int(classifier_list[numb_attributes+8])

        self.delete_vote = float(classifier_list[numb_attributes+10])
        self.action_cnt = int(classifier_list[numb_attributes+11])


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # MATCHING
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def match(self, state):
        """ Returns if the classifier matches in the current situation. """
        for i in range(len(self.condition)):
            att_info = cons.env.format_data.attribute_info[self.specified_attributes[i]]
            #-------------------------------------------------------
            # CONTINUOUS ATTRIBUTE
            #-------------------------------------------------------
            if att_info[0]:
                instance_val = state[self.specified_attributes[i]]
                if self.condition[i][0] < instance_val < self.condition[i][1] or instance_val == cons.label_missing_data:
                    pass
                else:
                    return False
            #-------------------------------------------------------
            # DISCRETE ATTRIBUTE
            #-------------------------------------------------------
            else:
                instance_val = state[self.specified_attributes[i]]
                if instance_val == self.condition[i] or instance_val == cons.label_missing_data:
                    pass
                else:
                    return False
        return True


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # GENETIC ALGORITHM MECHANISMS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def uniformCrossover(self, cl):
        """ Applies uniform crossover and returns if the classifiers changed. Handles both discrete and continuous attributes.
        #SWARTZ: self. is where for the better attributes are more likely to be specified
        #DEVITO: cl. is where less useful attribute are more likely to be specified
        """
        if cons.env.format_data.discrete_action: #Always crossover condition if the phenotype is discrete (if continuous phenotype, half the time phenotype crossover is performed instead)
            self_specified_atts = copy.deepcopy(self.specified_attributes)
            cl_specified_atts = copy.deepcopy(cl.specified_attributes)
            probability = 0.5  #Equal probability for attribute alleles to be exchanged.

            #Make list of attribute references appearing in at least one of the parents.-----------------------------
            combined_atts = []
            for i in self_specified_atts:
                combined_atts.append(i)
            for i in cl_specified_atts:
                if i not in combined_atts:
                    combined_atts.append(i)
                elif not cons.env.format_data.attribute_info[i][0]: #Attribute specified in both parents, and the attribute is discrete (then no reason to cross over)
                    combined_atts.remove(i)
            combined_atts.sort()
            #--------------------------------------------------------------------------------------------------------
            changed = False;
            for att in combined_atts:  #Each condition specifies different attributes, so we need to go through all attributes in the dataset.
                att_info = cons.env.format_data.attribute_info[att]
                #-----------------------------
                ref = 0
                #if att in self.specified_attributes:
                if att in self_specified_atts:
                    ref += 1
                #if att in cl.specified_attributes:
                if att in cl_specified_atts:
                    ref += 1
                #-----------------------------

                if ref == 0:    #Attribute not specified in either condition (Attribute type makes no difference)
                    print("Error: UniformCrossover!")
                    pass

                elif ref == 1:  #Attribute specified in only one condition - do probabilistic switch of whole attribute state (Attribute type makes no difference)
                    if att in self_specified_atts and random.random() > probability:
                        i = self.specified_attributes.index(att) #reference to the position of the attribute in the rule representation
                        cl.condition.append(self.condition.pop(i)) #Take attribute from self and add to cl
                        cl.specified_attributes.append(att)
                        self.specified_attributes.remove(att)
                        changed = True #Remove att from self and add to cl


                    if att in cl_specified_atts and random.random() < probability:
                        i = cl.specified_attributes.index(att) #reference to the position of the attribute in the rule representation
                        self.condition.append(cl.condition.pop(i)) #Take attribute from self and add to cl
                        self.specified_attributes.append(att)
                        cl.specified_attributes.remove(att)
                        changed = True #Remove att from cl and add to self.


                else: #Attribute specified in both conditions - do random crossover between state alleles.  The same attribute may be specified at different positions within either classifier
                    #-------------------------------------------------------
                    # CONTINUOUS ATTRIBUTE
                    #-------------------------------------------------------
                    if att_info[0]:
                        i_cl1 = self.specified_attributes.index(att) #pairs with self (classifier 1)
                        i_cl2 = cl.specified_attributes.index(att)   #pairs with cl (classifier 2)
                        tmp_key = random.randint(0,3) #Make random choice between 4 scenarios, Swap minimums, Swap maximums, Self absorbs cl, or cl absorbs self.
                        if tmp_key == 0:    #Swap minimum
                            temp = self.condition[i_cl1][0]
                            self.condition[i_cl1][0] = cl.condition[i_cl2][0]
                            cl.condition[i_cl2][0] = temp
                        elif tmp_key == 1:  #Swap maximum
                            temp = self.condition[i_cl1][1]
                            self.condition[i_cl1][1] = cl.condition[i_cl2][1]
                            cl.condition[i_cl2][1] = temp
                        else: #absorb range
                            all_list = self.condition[i_cl1] + cl.condition[i_cl2]
                            new_min = min(all_list)
                            new_max = max(all_list)
                            if tmp_key == 2:  #self absorbs cl
                                self.condition[i_cl1] = [new_min,new_max]
                                #Remove cl
                                cl.condition.pop(i_cl2)
                                cl.specified_attributes.remove(att)
                            else: #cl absorbs self
                                cl.condition[i_cl2] = [new_min,new_max]
                                #Remove self
                                self.condition.pop(i_cl1)
                                self.specified_attributes.remove(att)
                    #-------------------------------------------------------
                    # DISCRETE ATTRIBUTE
                    #-------------------------------------------------------
                    else:
                        pass
            tmp_list1 = copy.deepcopy(self_specified_atts)
            tmp_list2 = copy.deepcopy(cl.specified_attributes)
            tmp_list1.sort()
            tmp_list2.sort()
            if changed and (tmp_list1 == tmp_list2):
                changed = False

            if self.action != cl.action and random.random() > probability:
                # Switch phenotypes of 2 classifiers if GA is run in match set
                temp = self.action
                self.action = cl.action
                cl.action = temp
                changed = True
            return changed
        #-------------------------------------------------------
        # CONTINUOUS PHENOTYPE CROSSOVER
        #-------------------------------------------------------
        elif random.random() < 0.5:
            return self.actionCrossover(cl)


    def twoPointCrossover(self, cl):
        """ Applies two point crossover and returns if the classifiers changed. Handles merely discrete attributes and phenotypes """
        points = []
        changed = False
        points.append( int( random.random() * ( cons.env.format_data.numb_attributes + 1 ) ) )
        secondPoint = int( random.random() * ( cons.env.format_data.numb_attributes + 1 ) )
        if points[0] > secondPoint:
            tempPoint = points[0]
            points[0] = secondPoint
            points.append( tempPoint )
        else:
            points.append( secondPoint )
        if cons.env.format_data.discrete_action:
            self_specified_atts = copy.deepcopy(self.specified_attributes)
            cl_specified_atts = copy.deepcopy(cl.specified_attributes)
            for i in range( points[1] ):
                if i >= points[0]:
                    if i in self_specified_atts:
                        if i not in cl_specified_atts:
                            index = self.specified_attributes.index(i)
                            cl.condition.append(self.condition.pop(index))
                            cl.specified_attributes.append(i)
                            self.specified_attributes.remove(i)
                            changed = True #Remove att from self and add to cl
                    elif i in cl_specified_atts:
                        index = cl.specified_attributes.index(i) #reference to the position of the attribute in the rule representation
                        self.condition.append(cl.condition.pop(index)) #Take attribute from self and add to cl
                        self.specified_attributes.append(i)
                        cl.specified_attributes.remove(i)
                        changed = True
        return changed



    def phenotypeCrossover(self, cl):
        """ Crossover a continuous phenotype """
        changed = False
        if self.action[0] == cl.action[0] and self.action[1] == cl.action[1]:
            return changed
        else:
            tmp_key = random.random() < 0.5 #Make random choice between 4 scenarios, Swap minimums, Swap maximums, Children preserve parent phenotypes.
            if tmp_key: #Swap minimum
                temp = self.action[0]
                self.action[0] = cl.action[0]
                cl.action[0] = temp
                changed = True
            elif tmp_key:  #Swap maximum
                temp = self.action[1]
                self.action[1] = cl.action[1]
                cl.action[1] = temp
                changed = True

        return changed


    def Mutation(self, state):
        """ Mutates the condition of the classifier. Also handles phenotype mutation. This is a niche mutation, which means that the resulting classifier will still match the current instance.  """
        changed = False;
        #-------------------------------------------------------
        # MUTATE CONDITION
        #-------------------------------------------------------
        for att in range(cons.env.format_data.numb_attributes):  #Each condition specifies different attributes, so we need to go through all attributes in the dataset.
            att_info = cons.env.format_data.attribute_info[att]
            if random.random() < cons.mu and state[att] != cons.label_missing_data:
                #MUTATION--------------------------------------------------------------------------------------------------------------
                if att not in self.specified_attributes: #Attribute not yet specified
                    self.specified_attributes.append(att)
                    self.condition.append(self.buildMatch(att, state)) #buildMatch handles both discrete and continuous attributes
                    changed = True

                elif att in self.specified_attributes: #Attribute already specified
                    i = self.specified_attributes.index(att) #reference to the position of the attribute in the rule representation
                    #-------------------------------------------------------
                    # DISCRETE OR CONTINUOUS ATTRIBUTE - remove attribute specification with 50% chance if we have continuous attribute, or 100% if discrete attribute.
                    #-------------------------------------------------------
                    if not att_info[0] or random.random() > 0.5:
                        self.specified_attributes.remove(att)
                        self.condition.pop(i) #buildMatch handles both discrete and continuous attributes
                        changed = True
                    #-------------------------------------------------------
                    # CONTINUOUS ATTRIBUTE - (mutate range with 50% probability vs. removing specification of this attribute all together)
                    #-------------------------------------------------------
                    else:
                        #Mutate continuous range - based on Bacardit 2009 - Select one bound with uniform probability and add or subtract a randomly generated offset to bound, of size between 0 and 50% of att domain.
                        attribute_range = float(att_info[1][1]) - float(att_info[1][0])
                        mutate_range = random.random()*0.5*attribute_range
                        if random.random() > 0.5: #Mutate minimum
                            if random.random() > 0.5: #Add
                                self.condition[i][0] += mutate_range
                            else: #Subtract
                                self.condition[i][0] -= mutate_range
                        else: #Mutate maximum
                            if random.random() > 0.5: #Add
                                self.condition[i][1] += mutate_range
                            else: #Subtract
                                self.condition[i][1] -= mutate_range

                        #Repair range - such that min specified first, and max second.
                        self.condition[i].sort()
                        changed = True
                #-------------------------------------------------------
                # NO MUTATION OCCURS
                #-------------------------------------------------------
                else:
                    pass
        #-------------------------------------------------------
        # MUTATE PHENOTYPE
        #-------------------------------------------------------
        if cons.env.format_data.discrete_action:
            nowchanged = self.discreteActionMutation()
        #else:
        #    nowChanged = self.continuousPhenotypeMutation(phenotype)

        if changed or nowchanged:
            return True


    def discreteActionMutation(self):
        """ Mutate this rule's discrete phenotype. """
        changed = False
        if random.random() < cons.mu:
            action_list = copy.deepcopy(cons.env.format_data.action_list)
            action_list.remove(self.action)
            new_action = random.sample(action_list,1)
            self.action = new_action[0]
            changed= True

        return changed


    def continuousPhenotypeMutation(self, phenotype):
        """ Mutate this rule's continuous phenotype. """
        changed = False
        if random.random() < cons.mu: #Mutate continuous phenotype
            action_range = self.action[1] - self.action[0]
            mutation_range = random.random()*0.5*action_range
            tmp_key = random.randint(0,2) #Make random choice between 3 scenarios, mutate minimums, mutate maximums, mutate both
            if tmp_key == 0: #Mutate minimum
                if random.random() > 0.5 or self.action[0] + mutation_range <= phenotype: #Checks that mutated range still contains current phenotype
                    self.action[0] += mutation_range
                else: #Subtract
                    self.action[0] -= mutation_range
                changed = True
            elif tmp_key == 1: #Mutate maximum
                if random.random() > 0.5 or self.action[1] - mutation_range >= phenotype: #Checks that mutated range still contains current phenotype
                    self.action[1] -= mutation_range
                else: #Subtract
                    self.action[1] += mutation_range
                changed = True
            else: #mutate both
                if random.random() > 0.5 or self.action[0] + mutation_range <= phenotype: #Checks that mutated range still contains current phenotype
                    self.action[0] += mutation_range
                else: #Subtract
                    self.action[0] -= mutation_range
                if random.random() > 0.5 or self.action[1] - mutation_range >= phenotype: #Checks that mutated range still contains current phenotype
                    self.action[1] -= mutation_range
                else: #Subtract
                    self.action[1] += mutation_range
                changed = True

            #Repair range - such that min specified first, and max second.
            self.action.sort()
        #---------------------------------------------------------------------
        return changed

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # SUBSUMPTION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def subsumes(self, cl):
        """ Returns if the classifier (self) subsumes cl """
        #-------------------------------------------------------
        # DISCRETE PHENOTYPE
        #-------------------------------------------------------
        if cons.env.format_data.discrete_action:
            if cl.action == self.action:
                if self.isPossibleSubsumer() and self.isMoreGeneral(cl):
                    return True
            return False
        #-------------------------------------------------------
        # CONTINUOUS PHENOTYPE -  NOTE: for continuous phenotypes, the subsumption intuition is reversed, i.e. While a subsuming rule condition is more general, a subsuming phenotype is more specific.
        #-------------------------------------------------------
        else:
            if self.action[0] >= cl.action[0] and self.action[1] <= cl.action[1]:
                if self.isPossibleSubsumer() and self.isMoreGeneral(cl):
                    return True
            return False


    def isPossibleSubsumer(self):
        """ Returns if the classifier (self) is a possible subsumer. A classifier must be as or more accurate than the classifier it is trying to subsume.  """
        if self.action_cnt > cons.theta_sub and self.error < cons.err_sub: #self.prediction < cons.err_sub: (why does it work?)
            return True
        return False


    def isMoreGeneral(self,cl):
        """ Returns if the classifier (self) is more general than cl. Check that all attributes specified in self are also specified in cl. """
        if len(self.specified_attributes) >= len(cl.specified_attributes):# and self.action != cl.action and self.prediction < cl.prediction and self.error > cl.error:
            return False
        for i in range(len(self.specified_attributes)): #Check each attribute specified in self.condition
            att_info = cons.env.format_data.attribute_info[self.specified_attributes[i]]
            if self.specified_attributes[i] not in cl.specified_attributes:
                return False
            #-------------------------------------------------------
            # CONTINUOUS ATTRIBUTE
            #-------------------------------------------------------
            otherRef = cl.specified_attributes.index(self.specified_attributes[i])
            if att_info[0]:
                #If self has a narrower ranger of values than it is a subsumer
                if self.condition[i][0] < cl.condition[otherRef][0]:
                    return False
                if self.condition[i][1] > cl.condition[otherRef][1]:
                    return False
            #else:   # discrete attributes
            #    if self.condition[i] != cl.condition[otherRef]:
            #        return False

        return True

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # DELETION METHOD
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def getDelProb(self, mean_fitness):
        """  Returns the vote for deletion of the classifier. """
        self.delete_vote = self.mean_actionset_sz * self.numerosity
        if self.fitness < cons.delta * mean_fitness * self.numerosity and self.action_cnt > cons.theta_del:
            if self.fitness > 0.0:
                self.delete_vote *= mean_fitness * self.numerosity / self.fitness
            else:
                self.delete_vote *= mean_fitness / (cons.init_fit / self.numerosity)
        return self.delete_vote


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # OTHER METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def buildMatch(self, att, state):
        """ Builds a matching condition for the classifierCovering method. """
        att_info = cons.env.format_data.attribute_info[att]
        #-------------------------------------------------------
        # CONTINUOUS ATTRIBUTE
        #-------------------------------------------------------
        if att_info[0]:
            attribute_range = att_info[1][1] - att_info[1][0]
            range_radius = random.randint(25,75)*0.01*attribute_range / 2.0 #Continuous initialization domain radius.
            low = state[att] - range_radius
            high = state[att] + range_radius
            condition_list = [low,high] #ALKR Representation, Initialization centered around training instance  with a range between 25 and 75% of the domain size.
        #-------------------------------------------------------
        # DISCRETE ATTRIBUTE
        #-------------------------------------------------------
        else:
            condition_list = state[att] #State already formatted like GABIL in DataManagement

        return condition_list


    def equals(self, cl):
        """ Returns if the two classifiers are identical in condition and phenotype. This works for discrete or continuous attributes or phenotypes. """
        if cl.action == self.action and len(cl.specified_attributes) == len(self.specified_attributes): #Is phenotype the same and are the same number of attributes specified - quick equality check first.
            cl_refs = sorted(cl.specified_attributes)
            self_refs = sorted(self.specified_attributes)
            if cl_refs == self_refs:
                for i in range(len(cl.specified_attributes)):
                    tmp_index = self.specified_attributes.index(cl.specified_attributes[i])
                    if cl.condition[i] == self.condition[tmp_index]:
                        pass
                    else:
                        return False
                return True
        return False


    def updateXCSParameters(self, reward): #, maxPrediction):
        """ Update the XCS classifier parameters: prediction payoff, prediction error and fitness. """
        payoff = reward
        if self.action_cnt >= 1.0 / cons.beta:
            self.prediction = self.prediction + cons.beta * ( payoff - self.prediction )
            self.error = self.error + cons.beta * ( math.fabs( payoff - self.prediction ) - self.error )
        else:
            self.prediction = ( self.prediction * ( self.action_cnt - 1 ) + payoff ) / self.action_cnt
            self.error = ( self.error * ( self.action_cnt - 1 ) + math.fabs( payoff - self.prediction ) ) / self.action_cnt
        if self.error <= cons.offset_epsilon:
            self.accuracy = 1
        else:
            self.accuracy = cons.alpha * ( ( cons.offset_epsilon / self.error ) ** cons.nu ) #math.pow( cons.alpha, ( self.error - cons.offset_epsilon ) / cons.offset_epsilon )


    def updateFitness(self):
        if self.action_cnt >= 1.0 / cons.beta:
            self.fitness = self.fitness + cons.beta * ( self.accuracy - self.fitness )
        else:
            self.fitness = ( self.fitness * ( self.action_cnt - 1 ) + self.accuracy ) / self.action_cnt


    def updateActionSetSize(self, actionset_size):
        """  Updates the average action set size. """
        if self.action_cnt >= 1.0 / cons.beta:
            self.mean_actionset_sz = self.mean_actionset_sz + cons.beta * (actionset_size - self.mean_actionset_sz)
        else:
            self.mean_actionset_sz = (self.mean_actionset_sz * (self.action_cnt-1)+ actionset_size) / float(self.action_cnt)


    def resetParams(self):
        """ Reset prediction, error, fitness to default initial data. """
        self.prediction = cons.init_pred    # Classifier payoff - initialized to a constant initial payoff value
        self.error = cons.init_err          # Classifier error - initialized to a constant initial error value
        self.fitness = cons.init_fit        # Classifier fitness - initialized to a constant initial fitness value


    def updateActionExp(self):
        """ Increases the experience of the classifier by one. Once an epoch has completed, rule accuracy can't change."""
        self.action_cnt += 1


    def updateGACount(self):
        """ Increment number of times the classifier is selected in GA by one, for statistics. """
        self.ga_count += 1


    def updateNumerosity(self, num):
        """ Updates the numberosity of the classifier.  Notice that 'num' can be negative! """
        self.numerosity += num


    def updateTimeStamp(self, ts):
        """ Sets the time stamp of the classifier. """
        self.ga_timestamp = ts


    def setPrediction(self,pred):
        """ Sets the accuracy of the classifier """
        self.prediction = pred


    def setError(self,err):
        """ Sets the accuracy of the classifier """
        self.error = err


    def setAccuracy(self,acc):
        """ Sets the accuracy of the classifier """
        self.accuracy = acc


    def setFitness(self, fit):
        """  Sets the fitness of the classifier. """
        self.fitness = fit


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # PRINT CLASSIFIER FOR POPULATION OUTPUT FILE
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def printClassifier(self):
        """ Formats and returns an output string describing this classifier. """
        classifier_info = ""
        for att in range(cons.env.format_data.numb_attributes):
            att_info = cons.env.format_data.attribute_info[att]
            if att in self.specified_attributes:  #If the attribute was specified in the rule
                i = self.specified_attributes.index(att)
                #-------------------------------------------------------
                # CONTINUOUS ATTRIBUTE
                #-------------------------------------------------------
                if att_info[0]:
                    classifier_info += str(self.condition[i][0])+';'+str(self.condition[i][1]) + "\t"
                #-------------------------------------------------------
                # DISCRETE ATTRIBUTE
                #-------------------------------------------------------
                else:
                    classifier_info += str(self.condition[i]) + "\t"
            else: # Attribute is wild.
                classifier_info += '#' + "\t"
        #-------------------------------------------------------------------------------
        specificity = len(self.condition) / float(cons.env.format_data.numb_attributes)

        if cons.env.format_data.discrete_action:
            classifier_info += str(self.action)+"\t"
        else:
            classifier_info += str(self.action[0])+';'+str(self.action[1])+"\t"
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        classifier_info += '{:.1f}'.format(self.prediction)+"\t"+'{:.2f}'.format(self.error)+"\t"+'{:.2f}'.format(self.fitness)+"\t"+str(self.numerosity)+"\t"+str(self.ga_count)+"\t"
        classifier_info += '{:.1f}'.format(self.mean_actionset_sz)+"\t\t"+str(self.ga_timestamp)+"\t\t"+str(self.init_timestamp)+"\t\t"+'{:.2f}'.format(specificity)+"\t\t"
        classifier_info += '{:.1f}'.format(self.delete_vote)+"\t\t"+str(self.action_cnt)+"\n"

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        return classifier_info