#!/usr/bin/env ruby
# Phillip Thompkins (phith1@umbc.edu)
# CMSC478 Fall 2014
# Final Project - Information Gain Calculator
# Takes in a file and calcs the IG for each variable

from math import log
import sys
import operator

# checks for valid number of command line args
if len(sys.argv) != 2:
  print "Improper number of command line args."

TOTAL_PEOPLE = 37424.0
AMI_YES = 1835.0
AMI_NO = 35589.0
AMI_ENTROPY = 0 - ((AMI_YES / TOTAL_PEOPLE) * log((AMI_YES / TOTAL_PEOPLE),2)) - ((AMI_NO / TOTAL_PEOPLE) * log((AMI_NO / TOTAL_PEOPLE),2))
SMI_YES = 554.0
SMI_NO = 36870.0
SMI_ENTROPY = 0 - ((SMI_YES / TOTAL_PEOPLE) * log((SMI_YES / TOTAL_PEOPLE),2)) - ((SMI_NO / TOTAL_PEOPLE) * log((SMI_NO / TOTAL_PEOPLE),2))

# we need something to hold our variables and their i-gain
# let's use a hash table!
variables = {}

# command line should be 1) location of file
# first, we open up the file and analyze it, using open-uri
with open(str(sys.argv[1]), "r") as theFile:
	for line in theFile:
		vars = line.split(',')
		# if standard yes/no question...
		varName = vars[0]
		ya = 0.0
		na = 0.0
		
		if len(vars) == 5:
			ya -= ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2)) 
			ya -= ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			na -= ((float(vars[3]) / SMI_NO) * log((float(vars[3]) / SMI_NO),2))
			na -= ((float(vars[4]) / SMI_NO) * log((float(vars[4]) / SMI_NO),2))

		# if not a yes/no question...
		if len(vars) == 7:
			ya -= 0 - ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2))
			ya -= 0 - ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			ya -= 0 - ((float(vars[3]) / SMI_YES) * log((float(vars[3]) / SMI_YES),2))
			na -= 0 - ((float(vars[4]) / SMI_NO) * log((float(vars[4]) / SMI_NO),2))
			na -= 0 - ((float(vars[5]) / SMI_NO) * log((float(vars[5]) / SMI_NO),2))
			na -= 0 - ((float(vars[6]) / SMI_NO) * log((float(vars[6]) / SMI_NO),2))

		if len(vars) == 9:
			ya -= 0 - ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2))
			ya -= 0 - ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			ya -= 0 - ((float(vars[3]) / SMI_YES) * log((float(vars[3]) / SMI_YES),2))
			ya -= 0 - ((float(vars[4]) / SMI_YES) * log((float(vars[4]) / SMI_YES),2))
			na -= 0 - ((float(vars[5]) / SMI_NO) * log((float(vars[5]) / SMI_NO),2))
			na -= 0 - ((float(vars[6]) / SMI_NO) * log((float(vars[6]) / SMI_NO),2))
			na -= 0 - ((float(vars[7]) / SMI_NO) * log((float(vars[7]) / SMI_NO),2))
			na -= 0 - ((float(vars[8]) / SMI_NO) * log((float(vars[8]) / SMI_NO),2))
	
		if len(vars) == 11:
			ya -= 0 - ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2))
			ya -= 0 - ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			ya -= 0 - ((float(vars[3]) / SMI_YES) * log((float(vars[3]) / SMI_YES),2))
			ya -= 0 - ((float(vars[4]) / SMI_YES) * log((float(vars[4]) / SMI_YES),2))
			ya -= 0 - ((float(vars[5]) / SMI_YES) * log((float(vars[5]) / SMI_YES),2))
			na -= 0 - ((float(vars[6]) / SMI_NO) * log((float(vars[6]) / SMI_NO),2))
			na -= 0 - ((float(vars[7]) / SMI_NO) * log((float(vars[7]) / SMI_NO),2))
			na -= 0 - ((float(vars[8]) / SMI_NO) * log((float(vars[8]) / SMI_NO),2))
			na -= 0 - ((float(vars[9]) / SMI_NO) * log((float(vars[9]) / SMI_NO),2))
			na -= 0 - ((float(vars[10]) / SMI_NO) * log((float(vars[10]) / SMI_NO),2))

		if len(vars) == 15:
			ya -= 0 - ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2))
			ya -= 0 - ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			ya -= 0 - ((float(vars[3]) / SMI_YES) * log((float(vars[3]) / SMI_YES),2))
			ya -= 0 - ((float(vars[4]) / SMI_YES) * log((float(vars[4]) / SMI_YES),2))
			ya -= 0 - ((float(vars[5]) / SMI_YES) * log((float(vars[5]) / SMI_YES),2))
			ya -= 0 - ((float(vars[6]) / SMI_YES) * log((float(vars[6]) / SMI_YES),2))
			ya -= 0 - ((float(vars[7]) / SMI_YES) * log((float(vars[7]) / SMI_YES),2))
			na -= 0 - ((float(vars[8]) / SMI_NO) * log((float(vars[8]) / SMI_NO),2))
			na -= 0 - ((float(vars[9]) / SMI_NO) * log((float(vars[9]) / SMI_NO),2))
			na -= 0 - ((float(vars[10]) / SMI_NO) * log((float(vars[10]) / SMI_NO),2))
			na -= 0 - ((float(vars[11]) / SMI_NO) * log((float(vars[11]) / SMI_NO),2))
			na -= 0 - ((float(vars[12]) / SMI_NO) * log((float(vars[12]) / SMI_NO),2))
			na -= 0 - ((float(vars[13]) / SMI_NO) * log((float(vars[13]) / SMI_NO),2))
			na -= 0 - ((float(vars[14]) / SMI_NO) * log((float(vars[14]) / SMI_NO),2))

		if len(vars) == 23:
			ya -= 0 - ((float(vars[1]) / SMI_YES) * log((float(vars[1]) / SMI_YES),2))
			ya -= 0 - ((float(vars[2]) / SMI_YES) * log((float(vars[2]) / SMI_YES),2))
			ya -= 0 - ((float(vars[3]) / SMI_YES) * log((float(vars[3]) / SMI_YES),2))
			ya -= 0 - ((float(vars[4]) / SMI_YES) * log((float(vars[4]) / SMI_YES),2))
			ya -= 0 - ((float(vars[5]) / SMI_YES) * log((float(vars[5]) / SMI_YES),2))
			ya -= 0 - ((float(vars[6]) / SMI_YES) * log((float(vars[6]) / SMI_YES),2))
			ya -= 0 - ((float(vars[7]) / SMI_YES) * log((float(vars[7]) / SMI_YES),2))
			ya -= 0 - ((float(vars[8]) / SMI_YES) * log((float(vars[8]) / SMI_YES),2))
			ya -= 0 - ((float(vars[9]) / SMI_YES) * log((float(vars[9]) / SMI_YES),2))
			ya -= 0 - ((float(vars[10]) / SMI_YES) * log((float(vars[10]) / SMI_YES),2))
			ya -= 0 - ((float(vars[11]) / SMI_YES) * log((float(vars[11]) / SMI_YES),2))
			na -= 0 - ((float(vars[12]) / SMI_NO) * log((float(vars[12]) / SMI_NO),2))
			na -= 0 - ((float(vars[13]) / SMI_NO) * log((float(vars[13]) / SMI_NO),2))
			na -= 0 - ((float(vars[14]) / SMI_NO) * log((float(vars[14]) / SMI_NO),2))
			na -= 0 - ((float(vars[15]) / SMI_NO) * log((float(vars[15]) / SMI_NO),2))
			na -= 0 - ((float(vars[16]) / SMI_NO) * log((float(vars[16]) / SMI_NO),2))
			na -= 0 - ((float(vars[17]) / SMI_NO) * log((float(vars[17]) / SMI_NO),2))
			na -= 0 - ((float(vars[18]) / SMI_NO) * log((float(vars[18]) / SMI_NO),2))
			na -= 0 - ((float(vars[19]) / SMI_NO) * log((float(vars[19]) / SMI_NO),2))
			na -= 0 - ((float(vars[20]) / SMI_NO) * log((float(vars[20]) / SMI_NO),2))
			na -= 0 - ((float(vars[21]) / SMI_NO) * log((float(vars[21]) / SMI_NO),2))
			na -= 0 - ((float(vars[22]) / SMI_NO) * log((float(vars[22]) / SMI_NO),2))
		iGain = SMI_ENTROPY - (ya + na)
		variables[varName] = iGain

theFile.close()

# so at this point we're done with our hash and now we have to...
# sort the hash and get the top i-gains!
sorted_vars = sorted(variables.items(), key=operator.itemgetter(1))
for item in sorted_vars[-25:]:
	print "%s: %d" % (item)

