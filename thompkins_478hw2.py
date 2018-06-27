# Phillip Thompkins
# phith1@umbc.edu
# CMSC478 (Machine Learning) Fall 2014 HW2
# K-Means Clustering of MNIST data

import math, sys, os, random

# holds the label and corresponding pixel shadings for a given data instance
class Numeral:
	# numLabel is the singular 0-9 integer within mnist_labels
	# listPixels is the array of values (size 784) between 0-255 within mnist_data
	def __init__(self, numLabel, listPixels):
		self.label = numLabel
		self.pixels = listPixels
		
# has a separate instance for the cluster centroid and the members of the cluster
class Cluster:
	# center is the Numeral averaging the data of all cluster members
	# members is the array of Numerals that make up the cluster
	def __init__(self, centerpoint):
		self.center = centerpoint
		self.members = []
		self.labelCounts = [0] * 10
		self.members.append(centerpoint)
		
	# goes through and changes center to the average of all other Numerals in the cluster
	def newCenter(self):
		newLabel = self.mostCommonLabel()
		newPixels = [0] * 784
		pixelValues = [0] * 784
		# loop through all members and then all pixels in each member
		for item in self.members:
			for pixel in pixelValues:
				pixelValues[pixel] += item.pixels[pixel]
		# compute the average of each pixel's values throughout the cluster
		for pixelNum in pixelValues:
			newPixels[pixelNum] = int(pixelValues[pixelNum] / len(self.members))
		centered = Numeral(newLabel, newPixels)
		return centered
		
	# appends a new member in Numeral form to the cluster's members list
	def addMember(self, member):
		self.members.append(member)
		
	# resets the members list to an empty list
	def clearMembers(self):
		del self.members[:]
		self.members = []
		
	# finds the most abundant label for the sake of recomputing the centerpoint	
	def mostCommonLabel(self):
		for member in self.members:
			self.labelCounts[member.label] += 1
		highest = max(self.labelCounts)
		return self.labelCounts.index(highest)
		
	# determines the length of a given item from the center of the cluster
	def distance(self, otherInstance):
		dist = 0
		for i in range(0, 784):
			# adds a ratio of the distance to the overall distance tracker
			# comparing a pixels at 255 and 0 produce difference value of 1, while exact matches produce difference 0
			dist += abs(self.center.pixels[i] - otherInstance.pixels[i])/float(255)
		return dist
		
def main(kValue):
	# create k many clusters
	k = kValue
	# clusters and dataPoints are both Numerals
	clusters = []
	dataPoints = []
	
	# Go through and turn the entire dataset into a 10,000 size array of "Numerals" with a corresponding "Label"
	
	# open both the Label and Data files simultaneously
	labelFile = open("mnist_labels.txt", "r")
	pixelFile = open("mnist_data.txt", "r")
	
	# populate the dataPoints list with Numerals created from the input files
	for i in range(0, 10000):
		tempLabel = int(labelFile.readline().strip())
		numbers = pixelFile.readline()
		pixelsAsStr = numbers.split()
		pixelsAsInt = []
		for j in range(0, len(pixelsAsStr)):
			pixelsAsInt.append(int(pixelsAsStr[j]))
		dataPoints.append(Numeral(tempLabel, pixelsAsInt))
	
	pixelFile.close();
	labelFile.close();
	
	# Generate "K" random numbers that will correspond to the initial cluster centers. 
	# generate the random numbers
	randClusters = [] 
	#for i in range(0, k):
	#	randNum = random.randint(0, len(dataPoints)-1)
	#	while randNum in randClusters:
	#		randNum = random.randint(0, len(dataPoints)-1)
	#	randClusters.append(randNum)
	
	# Generate 10 numbers that correspond to getting one representative for each label
	for i in range(0, ):
		randNum = random.randint(0, len(dataPoints)-1)
		while dataPoints[randNum].label != i:
			randNum = random.randint(0, len(dataPoints)-1)
		randClusters.append(randNum)
		
	# assign these randomly generated data points as cluster centroids
	for i in range(0, k):
		index = int(randClusters[i])
		clustToAdd = dataPoints[index]
		clusters.append(Cluster(clustToAdd))
	
	# Go thru each of the 10,000 items, and append them to the nearest cluster centroid. 
	for item in dataPoints:
		distances = []
		for clust in clusters:
			distances.append(clust.distance(item))
		closest = min(distances)
		closestCluster = distances.index(closest)
		clusters[closestCluster].addMember(item)
	
	# REPEAT a bunch of times to get close to convergence
	for x in range (0, 5):
		# add everything to the list based off of the new centers
		for item in dataPoints:
			distances = []
			for clust in clusters:
				distances.append(clust.distance(item))
			closest = min(distances)
			closestCluster = distances.index(closest)
			clusters[closestCluster].addMember(item)
		
		# recalculate the cluster's center and clear the list
		for cluster in clusters:
			newC = cluster.newCenter()
			cluster.center = newC
			del cluster.members[:]
			cluster.addMember(newC)	
	
	# At this point, the cluster centroids aren't changing anymore!
	for clustered in clusters:
		print("------Cluster " + str(clusters.index(clustered)) + "------")
		print("Cluster Size: " + str(len(clustered.members)))
		print("Most Common Label: " + str(clustered.mostCommonLabel()))
		# distribution corresponds to individual number counts, so [1,1,1,1,1,1,1,1,1] 
		#	means that there is one member with each label in the cluster
		print("Label Distribution:\n", clustered.labelCounts)
		
main(10)