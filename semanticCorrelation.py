#!/usr/bin/env python

# semanticCorrelation: similarity between statistical concepts

from nltk.corpus import wordnet
from SPARQLWrapper import SPARQLWrapper, JSON
import argparse

# Argument parsing

parser = argparse.ArgumentParser(description="Computes semantic similarities between all concepts retrieved via SPARQL")
parser.add_argument('--endpoint', '-e',
                    help = "SPARQL endpoint to query", 
                    required = True)
parser.add_argument('--limit', '-l',
                    help = "Number of max results to retrieve", 
                    required = False)
parser.add_argument('--query-a', '-qa',
                    help = "First concept to compare",
                    required = True)
parser.add_argument('--query-b', '-qb',
                    help = "Second concept to compare",
                    required = True)

args = parser.parse_args()

# SPARQL to get statistical concepts for great justice

limit = ""
if args.limit:
    limit = "LIMIT %s" % args.limit
sparql = SPARQLWrapper(args.endpoint)
sparql.setQuery("""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?concept ?concept_l
FROM <%s>
WHERE { 
?concept a skos:Concept .
?concept skos:prefLabel ?concept_l .
} %s
""" % (args.endpoint, limit))
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# We put results in a list, we'll use its indices

statConcepts = []

for result in results["results"]["bindings"]:
    statConcepts.append(result["concept_l"]["value"])

# We put all these in a NxN matrix to pair all of them

statConceptsMatrix = []

for i in range(len(statConcepts)):
    statConceptsMatrix.append([])
    for j in range(len(statConcepts)):
        # Look for all sysnsets and get first
        # If some not found, similarity = -1
        synsetsA = wordnet.synsets(statConcepts[i])
        synsetsB = wordnet.synsets(statConcepts[j])
        similarity = None
        if synsetsA and synsetsB:
            similarity = synsetsA[0].path_similarity(synsetsB[0])
        statConceptsMatrix[i].append(similarity)

# Query
if args.query_a in statConcepts and args.query_b in statConcepts:
    indexA = statConcepts.index(args.query_a)
    indexB = statConcepts.index(args.query_b)
    print "Similarity between %s and %s is %s" % (statConcepts[indexA],
                                              statConcepts[indexB],
                                              statConceptsMatrix[indexA][indexB])
else:
    if args.query_a not in statConcepts:
        print "%s not found in %s" % (args.query_a, args.endpoint)
    if args.query_b not in statConcepts:
        print "%s not found in %s" % (args.query_b, args.endpoint)

