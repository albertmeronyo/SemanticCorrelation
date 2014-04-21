#!/usr/bin/env python

# semanticCorrelation: similarity between statistical concepts

from nltk.corpus import wordnet
from SPARQLWrapper import SPARQLWrapper, JSON

# SPARQL to get statistical concepts for great justice

sparql = SPARQLWrapper("http://worldbank.270a.info/sparql")
sparql.setQuery("""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?concept ?concept_l
FROM <http://worldbank.270a.info/graph/meta>
WHERE { 
?concept a skos:Concept .
?concept skos:prefLabel ?concept_l .
} LIMIT 100
""")
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
conceptA = 'Spain'
conceptB = 'Temperature'
indexA = statConcepts.index(conceptA)
indexB = statConcepts.index(conceptB)
print "Similarity between %s and %s is %s" % (statConcepts[indexA],
                                              statConcepts[indexB],
                                              statConceptsMatrix[indexA][indexB])
