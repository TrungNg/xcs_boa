'''
Name: data_generator.py
Author: Bao-Trung Nguyen
Created: July 13, 2017
Description:  Module for generating datasets.
'''
import random



def generate_parity_countone_data(myfile, numb_parity,numb_countone, instances):
    """ """
    fp=open(myfile,"w")
    #Make File Header
    for i in range(numb_parity*numb_countone):
        fp.write('B_'+str(i)+"\t")
    fp.write("Class" + "\n") #State found at Register Bit

    for i in range(instances):
        state_phenotype = generate_parity_countone_instance(numb_parity,numb_countone)
        for j in state_phenotype[0]:
            fp.write(str(j)+"\t")
        fp.write(str(state_phenotype[1])+ "\n")


def generate_parity_countone_instance(numb_parity,numb_countone):
    """ """
    condition = []
    #Generate random boolean string
    for _ in range(numb_parity*numb_countone):
        condition.append(str(random.randint(0,1)))

    counts=[]
    for j in range(numb_countone):
        counts.append(0)
        for k in range(numb_parity):
            if condition[j*numb_parity + k] == '1':
                counts[j]+=1
        if counts[j]%2 == 0:
            counts[j]=0
        else:
            counts[j]=1

    if sum(counts) > numb_countone/2:
        output='1'
    else:
        output='0'

    return [condition,output]


def generate_complete_parity_countone(myfile,numb_parity,numb_countone):
    length=numb_parity*numb_countone
    try:
        fp=open(myfile,"w")
        #Make File Header
        for i in range(length):
            fp.write('B_'+str(i)+"\t")
        fp.write("Class" + "\n") #State found at Register Bit

        for i in range(2**length):
            binary_str=bin(i)
            string_array=binary_str.split('b')
            binary=string_array[1]

            while len(binary)<length:
                binary="0" + binary

            counts=[]
            for j in range(numb_countone):
                counts.append(0)
                for k in range(numb_parity):
                    if binary[j*numb_parity + k] == '1':
                        counts[j]+=1
                if counts[j]%2 == 0:
                    counts[j]=0
                else:
                    counts[j]=1

            if sum(counts) > numb_countone/2:
                output='1'
            else:
                output='0'

            #fp.write(str(i)+"\t")
            for j in binary:
                fp.write(j+ "\t")
            fp.write(output+ "\n")

    except:
        print("Data set generation: ERROR - Cannot generate all data instances due to computational limitations")


#generate_complete_parity_countone('Demo_Datasets/3Parity_5CountOne_Data_Complete.txt',3,5)
#generate_parity_countone_data('Demo_Datasets/3Parity_5CountOne_Data_20000.txt',3,5,20000)


'''
Name: problem_multiplexer.py
Author: Gediminas Bertasius and Ryan Urbanowicz
Created: June 13, 2013
Description:
Additional Notes:
        Address Bits = 1 (3-Multiplexer)
        Address Bits = 2 (6-Multiplexer)
        Address Bits = 3 (11-Multiplexer)
        Address Bits = 4 (20-Multiplexer)
        Address Bits = 5 (37-Multiplexer)
        Address Bits = 6 (70-Multiplexer)
        Address Bits = 7 (135-Multiplexer)
        Address Bits = 8 (264-Multiplexer)
'''
import random

def generate_mulitplexer_data(myfile, num_bits, instances):
    """ """
    print("Problem_Multiplexer: Generate multiplexer dataset with "+str(instances)+" instances.")
    first=solve_equation(num_bits)
    if first==None:
        print("Problem_Multiplexer: ERROR - The multiplexer takes # of bits as 3,6,11,20,37,70,135,264")

    else:
        fp=open(myfile,"w")
        #Make File Header
        for i in range(first):
            fp.write('A_'+str(i)+"\t") #Address Bits

        for i in range(num_bits-first):
            fp.write('R_'+str(i)+"\t") #Register Bits
        fp.write("Class" + "\n") #State found at Register Bit

        for i in range(instances):
            state_phenotype = generate_multiplexer_instance(num_bits)
            for j in state_phenotype[0]:
                fp.write(str(j)+"\t")
            fp.write(str(state_phenotype[1])+ "\n")


def generate_multiplexer_instance(num_bits):
    """ """
    first=solve_equation(num_bits)
    if first==None:
        print("Problem_Multiplexer: ERROR - The multiplexer takes # of bits as 3,6,11,20,37,70,135,264")

    else:
        condition = []
        #Generate random boolean string
        for i in range(num_bits):
            condition.append(str(random.randint(0,1)))

        gates=""

        for j in range(first):
            gates+=condition[j]

        gates_decimal=int(gates,2)
        output=condition[first+gates_decimal]

        return [condition,output]



def generate_complete_multiplexer_data(myfile,num_bits):
    """ Attempts to generate a complete non-redundant multiplexer dataset.  Ability to generate the entire dataset is computationally limited.
     We had success generating up to the complete 20-multiplexer dataset"""

    print("Problem_Multiplexer: Attempting to generate multiplexer dataset")
    first=solve_equation(num_bits)

    if first==None:
        print("Problem_Multiplexer: ERROR - The multiplexer takes # of bits as 3,6,11,20,37,70,135,264")
    else:
        try:
            fp=open(myfile,"w")
            #Make File Header
            for i in range(first):
                fp.write('A_'+str(i)+"\t") #Address Bits

            for i in range(num_bits-first):
                fp.write('R_'+str(i)+"\t") #Register Bits
            fp.write("Class" + "\n") #State found at Register Bit


            for i in range(2**num_bits):
                binary_str=bin(i)
                string_array=binary_str.split('b')
                binary=string_array[1]

                while len(binary)<num_bits:
                    binary="0" + binary

                gates=""
                for j in range(first):
                    gates+=binary[j]

                gates_decimal=int(gates,2)
                output=binary[first+gates_decimal]

                #fp.write(str(i)+"\t")
                for j in binary:
                    fp.write(j+ "\t")
                fp.write(output+ "\n")

            fp.close()
            print("Problem_Multiplexer: Dataset Generation Complete")

        except:
            print("Problem_Multiplexer: ERROR - Cannot generate all data instances for specified multiplexer due to computational limitations")


def solve_equation(num_bits):
    for i in range(1000):
        if i+2**i==num_bits:
            return i
        if i+2**i > num_bits:
            break
    return None

#generate_multiplexer_instance(37)
#generate_mulitplexer_data("20Multiplexer_Data_2000.txt", 20, 2000)
#generate_complete_multiplexer_data("20Multiplexer_Complete_Data.txt",6)  #3,6,11,20, 37
