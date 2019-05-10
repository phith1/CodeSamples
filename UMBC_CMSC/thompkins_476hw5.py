# Phillip Thompkins
# phith1@umbc.edu
# CMSC476 Spring 2014 HW5
# Clustering System

import os, sys, math
from collections import Counter

def main(): 
	# create a hash table to hold the relevant information for all documents in the corpus
	docCorpus = {}

	# open the dictionary and postings files concurrently
	try:
		dictFile = open("Dictionary.txt", "r")
		dictLength = fileLength("Dictionary.txt")
	
	except:
		print ("\nDictionary.txt does not exist.\n")
		sys.exit()
	
	try:
		postFile = open("Postings.txt", "r")
	except:
		print("\nPostings.txt does not exist.\n")
		sys.exit()

	# go through them and populate the corpus
	# going through every three lines of the dictionary because only each third line part of the corpus
	for i in xrange(0, dictLength, 3): 
		# gets the word at the front of the line and strips endline characters
		word = dictFile.readline().strip()
		# gets the number of files it shows up
		listLength = dictFile.readline().strip()
		# actively ignores the third thing
		dictFile.readline()

		for count in range (int(listLength)):
			# gets the corresponding part in the postings file
			inPost = postFile.readline().split()

			# if the word is in the hashtable already, 
			# append it to the existing entry
			if inPost[0] in docCorpus:
				if word in docCorpus[inPost[0]]:
					docCorpus[inPost[0]][word] += float(inPost[1])
				else:
					docCorpus[inPost[0]][word] = float(inPost[1])
			# if the word is not in the hashtable, 
			# add it to the hashtable
			else:
				docCorpus[inPost[0]] = Counter({word: float(inPost[1])})

	# and now we're done with the dictionary and postings files, so...
	dictFile.close()
	postFile.close()

	# now we do a huge loop to handle the clustering of the documents
	moreLoop = True
	while moreLoop == True:
		# if all documents are in a single cluster, stop looping
		if len(docCorpus) == 1:
			moreLoop = False
			pass

		# sort the documents in the corpus by name (in this case number)
		docNames = sorted(docCorpus.keys())
		similars = []
		# set the similarity matrix to pairs of NIL and the length of the document
		for i in range (len(docNames)):
			similars.append([None] * len(docNames))

		# variable avg built to hold average for future clustering thresholds
		avg = 0.0

		# turn the matrix into a triangular matrix
		for i in range(len(docNames)):
			for j in range(len(docNames)):

				# skip diagonals
				if i < j:
					totalSum = 0.0
					sumI = 0.0
					sumJ = 0.0

					# cosine similarities for matrix
					for item in docCorpus[docNames[i]]:
						if item in docCorpus[docNames[j]]:
							sumI = docCorpus[docNames[i]][item]
							sumJ = docCorpus[docNames[j]][item]
							totalSum += (sumI * sumJ)
					# updates the sim matrix and average if sums != 0
					if sumI > 0 and sumJ > 0:
						similars[i][j] = (totalSum/(math.sqrt(sumJ**2) * math.sqrt(sumI**2)))
						avg += similars[i][j]
					# set matrix at the point to zero if a sum = 0
					else: 
						similars[i][j] = 0

		'''
		# Get the most and least similar and the documents closest to the centroid.

		minVal = getMin(similars)
		cl, rw = getCoords(similars, minVal)
		print str(docNames[rw]) + " and " + str(docNames[cl]) + " are least similar"
		print similars[rw][cl]

		minVal = getMax(similars)
		cl, rw = getCoords(similars, minVal)
		print str(docNames[rw]) + " and " + str(docNames[cl]) + " are most similar"
		print similars[rw][cl]


		center = ((avg/len(docNames))/100)
		minVal = None
		location = None
		print "Centroid: " + str((avg/len(docNames))/100)
		for i in range(len(docNames)):
			for j in range(len(docNames)):
				if similars[i][j] != None:
					if minVal == None or math.fabs(similars[i][j] - center) < minVal:
						minVal = math.fabs(similars[i][j]-center)
						location = similars[i][j]

		cl, rw = getCoords(similars, location)
		print str(docNames[rw]) + " and " + str(docNames[cl]) + " are most closest to the centroid"
		print similars[rw][cl]
		sys.exit()
		'''						
						
		# gets the highest value in the similarity matrix
		highest = getMax(similars)

		# checks if the highest value is above the clustering threshold
		if highest >= 0.4:
			column, row = getCoordinates(similars, highest)

			colSplit = docNames[column].split("*")
			rowSplit = docNames[row].split("*")
			comboName = ("*").join(sorted(colSplit + rowSplit))

			# cluster the documents together
			docCorpus[comboName] = docCorpus[docNames[column]] + docCorpus[docNames[row]]
			print str(docNames[row]) + " and " + str(docNames[column]) + " formed a cluster. "

			# clean up the document corpus to prevent reclustering
			del docCorpus[docNames[column]], docCorpus[docNames[row]]

		# if clustering threshold isn't reached, stop clustering
		else: 
			print ("Number of clusters: %d" % len(docCorpus))
			printings = 1
			for thing in docCorpus:
				print("Cluster #" + str(printings) + ": "), 
				print(thing)
				printings += 1
			keepLooping = False

# returns the number of lines in a file
def fileLength(flNm):
	with open(flNm) as f:
			for counter, l in enumerate(f, 1):
				pass
	return counter

# returns the greatest value in the 2d-matrix
def getMax(matrix):
	maxInList = []
	# creates a list of maximums in each row before maxing all rows
	for i in range(len(matrix)):
		maxInList.append(max(matrix[i]))
	return max(sorted(maxInList))

# returns the smallest value in the 2d-matrix
def getMin(matrix):
	minInList = []
	# creates a list of minimums in each row before mining all rows
	for i in range(len(matrix)):
		try:
			# Ignore all of the Nulls!
			minInList.append(min(x for x in matrix[i] if x is not None))
		except:
			pass
	return min(minInList)

# returns the coordinates of the value
def getCoordinates(matrix, val):
	for i in range(len(matrix)):
		try:
			#returns column and row
			return matrix[i].index(val), i
		except:
			pass


main()
