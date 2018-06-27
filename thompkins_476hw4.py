# Phillip Thompkins
# phith1@umbc.edu
# CMSC476 Spring 2014 HW4
# Query Retrieval

import os, sys, operator
from collections import Counter

def main(): 
	# holds the queries in a list
	queries = Counter()
	# create a hash table to hold the relevant information for all possible query terms that exist in the document corpus
	wordCorpus = {}

	# checks if the command line args are amenable
	if(len(sys.argv) > 1):
		# removes whitespace and lowercases the queries for ease of searching
		queries = [query.strip().lower() for query in sys.argv[1:]]
		queries = Counter(queries)
	else:
		print("\nImproper command line format. Exiting.\n")
		sys.exit()

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
			if word in wordCorpus:
				wordCorpus[word].append((inPost[0], float(inPost[1])))
			# if the word is not in the hashtable, 
			# add it to the hashtable
			else:
				wordCorpus[word] = [(inPost[0], float(inPost[1]))]

	# and now we're done with the dictionary and postings files, so...
	dictFile.close()
	postFile.close()

	# so we have our populated word corpus as a hash table, so now we have to...
	# navigate the hash table and look up the queries! 
	# results is also a hash table for ease of traversal
	results = {}
	for term in queries:
		# if the term exists in the corpus, great!
		if term in wordCorpus:
			# transfer the hits/documents for the term into the results hashtable
			for hit in wordCorpus[term]:

				# if the document has shown up before...
				if hit[0] in results:
					# and if the particular word has been queried in this document...
					if term in results[hit[0]]:
						# add the results together
						results[hit[0]][term] += hit[1]
					else:
						# otherwise, create the spot in the results hash
						results[hit[0]][term] = hit[1]
				# if the document is completely new
				else:
					results[hit[0]] = {term: hit[1]}
		# do not do anything if the term does not exist!!!

	sortedResults = {}
	# if queries don't have results, quit out
	if not results:
		print "\nQueries not found.\n"
		sys.exit()
	# since at this point we DO have results, we need to get them ready to present
	else:
		# dot product the frequency versus how many times the term was in the query 
		# this was something covered in class, I've been told
		for term, frequency in results.iteritems():
			result = 0
			for wordd, freq in frequency.iteritems():
				result += queries[wordd] * freq
			sortedResults[term] = result

		# sort the results by term frequency
		endgame = list(reversed(sorted(sortedResults.iteritems(), key=operator.itemgetter(1))))

		print("==Top Ten Results==")
		# list the first ten results
		for i in range (10):
			# if we have more things to print, print them
			if i < len(endgame): 
				print("%s %f" % (endgame[i][0], endgame[i][1]))
			# if we're out of things to print, quit out
			else:
				break
		print

# returns the number of lines in a file
def fileLength(flNm):
	with open(flNm) as f:
			for counter, l in enumerate(f, 1):
				pass
	return counter


main()