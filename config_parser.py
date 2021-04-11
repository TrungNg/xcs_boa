"""
Name:        config_parser.py
Authors:     Bao Trung
Contact:     baotrung@ecs.vuw.ac.nz
Created:     July, 2017
Description:
---------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------------
"""

#Import Required Modules----------
from xcs_constants import *
from boa_constants import *
import os
import copy
#---------------------------------

class ConfigParser:
    def __init__(self, filename):
        self.commentChar = '#'
        self.paramChar =  '='
        self.parameters = self.parseConfig(filename) #Parse the configuration file and get all parameters.
        cons.setConstants(self.parameters) #Store run parameters in the 'Constants' module.
        bcons.setConstants(self.parameters)


    def parseConfig(self, filename):
        """ Parses the configuration file. """
        parameters = {}
        try:
            f = open(filename)
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            print(inst)
            print('cannot open', filename)
            raise
        else:
            for line in f:
                #Remove text after comment character.
                if self.commentChar in line:
                    line, comment = line.split(self.commentChar, 1) #Split on comment character, keep only the text before the character

                #Find lines with parameters (param=something)
                if self.paramChar in line:
                    parameter, value = line.split(self.paramChar, 1) #Split on parameter character
                    parameter = parameter.strip() #Strip spaces
                    value = value.strip()
                    parameters[parameter] = value #Store parameters in a dictionary

            f.close()

        return parameters

