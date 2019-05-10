# Phillip Thompkins
# CMSC 476 HW2
# Document Tokenizer
# Additions from previous version:
#	Instant removal of strings containing numbers in tokenize()
#	Addition of stopwords document and removal of stopwords
#	Removal of two of the three symbol-removal commands in tokenize()
#   Post-processing removal of words that occur once in the entire corpus

import os, re, time
import collections as coll

# First input is the directory where the input files are, 
# the second is the output directory
def main(inputDir, outputDir):
	print "RUNNING"
	# gets the list of files from the directory
	files = os.listdir(inputDir)
	if not(os.path.exists(outputDir)):
		os.makedirs(outputDir)
	
	allTokens = TokenLibrary()
	
	# NEW AS OF HW2: Gets the list of stopwords
	stopfile = open(os.path.join(inputDir, "stopwords.txt"), 'r')
	stopwords = stopfile.split()
	stopfile.close()
	
	# Goes through each file and prints out the tokens in the file
	for fileName in files:
		tokenLib = TokenLibrary()
		inputFile = open(os.path.join(inputDir, fileName), 'r')
		
		# does the tokenizing on the file
		tokens = tokenize(inputFile.read(), stopwords)
		inputFile.close()
		
		#uses the python counter class to keep track of the number of occurrences
		tokenLib.tokens.update(tokens)
		allTokens.tokens.update(tokens)
		tokenLib.toFile(os.path.join(outputDir, fileName + '.txt'))
		
		# removes stopwords and things that occur once
		tokens = tokenLib.tokens.most_common()
		for stopWord in readStopWords(stopWordFile):
			del tokenLib.tokens[stopWord.strip()]

		tokens = tokenLib.tokens.most_common()
		for token in tokens:
			if token[1] <= 1:
				del tokenLib.tokens[token[0]]
		
		#perform the weighting based on the total number of token in the document
		totalTokens = 0.0
		tokens = allTokens.tokens.most_common()
		for token in tokens:
			totalTokens += float(token[1])

		for token in tokens:
			allTokens.tokens[token[0]] = (allTokens.tokens[token[0]]/totalTokens) * 100
	
	# removes stopwords and things that occur once
	tokens = tokenLib.tokens.most_common()
	for stopWord in readStopWords(stopWordFile):
		del tokenLib.tokens[stopWord.strip()]

	tokens = tokenLib.tokens.most_common()
	for token in tokens:
		if token[1] <= 1:
			del tokenLib.tokens[token[0]]
			
	#perform the weighting based on the total number of token in the document
	totalTokens = 0.0
	tokens = allTokens.tokens.most_common()
	for token in tokens:
		totalTokens += float(token[1])

	for token in tokens:
		allTokens.tokens[token[0]] = (allTokens.tokens[token[0]]/totalTokens) * 100
	
	#print out the results
	allTokens.toFile("all_tokens.txt")
		
	return

def tokenize(inputString, stopwords):
	# goes through the input and turns it into a list of words for further processing
	wordList = inputString.split()
	# list of indices of things to be removed after tokenization is complete
	toRemove = []
	
	for i in range(len(wordList)):
		# remove white space
		wordList[i] = wordList[i].strip()
		# remove all the random symbols that might appear
		wordList[i] = wordList[i].strip("!@#$%^&*()-_=+{[}]\|;:,.?/")
		# remove all the leading and trailing apostrophes and quotation marks
		wordList[i] = wordList[i].strip("'")
		wordList[i] = wordList[i].strip('"')
		# remove any leading or trailing HTML brackets
		wordList[i] = removeHTML(wordList[i])
		# if the word becomes a single character like "a" or a weird extraneous punctuation, add index for removal
		# NEW AS OF HW2: also adds index for removal if the word is within the list of stopwords
		# NEW AS OF HW2: also adds index for removal is a number is present within the word
		if (len(wordList[i]) <= 1 or 
			wordList[i].find('<') != -1 or
			wordList[i].find('>') != -1 or 
			wordList[i].find('#') != -1 or
			wordList[i].find(']') != -1 or
			wordList[i].find('[') != -1 or
			wordList[i].find('&') != -1 or
			wordList[i].find('%') != -1 or
			wordList[i].find('$') != -1 or
			wordList[i].find('^') != -1 or
			wordList[i].find('*') != -1 or
			wordList[i].find('=') != -1 or
			wordList[i] in stopwords or
			wordList[i].find('0') != -1 or
			wordList[i].find('1') != -1 or 
			wordList[i].find('2') != -1 or
			wordList[i].find('3') != -1 or
			wordList[i].find('4') != -1 or
			wordList[i].find('5') != -1 or
			wordList[i].find('6') != -1 or
			wordList[i].find('7') != -1 or
			wordList[i].find('8') != -1 or
			wordList[i].find('9') != -1):
			toRemove.append(i)
		# put into lowercase
		else:
			wordList[i] = wordList[i].lower()
	
	# goes through toRemove from back to front and removes all indices that were slated for removal
	toRemove.reverse()
	for i in toRemove:
		wordList.pop(i)
		
	return wordList	
	
def removeHTML(word):
	# Assumption is that the input, "word", has HTML code in it, denoted by angle brackets <>.
	# This method removes everything between those brackets and returns the actual word.
	openBracket = word.find("<")
	closeBracket = word.find(">")
	# checks if the bracket is at the start of the word and returns all after the >
	if openBracket == 0:
		return word[closeBracket:]
	# checks if the bracket is at the end of the word and returns all before the <
	elif closeBracket == (len(word) - 1):
		return word[:openBracket]
	# does not check if bracket is between two words "like<i>this" because there would likely be spacing.
	else:
		return word
		

class TokenLibrary:
	tokens = coll.Counter()

	def __init__(self):
		self.tokens = coll.Counter()
		return
	
	#Write to file by frequency
	def toFile(self, fileName):
		outFile = open(fileName, 'w')
		toWrite = self.tokens.most_common()
		for token in toWrite:
			outFile.write(str(token[0]) + ' ' + str(token[1]) + '\n')
		outFile.close()
		return

	#Write to file by token name
	def toFileByToken(self, fileName):
		outFile = open(fileName, 'w')
		sortedTokens = sorted(self.tokens)
		for tokenName in sortedTokens:
			outFile.write(tokenName + ' ' + str(self.tokens[tokenName]))
		outFile.close()
		return
		
	#read from file
	def readFile(self, fileName):
		with open(fileName, 'r') as inFile:
			for token in inFile:
				token = token.strip()
				token = token.split(' ')
				self.tokens[token[0]] += int(token[1])
		return
	
	#display by frequency
	def displayByFrequency(self):
		print('\nAll tokens listed by Frequency:\n')
		sortedTokens = self.tokens.most_common()
		for token in sortedTokens:
			print(str(token[0]) + ' ' + str(token[1]))
		return
		
	#display by token name
	def displayByToken(self):
		print('\nAll tokens listed by Token Name:\n')
		sortedTokens = sorted(self.tokens)
		for tokenName in sortedTokens:
			print(tokenName + ' ' + str(self.tokens[tokenName]))
		return
		
