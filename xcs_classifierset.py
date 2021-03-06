"""
Name:        xcs_classifierset.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules---------------------
from boa_algorithm import *
from xcs_constants import *
from xcs_classifier import Classifier
import random
import copy
import sys
from boa_constants import bcons
#--------------------------------------------

class ClassifierSet:
    def __init__(self, a=None):
        """ Overloaded initialization: Handles creation of a new population or a rebooted population (i.e. a previously saved population). """
        # Major Parameters
        self.pop_set = []        # List of classifiers/rules
        self.match_set = []      # List of references to rules in population that match
        self.action_set = []     # List of references to rules in population that match and has action with highest prediction payoff
        self.micro_size = 0   # Tracks the current micro population size, i.e. the population size which takes rule numerosity into account.

        # Evaluation Parameters-------------------------------
        self.ave_generality = 0.0
        self.attribute_spec_list = []
        self.attribute_acc_list = []

        # Set Constructors-------------------------------------
        if a==None:
            self.makePop() #Initialize a new population
        elif isinstance(a,str):
            self.rebootPop(a) #Initialize a population based on an existing saved rule population
        else:
            print("ClassifierSet: Error building population.")

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # POPULATION CONSTRUCTOR METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def makePop(self):
        """ Initializes the rule population """
        self.pop_set = []


    def rebootPop(self, remake_file):
        """ Remakes a previously evolved population from a saved text file. """
        print("Rebooting the following population: " + str(remake_file)+"_RulePop.txt")
        #*******************Initial file handling**********************************************************
        dataset_list = []
        try:
            f = open(remake_file+"_RulePop.txt", 'r')
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', remake_file+"_RulePop.txt")
            raise
        else:
            self.header_list = f.readline().rstrip('\n').split('\t')   #strip off first row
            for line in f:
                lineList = line.strip('\n').split('\t')
                dataset_list.append(lineList)
            f.close()

        #**************************************************************************************************
        for each in dataset_list:
            cl = Classifier(each)
            self.pop_set.append(cl)
            numerosity_ref = cons.env.format_data.numb_attributes + 3
            self.micro_size += int(each[numerosity_ref])
        print("Rebooted Rule Population has "+str(len(self.pop_set))+" Macro Pop Size.")

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # CLASSIFIER SET CONSTRUCTOR METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def makeMatchSet(self, state, iteration):
        """ Constructs a match set from the population. Covering is initiated if the match set is empty or total prediction of rules in match set is too low. """
        #Initial values
        do_covering = True # Covering check: Twofold (1)checks that a match is present, and (2) that total Prediction in Match Set is greater than a threshold compared to mean preadiction.
        #setNumerositySum = 0
        matched_phenotype_list = []
        #totalPrediction = 0.0
        #totalMatchSetPrediction = 0.0
        #-------------------------------------------------------
        # MATCHING
        #-------------------------------------------------------
        cons.timer.startTimeMatching()
        for i in range( len( self.pop_set ) ):           # Go through the population
            cl = self.pop_set[i]                     # One classifier at a time
            #totalPrediction += cl.prediction * cl.numerosity
            if cl.match(state):                     # Check for match
                self.match_set.append( i )             # If match - add classifier to match set
                #setNumerositySum += cl.numerosity   # Increment the set numerosity sum
                if cl.action not in matched_phenotype_list:
                    matched_phenotype_list.append( cl.action )
                #totalMatchSetPrediction += cl.prediction * cl.numerosity
        cons.timer.stopTimeMatching()
        #if totalMatchSetPrediction * self.micro_size >= cons.phi * totalPrediction and totalPrediction > 0:
        if len( matched_phenotype_list ) >= cons.theta_mna:# and ( totalMatchSetPrediction * self.micro_size >= cons.phi * totalPrediction and totalPrediction > 0 ):
            do_covering = False
        #-------------------------------------------------------
        # COVERING
        #-------------------------------------------------------
        while do_covering:
            missing_actions = [a for a in cons.env.format_data.action_list if a not in matched_phenotype_list]
            new_cl = Classifier( iteration, state, random.choice( missing_actions ) )
            self.addClassifierToPopulation( new_cl )
            self.match_set.append( len(self.pop_set)-1 )  # Add covered classifier to match set
            matched_phenotype_list.append( new_cl.action )
            #totalMatchSetPrediction += new_cl.prediction * new_cl.numerosity
            #totalPrediction += new_cl.prediction * new_cl.numerosity
            if len( matched_phenotype_list ) >= cons.theta_mna: # and totalMatchSetPrediction >= cons.phi * totalPrediction / self.micro_size:
                self.deletion()
                self.match_set = []
                do_covering = False


    def makeActionSet(self, chosenPhenotype):
        """ Constructs a correct set out of the given match set. """
        for i in range(len(self.match_set)):
            ref = self.match_set[i]
            #-------------------------------------------------------
            # DISCRETE PHENOTYPE
            #-------------------------------------------------------
            if cons.env.format_data.discrete_action:
                if self.pop_set[ref].action == chosenPhenotype:
                    self.action_set.append(ref)
            #-------------------------------------------------------
            # CONTINUOUS PHENOTYPE
            #-------------------------------------------------------
            else:
                if float(chosenPhenotype) <= float(self.pop_set[ref].action[1]) and float(chosenPhenotype) >= float(self.pop_set[ref].action[0]):
                    self.action_set.append(ref)


    def makeEvalMatchSet(self, state):
        """ Constructs a match set for evaluation purposes which does not activate either covering or deletion. """
        for i in range(len(self.pop_set)):       # Go through the population
            cl = self.pop_set[i]                 # A single classifier
            if cl.match(state):                 # Check for match
                self.match_set.append(i)         # Add classifier to match set


    def makeBOAPopulation(self):
        """ Filter classifiers and convert them for BOA. """
        boa_population = []
        for cl in self.pop_set:
            if cl.action_cnt > bcons.theta_boa and cl.error < bcons.error_boa:# and cl.prediction > bcons.pred_boa:
                #boa_population.append( cl )
                boa_population += [ cl ] * cl.numerosity
        return boa_population


    def makeBOALocalPopulation(self, n):
        """ Select best classifiers in action set and convert them for sampling in BOA. """
        boa_locals = []                   # selected classifiers in action set without repetition by numerosity.
        boa_locals_with_num = []             # selected classifiers from action set with repetition by numerosity.
        if cons.selection_method == "roulette":
            # Set to not count numerosity in the second argument.
            best_locals = self.boaSelectClassifierRW( n, False )
        elif cons.selection_method == "tournament":
            # Set to not count numerosity in the second argument.
            best_locals = self.boaSelectClassifierT( n, False )
        for cl in best_locals:
            boa_locals.append( cl )
            boa_locals_with_num += [ cl ] * cl.numerosity
        return boa_locals, boa_locals_with_num


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # CLASSIFIER DELETION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def deletion(self):
        """ Returns the population size back to the maximum set by the user by deleting rules. """
        cons.timer.startTimeDeletion()
        while self.micro_size > cons.N:
            self.deleteFromPopulation()
        cons.timer.stopTimeDeletion()


    def deleteFromPopulation(self):
        """ Deletes one classifier in the population.  The classifier that will be deleted is chosen by roulette wheel selection
        considering the deletion vote. Returns the macro-classifier which got decreased by one micro-classifier. """
        mean_fitness = self.getPopFitnessSum()/float(self.micro_size)

        #Calculate total wheel size------------------------------
        sum_cl = 0.0
        vote_list = []
        for cl in self.pop_set:
            vote = cl.getDelProb(mean_fitness)
            sum_cl += vote
            vote_list.append(vote)
        #--------------------------------------------------------
        choice_point = sum_cl * random.random() #Determine the choice point

        new_sum=0.0
        for i in range(len(vote_list)):
            cl = self.pop_set[i]
            new_sum = new_sum + vote_list[i]
            if new_sum > choice_point: #Select classifier for deletion
                #Delete classifier----------------------------------
                cl.updateNumerosity(-1)
                self.micro_size -= 1
                if cl.numerosity < 1: # When all micro-classifiers for a given classifier have been depleted.
                    self.removeMacroClassifier(i)
                    self.deleteFromMatchSet(i)
                    self.deleteFromActionSet(i)
                return

        print("ClassifierSet: No eligible rules found for deletion in deleteFromPopulation.")
        return


    def removeMacroClassifier(self, ref):
        """ Removes the specified (macro-) classifier from the population. """
        self.pop_set.pop(ref)


    def deleteFromMatchSet(self, del_ref):
        """ Delete reference to classifier in population, contained in self.match_set."""
        if del_ref in self.match_set:
            self.match_set.remove(del_ref)

        #Update match set reference list--------
        for j in range(len(self.match_set)):
            ref = self.match_set[j]
            if ref > del_ref:
                self.match_set[j] -= 1


    def deleteFromActionSet(self, del_ref):
        """ Delete reference to classifier in population, contained in self.action_set."""
        if del_ref in self.action_set:
            self.action_set.remove(del_ref)

        #Update match set reference list--------
        for j in range(len(self.action_set)):
            ref = self.action_set[j]
            if ref > del_ref:
                self.action_set[j] -= 1


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # GENETIC ALGORITHM
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def runGA(self, explore_iter, state):
        """ The genetic discovery mechanism in XCS is controlled here. """
        #-------------------------------------------------------
        # GA RUN REQUIREMENT
        #-------------------------------------------------------
        if (explore_iter - self.getIterStampAverage()) < cons.theta_GA:  #Does the action set meet the requirements for activating the GA?
            return

        self.setIterStamps(explore_iter) #Updates the iteration time stamp for all rules in the match set (which the GA opperates in).
        changed = False

        #-------------------------------------------------------
        # SELECT PARENTS - Niche GA - selects parents from the match set
        #-------------------------------------------------------
        cons.timer.startTimeSelection()
        if cons.selection_method == "roulette":
            select_cls = self.gaSelectClassifierRW()
        elif cons.selection_method == "tournament":
            select_cls = self.gaSelectClassifierT()
        else:
            print("ClassifierSet: Error - requested GA selection method not available.")
        clP1 = select_cls[0]
        if len(select_cls) > 1:
            clP2 = select_cls[1]
        else:
            clP2 = select_cls[0]
        cons.timer.stopTimeSelection()
        clP1.updateGACount()
        clP2.updateGACount()
        #-------------------------------------------------------
        # INITIALIZE OFFSPRING
        #-------------------------------------------------------
        cl1  = Classifier(clP1, explore_iter)
        if clP2 == None:
            cl2 = Classifier(clP1, explore_iter)
        else:
            cl2 = Classifier(clP2, explore_iter)

        #-------------------------------------------------------
        # CROSSOVER OPERATOR - Uniform Crossover Implemented (i.e. all attributes have equal probability of crossing over between two parents)
        #-------------------------------------------------------
        if not cl1.equals(cl2) and random.random() < cons.chi:
            if cons.crossover_method == 'uniform':
                changed = cl1.uniformCrossover(cl2)
            elif cons.crossover_method == 'twopoint':
                changed = cl1.twoPointCrossover(cl2)

        #-------------------------------------------------------
        # INITIALIZE KEY OFFSPRING PARAMETERS
        #-------------------------------------------------------
        if changed:
            cl1.setPrediction((cl1.prediction + cl2.prediction)/2)
            cl1.setError((cl1.error + cl2.error)/2.0)
            cl1.setFitness(cons.fitness_reduction * (cl1.fitness + cl2.fitness)/2.0)
            cl2.setPrediction(cl1.prediction)
            cl2.setError(cl1.error)
            cl2.setFitness(cl1.fitness)

        cl1.setFitness(cons.fitness_reduction * cl1.fitness)
        cl2.setFitness(cons.fitness_reduction * cl2.fitness)
        #-------------------------------------------------------
        # MUTATION OPERATOR
        #-------------------------------------------------------
        nowchanged = cl1.Mutation(state)
        howaboutnow = cl2.Mutation(state)
        #-------------------------------------------------------
        # ADD OFFSPRING TO POPULATION
        #-------------------------------------------------------
        if changed or nowchanged or howaboutnow:
            self.insertDiscoveredClassifiers(cl1, cl2, clP1, clP2) #Subsumption
        self.deletion()


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # SELECTION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def gaSelectClassifierRW(self):
        """ Selects parents for GA using roulette wheel selection according to the fitness of the classifiers. """
        #Prepare for actionSet set or 'niche' selection.
        set_list = copy.deepcopy(self.action_set)

        if len(set_list) > 2:
            select_cls = [None, None]
            count = 0 #Pick two parents
            #-----------------------------------------------
            while count < 2:
                fitness_sum = self.getFitnessSum(set_list)

                choice_p = random.random() * fitness_sum
                i=0
                sum_cl = self.pop_set[set_list[i]].fitness
                while choice_p > sum_cl:
                    i=i+1
                    sum_cl += self.pop_set[set_list[i]].fitness

                select_cls[count] = self.pop_set[set_list[i]]
                set_list.remove(set_list[i])
                count += 1
            #-----------------------------------------------
        elif len(set_list) == 2:
            select_cls = [self.pop_set[set_list[0]],self.pop_set[set_list[1]]]
        elif len(set_list) == 1:
            select_cls = [self.pop_set[set_list[0]],self.pop_set[set_list[0]]]
        else:
            print("ClassifierSet: Error in parent selection.")

        return select_cls


    def gaSelectClassifierT(self):
        """  Selects parents for GA using tournament selection according to the fitness of the classifiers. """
        select_cls = [None, None]
        count = 0
        set_list = self.action_set #actionSet set is a list of reference IDs

        while count < 2:
            tournament_size = int(len(set_list)*cons.theta_sel)
            tournament_list = random.sample(set_list, tournament_size)

            best_fitness = 0
            best_cl = self.action_set[0]
            for j in tournament_list:
                if self.pop_set[j].fitness > best_fitness:
                    best_fitness = self.pop_set[j].fitness
                    best_cl = j

            select_cls[count] = self.pop_set[best_cl]
            count += 1

        return select_cls


    def boaSelectClassifierRW(self, n, is_numerosity_counted=True):
        """ Selects parents using roulette wheel selection according to the fitness of the classifiers. """
        #Prepare for actionSet set or 'niche' selection.
        set_list = copy.deepcopy( self.action_set )
        select_list = []
        count = 0
        #-----------------------------------------------
        while count < n and len( set_list ) > 0:
            fitness_sum = self.getFitnessSum( set_list )

            choice_p = random.random() * fitness_sum
            i=0
            sum_cl = self.pop_set[ set_list[i] ].fitness
            while choice_p > sum_cl:
                i=i+1
                sum_cl += self.pop_set[ set_list[i] ].fitness

            if is_numerosity_counted:
#                 if self.pop_set[ set_list[i] ].numerosity <= n - len( select_list ):
#                     number_of_copies = self.pop_set[ set_list[i] ].numerosity
#                 else:
#                     number_of_copies = n - len( select_list )
                select_list.append( self.pop_set[ set_list[i] ] )
                count += self.pop_set[ set_list[i] ].numerosity
            else:
                select_list.append( self.pop_set[ set_list[i] ] )
                count += 1
            set_list.pop( i )
        if len( select_list ) == 1:
            select_list.append( select_list[0] )
        #-----------------------------------------------

        return select_list


    def boaSelectClassifierT(self, n, is_numerosity_counted=True):
        """  Selects parents using tournament selection according to the fitness of the classifiers. """
        select_list = []
        count = 0
        set_list = copy.deepcopy( self.action_set ) #actionSet set is a list of reference IDs

        while count < n and ( int( len( set_list ) * cons.theta_sel ) > 0 ):
            tournament_list = random.sample( set_list, int( len( set_list ) * cons.theta_sel ) )

            best_fitness = 0
            best_cl = self.action_set[0]
            for j in tournament_list:
                if self.pop_set[j].fitness > best_fitness:
                    best_fitness = self.pop_set[j].fitness
                    best_cl = j

            if is_numerosity_counted:
#                 if self.pop_set[ best_cl ].numerosity <= n - len( select_list ):
#                     number_of_copies = self.pop_set[ best_cl ].numerosity
#                 else:
#                     number_of_copies = n - len( select_list )
                select_list.append( self.pop_set[ best_cl ] )
                count += self.pop_set[ best_cl ].numerosity
            else:
                select_list.append( self.pop_set[ best_cl ] )
                count += 1
            set_list.remove( best_cl )
        if len( select_list ) == 1:
            select_list.append( select_list[0] )

        return select_list


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # SUBSUMPTION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def subsumeClassifier(self, cl=None, cl1P=None, cl2P=None):
        """ Tries to subsume a classifier in the parents. If no subsumption is possible it tries to subsume it in the current set. """
        if cl1P!=None and cl1P.subsumes(cl):
            self.micro_size += 1
            cl1P.updateNumerosity(1)
        elif cl2P!=None and cl2P.subsumes(cl):
            self.micro_size += 1
            cl2P.updateNumerosity(1)
        else:
            #self.addClassifierToPopulation(cl)
            self.subsumeClassifier2(cl); #Try to subsume in the match set.


    def subsumeClassifier2(self, cl):
        """ Tries to subsume a classifier in the match set. If no subsumption is possible the classifier is simply added to the population considering
        the possibility that there exists an identical classifier. """
        choices = []
        for ref in self.match_set:
            if self.pop_set[ref].subsumes(cl):
                choices.append(ref)

        if len(choices) > 0: #Randomly pick one classifier to be subsumer
            choice = int(random.random()*len(choices))
            self.pop_set[choices[choice]].updateNumerosity(1)
            self.micro_size += 1
            return

        self.addClassifierToPopulation(cl) #If no subsumer was found, check for identical classifier, if not then add the classifier to the population


    def doActionSetSubsumption(self):
        """ Executes match set subsumption.  The match set subsumption looks for the most general subsumer classifier in the match set
        and subsumes all classifiers that are more specific than the selected one. """
        subsumer = None
        for ref in self.action_set:
            cl = self.pop_set[ref]
            if cl.isPossibleSubsumer():
                if subsumer == None or len( subsumer.specified_attributes ) > len( cl.specified_attributes ) or ( ( len(subsumer.specified_attributes ) == len(cl.specified_attributes) and random.random() < 0.5 ) ):
                    subsumer = cl

        if subsumer != None: #If a subsumer was found, subsume all more specific classifiers in the match set
            i=0
            while i < len(self.action_set):
                ref = self.action_set[i]
                if subsumer.isMoreGeneral(self.pop_set[ref]):
                    subsumer.updateNumerosity(self.pop_set[ref].numerosity)
                    self.removeMacroClassifier(ref)
                    self.deleteFromMatchSet(ref)
                    self.deleteFromActionSet(ref)
                    i = i - 1
                i = i + 1


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # OTHER KEY METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def addClassifierToPopulation(self, cl, covering = False):
        """ Adds a classifier to the set and increases the microPopSize value accordingly."""
        oldCl = None
        if not covering:
            oldCl = self.getIdenticalClassifier(cl)
        if oldCl != None: #found identical classifier
            oldCl.updateNumerosity(1)
        else:
            self.pop_set.append(cl)
        self.micro_size += 1


    def insertDiscoveredClassifiers(self, cl1, cl2, clP1, clP2):
        """ Inserts both discovered classifiers and activates GA subsumption if turned on. Also checks for default rule (i.e. rule with completely general condition) and
        prevents such rules from being added to the population, as it offers no predictive value within XCS. """
        #-------------------------------------------------------
        # SUBSUMPTION
        #-------------------------------------------------------
        if cons.do_ga_subsumption:
            cons.timer.startTimeSubsumption()

            if len(cl1.specified_attributes) > 0:
                self.subsumeClassifier(cl1, clP1, clP2)
            if len(cl2.specified_attributes) > 0:
                self.subsumeClassifier(cl2, clP1, clP2)

            cons.timer.stopTimeSubsumption()
        #-------------------------------------------------------
        # ADD OFFSPRING TO POPULATION
        #-------------------------------------------------------
        else: #Just add the new classifiers to the population.
            if len(cl1.specified_attributes) > 0:
                self.addClassifierToPopulation(cl1) #False passed because this is not called for a covered rule.
            if len(cl2.specified_attributes) > 0:
                self.addClassifierToPopulation(cl2) #False passed because this is not called for a covered rule.


    def updateSets(self, reward): #, maxPrediction):
        """ Updates all relevant parameters in the current match and match sets. """
        actionSetNumerosity = 0
        for ref in self.action_set:
            actionSetNumerosity += self.pop_set[ref].numerosity
        accuracySum = 0.0
        for ref in self.action_set:
            #self.pop_set[ref].updateExperience()
            #self.pop_set[ref].updateMatchSetSize(matchSetNumerosity)
            #if ref in self.action_set:
            self.pop_set[ref].updateActionExp()
            self.pop_set[ref].updateActionSetSize( actionSetNumerosity )
            self.pop_set[ref].updateXCSParameters( reward ) #, maxPrediction )
            accuracySum += self.pop_set[ref].accuracy * self.pop_set[ref].numerosity
        for ref in self.action_set:
            self.pop_set[ref].setAccuracy( 1000 * self.pop_set[ref].accuracy * self.pop_set[ref].numerosity / accuracySum )
            self.pop_set[ref].updateFitness()


    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # OTHER METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def samplingOffspring(self, boa, state, explore_iter):
        """ Generate offsprings for XCS. """
        ###---Does the action set meet the requirements for activating the GA?---###
        if ( explore_iter - self.getIterStampAverage() ) < cons.theta_GA:
            return True

        select_size = max ( bcons.A, 2 )
        ###------Choose bcon.A local classifiers in filled list format------###
        best_locals, best_locals_with_num = self.makeBOALocalPopulation( select_size )
        #if len( best_locals ) < bcons.A:
            ###......No sampling is done, GA will be executed......###
        #    return False
        self.setIterStamps( explore_iter ) #Updates the iteration time stamp for all rules in the match set (which the GA opperates in).

        boa_offspring = []
        ###------Encode the filled list of local classifiers into the format that BOA can read and process-----###
        encoded_locals = boa.converter.encodePop( best_locals )
        if bcons.A > 0:
            encoded_locals_with_num = boa.converter.encodePop( best_locals_with_num )
            ###------------Assign local parameters to the global model----------###
            for graph in boa.bn.decision_graphs:
                graph.countFrequencies( encoded_locals_with_num )
        length_boa_classifier = len( encoded_locals[ 0 ] )

        ###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### GENERATE OFFSPRINGS by BOA
        ###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        for i in range( 2 ):
            old_likelihood = boa.bn.getInstanceLikelihood( encoded_locals[ i ] )         # Get likelihood of a parent classifier.
            for _ in range( bcons.B ):
                perturbed_index = int( random.random() * length_boa_classifier )            # Select variable (bit) to be perturbed.
                ###------------Copy parent classifier to make changes-----------###
                new_boa_encoded_cl = copy.deepcopy( encoded_locals[ i ] )
                ###-------Perturb the variable and compute new likelihood-------###
                boa.converter.flipValue( new_boa_encoded_cl, perturbed_index )   # Randomly flip value at perturbed_index.
                new_likelihood = boa.bn.getInstanceLikelihood( new_boa_encoded_cl )
                ###----Apply the change with probability corresponding to ratio between new likelihood and old likelihood----###
                if random.random() < new_likelihood / ( new_likelihood + old_likelihood ):
                    encoded_locals[ i ] = new_boa_encoded_cl
                    old_likelihood = new_likelihood
            ###------If no perturbation allowed, generate boa_offspring directly from the global model-----###
            if bcons.B == 0:
                boa_offspring.append( boa.bn.generateInstance( 1 )[ 0 ] )
            ###------Or use the new offsprings generated by perturbation (allowed)------###
            else:
                boa_offspring.append( encoded_locals[ i ] )

        ###--------Add new offsprings to population of classifiers---------###
        offspring = []
        for i in range( 2 ):
            offspring.append( Classifier( best_locals[ i ], explore_iter ) )
            boa.converter.decode( boa_offspring[ i ], offspring[ i ] )                # Convert classifiers to XCS format.
            if bcons.B == 0:
                offspring[ i ].resetParams()
            else:
                offspring[ i ].setFitness( cons.fitness_reduction * offspring[ i ].fitness )
            offspring[ i ].Mutation( state )
            #self.addClassifierToPopulation( offspring[ i ] )
        self.insertDiscoveredClassifiers( offspring[ 0 ], offspring[ 1 ], best_locals[ 0 ], best_locals[ 1 ] )
        self.deletion()
        return True


    def getIterStampAverage(self):
        """ Returns the average of the time stamps in the match set. """
        sum_cl=0.0
        sum_numer=0.0
        for i in range(len(self.action_set)):
            ref = self.action_set[i]
            sum_cl += self.pop_set[ref].ga_timestamp * self.pop_set[ref].numerosity
            sum_numer += self.pop_set[ref].numerosity #numerosity sum of match set
        return sum_cl/float(sum_numer)


    def setIterStamps(self, explore_iter):
        """ Sets the time stamp of all classifiers in the set to the current time. The current time
        is the number of exploration steps executed so far.  """
        for i in range(len(self.action_set)):
            ref = self.action_set[i]
            self.pop_set[ref].updateTimeStamp(explore_iter)


    def getFitnessSum(self, set_list):
        """ Returns the sum of the fitnesses of all classifiers in the set. """
        sum_cl=0.0
        for i in range(len(set_list)):
            ref = set_list[i]
            sum_cl += self.pop_set[ref].fitness
        return sum_cl


    def getPopFitnessSum(self):
        """ Returns the sum of the fitnesses of all classifiers in the set. """
        sum_cl = 0.0
        for cl in self.pop_set:
            sum_cl += cl.fitness
        return sum_cl


    def getIdenticalClassifier(self, new_cl):
        """ Looks for an identical classifier in the population. """
        for ref in self.match_set:
            if new_cl.equals(self.pop_set[ref]):
                return self.pop_set[ref]
        return None


    def clearSets(self):
        """ Clears out references in the match and action sets for the next learning iteration. """
        self.match_set = []
        self.action_set = []

    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # EVALUTATION METHODS
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def runPopAveEval(self):
        """ Calculates some summary evaluations across the rule population including average generality. """
        gen_sum = 0
        #agedCount = 0
        for cl in self.pop_set:
            gen_sum += (cons.env.format_data.numb_attributes - len(cl.condition)) * cl.numerosity
        if self.micro_size == 0:
            self.ave_generality = 'NA'
        else:
            self.ave_generality = gen_sum / float(self.micro_size * cons.env.format_data.numb_attributes)


    def runAttGeneralitySum(self, is_evaluation_summary):
        """ Determine the population-wide frequency of attribute specification, and accuracy weighted specification.  Used in complete rule population evaluations. """
        if is_evaluation_summary:
            self.attribute_spec_list = []
            self.attribute_acc_list = []
            for _ in range(cons.env.format_data.numb_attributes):
                self.attribute_spec_list.append(0)
                self.attribute_acc_list.append(0.0)
            for cl in self.pop_set:
                for ref in cl.specified_attributes: #for each attRef
                    self.attribute_spec_list[ref] += cl.numerosity
                    self.attribute_acc_list[ref] += cl.numerosity * cl.accuracy


    def getPopTrack(self, accuracy, iteration, tracking_frequency):
        """ Returns a formated output string to be printed to the Learn Track output file. """
        track_string = str(iteration)+ "\t" + str(len(self.pop_set)) + "\t" + str(self.micro_size) + "\t" + str(accuracy) + "\t" + str(self.ave_generality)  + "\t" + str(cons.timer.returnGlobalTimer())+ "\n"
        if cons.env.format_data.discrete_action: #discrete phenotype
            print(("Epoch: "+str(int(iteration/tracking_frequency))+"\t Iteration: " + str(iteration) + "\t MacroPop: " + str(len(self.pop_set))+ "\t MicroPop: " + str(self.micro_size) + "\t AccEstimate: " + str(accuracy) + "\t AveGen: " + str(self.ave_generality)  + "\t Time: " + str(cons.timer.returnGlobalTimer())))
        else: # continuous phenotype
            print(("Epoch: "+str(int(iteration/tracking_frequency))+"\t Iteration: " + str(iteration) + "\t MacroPop: " + str(len(self.pop_set))+ "\t MicroPop: " + str(self.micro_size) + "\t AccEstimate: " + str(accuracy) + "\t AveGen: " + str(self.ave_generality) + "\t PhenRange: " +str(self.ave_phenotype_range) + "\t Time: " + str(cons.timer.returnGlobalTimer())))

        return track_string


