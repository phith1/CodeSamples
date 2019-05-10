# Phillip Thompkins
# CMSC 476 HW3
# Document Tokenizer

import os, re, time, profile, timeit
import collections as coll

# The first input is the directory where the input files are.
# The second input is the output directory.
# The third input is the name of the list of stopwords. 
def main(inputDir, outputDir, stopWordFile = "stopwords.txt"):
	# creates the empty dictionary and a variable to track which document we're on
	dictionary = dict()
	docNumber = 0
	
	# gets the list of files from the directory
	files = os.listdir(inputDir)
	if not(os.path.exists(outputDir)):
		os.makedirs(outputDir)
	
	allTokens = TokenLibrary()
	
	# Goes through each file and prints out the tokens in the file
	for fileName in files:
		tokenLib = TokenLibrary()
		inputFile = open(os.path.join(inputDir, fileName), 'r')
		
		# tokenizes each file
		tokens = tokenize(inputFile.read())
		inputFile.close()
		
		# uses the python counter class to keep track of the number of occurrences
		tokenLib.tokens.update(tokens)
		allTokens.tokens.update(tokens)

		# removes the stopwords for each document
		tokens = tokenLib.tokens.most_common()
		for stopWord in readStopWords(stopWordFile):
			del tokenLib.tokens[stopWord.strip().rstrip('s')]

		# removes words that show up only once in the document
		tokens = tokenLib.tokens.most_common()
		for token in tokens:
			if token[1] <= 1:
				del tokenLib.tokens[token[0]]

		# performs the weighting based on the total number of tokens in the document
		totalTokens = 0.0
		tokens = tokenLib.tokens.most_common()
		for token in tokens:
			totalTokens += float(token[1])

		for token in tokens:
			tokenLib.tokens[token[0]] = (tokenLib.tokens[token[0]]/totalTokens) * 100
			
		# NEW FOR HW3: adds the information to the dictionary
		for token in tokens:
			dictionary[token] = [[docNumber], tokenLib.tokens[token[0]]]
			
		docNumber += 1

		# command to create file containing weightings is disabled, it's unnecessary
		# tokenLib.toFile(os.path.join(outputDir, fileName + '.txt'))

	# remove the stopwords from the entire token library
	tokens = allTokens.tokens.most_common()
	for stopWord in readStopWords(stopWordFile):
		del allTokens.tokens[stopWord.strip().rstrip('s')]

	# remove words that show up once in the entire library
	# AS OF HW3: removes words that are 30 or more characters long
	tokens = allTokens.tokens.most_common()
	for token in tokens:
		if token[1] <= 1 or token.len >= 30:
			del allTokens.tokens[token[0]]

	# perform the weighting based on the total number of token in the corpus
	totalTokens = 0.0
	tokens = allTokens.tokens.most_common()
	for token in tokens:
		totalTokens += float(token[1])

	for token in tokens:
		allTokens.tokens[token[0]] = (allTokens.tokens[token[0]]/totalTokens) * 100

	# disabling this command, it's unnecessary for this implementation
	# allTokens.toFile("all_tokens.txt")
	
	# create the files that will be used for HW3
	dic = open("dictionaryFileThompkins.txt", 'w')
	post = open("postingsFileThompkins.txt", 'w')
	# variable to track which line a given word starts on
	postingsLine = 0
	
	# loop through each key...
	for key in dictionary.keys():
		# ...get the value, and for each value(docnum/weight pair)...
		value = dictionary[key]
		
		# ...write to the dictionary file: word, # of documents, first appearance in postingsFile...
		dic.write(str(key) + "\n" + str(len(value)) + "\n" + postingsLine + "\n")
		
		for x in value:
			# write "docNum, weight" to the postings file and update postingsLine
			post.write(str(x[0]) + " " + str(x[1]) + "\n")
			postingsLine += 1
		# at this point we've written all of the values for a key!
	
	# at this point we should be done!
	dic.close();
	post.close();
	
	return

def readStopWords(fileName):
	stopWords = []
	with  open(fileName, 'r') as stopWordsFile:
		for line in stopWordsFile:
			stopWords.append(line)
	return stopWords


def tokenize(inString):
	# takes in a string of the full document
	words = inString.split()
	toRemove = []
	
	# loops through each word in the file
	for i in range(len(words)):
		
		# strips whitespace and punctuation
		words[i] = words[i].strip()
		words[i] = words[i].strip('?<>=`~_:;,.()[]{}+-/\|"!@#$%^&*')
		words[i] = words[i].strip("'")
		words[i] = words[i].strip()
		
		# checks for entire numbers and marks them for removal
		try:
			float(words[i])
			toRemove.append(i)
		except ValueError:		
			# catches empty/single strings and strings with non-alphanumeric elements
			if (len(words[i]) <= 1 or 
				words[i].find('<') != -1 or
				words[i].find('>') != -1 or 
				words[i].find('#') != -1 or
				words[i].find(']') != -1 or
				words[i].find('[') != -1 or
				words[i].find('&') != -1 or
				words[i].find('%') != -1 or
				words[i].find('$') != -1 or
				words[i].find('^') != -1 or
				words[i].find('*') != -1 or
				words[i].find('=') != -1 or
				words[i].find('`') != -1 or
				words[i].find('~') != -1 or 
				words[i].find('!') != -1 or
				words[i].find('@') != -1 or
				words[i].find('(') != -1 or
				words[i].find(')') != -1 or
				words[i].find('_') != -1 or
				words[i].find('+') != -1 or
				words[i].find('{') != -1 or
				words[i].find('}') != -1 or
				words[i].find('|') != -1 or
				words[i].find('/') != -1 or 
				words[i].find('"') != -1 or
				words[i].find(':') != -1 or
				words[i].find(';') != -1 or
				words[i].find('.') != -1 or
				words[i].find(',') != -1 or
				words[i].find('?') != -1):
				toRemove.append(i)
			else:
				words[i] = words[i].lower()
	
	# Removal is after the loop since the count does not update on removal
	toRemove.reverse()
	for i in toRemove:
		words.pop(i)
	
	return words

class TokenLibrary:
	tokens = coll.Counter()

	def __init__(self):
		self.tokens = coll.Counter()
		return
		
	# Write to file by frequency
	def toFile(self, fileName):
		outFile = open(fileName, 'w')
		toWrite = self.tokens.most_common()
		for token in toWrite:
			outFile.write(str(token[0]) + ' ' + str(token[1]) + '\n')
		outFile.close()
		return

	# Write to file by token name
	def toFileByToken(self, fileName):
		outFile = open(fileName, 'w')
		sortedTokens = sorted(self.tokens)
		for tokenName in sortedTokens:
			outFile.write(tokenName + ' ' + str(self.tokens[tokenName]) + '\n')
		outFile.close()
		return
		
	# Read from file
	def readFile(self, fileName):
		with open(fileName, 'r') as inFile:
			for token in inFile:
				token = token.strip()
				token = token.split(' ')
				self.tokens[token[0]] += int(token[1])
		return
	
	# Display by frequency
	def displayByFrequency(self):
		print('\nAll tokens listed by Frequency:\n')
		sortedTokens = self.tokens.most_common()
		for token in sortedTokens:
			print(token[0] + ' ' + str(token[1]))
		return
		
	# Display by token name
	def displayByToken(self):
		print('\nAll tokens listed by Token Name:\n')
		sortedTokens = sorted(self.tokens)
		for tokenName in sortedTokens:
			print(tokenName + ' ' + str(self.tokens[tokenName]))
		return

def runAll():
	print ("Time to Complete 1 file:")
	print timeit.timeit(stmt = 'tokenizer.main("files_1", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 50 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_50", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 100 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_100", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 150 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_150", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 200 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_200", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 250 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_250", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 300 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_300", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 350 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_350", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 400 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_400", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 450 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_450", "output")', setup = 'import tokenizer', number=5)
	print

	print ("Time to Complete 503 files:")
	print timeit.timeit(stmt = 'tokenizer.main("files_503", "output")', setup = 'import tokenizer', number=5)
