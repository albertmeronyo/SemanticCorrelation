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
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wgs: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX sdmx: <http://purl.org/linked-data/sdmx#>
PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#>
PREFIX sdmx-dimension: <http://purl.org/linked-data/sdmx/2009/dimension#>
PREFIX sdmx-measure: <http://purl.org/linked-data/sdmx/2009/measure#>
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX year: <http://reference.data.gov.uk/id/year/>
PREFIX void: <http://rdfs.org/ns/void#>

PREFIX wbld: <http://worldbank.270a.info/>
PREFIX property: <http://worldbank.270a.info/property/>
PREFIX classification: <http://worldbank.270a.info/classification/>
PREFIX indicator: <http://worldbank.270a.info/classification/indicator/>
PREFIX country: <http://worldbank.270a.info/classification/country/>
PREFIX income-level: <http://worldbank.270a.info/classification/income-level/>
PREFIX lending-type: <http://worldbank.270a.info/classification/lending-type/>
PREFIX region: <http://worldbank.270a.info/classification/region/>
PREFIX source: <http://worldbank.270a.info/classification/source/>
PREFIX topic: <http://worldbank.270a.info/classification/topic/>
PREFIX currency: <http://worldbank.270a.info/classification/currency/>
PREFIX project: <http://worldbank.270a.info/classification/project/>
PREFIX loan-status: <http://worldbank.270a.info/classification/loan-status/>
PREFIX variable: <http://worldbank.270a.info/classification/variable/>
PREFIX global-circulation-model: <http://worldbank.270a.info/classification/global-circulation-model/>
PREFIX scenario: <http://worldbank.270a.info/classification/scenario/>

PREFIX stats: <http://stats.270a.info/vocab#>

PREFIX d-indicators: <http://worldbank.270a.info/dataset/world-bank-indicators>
PREFIX d-finances: <http://worldbank.270a.info/dataset/world-bank-finances/>
PREFIX d-climates: <http://worldbank.270a.info/dataset/world-bank-climates/>

#USE THESE GRAPHS :)
PREFIX g-void: <http://worldbank.270a.info/graph/void>
PREFIX g-meta: <http://worldbank.270a.info/graph/meta>
PREFIX g-climates: <http://worldbank.270a.info/graph/world-bank-climates>
PREFIX g-finances: <http://worldbank.270a.info/graph/world-bank-finances>
PREFIX g-projects: <http://worldbank.270a.info/graph/world-bank-projects-and-operations>
PREFIX g-indicators: <http://worldbank.270a.info/graph/world-development-indicators>

SELECT DISTINCT ?title
WHERE {
GRAPH g-indicators: {
?s qb:dataSet ?dataset .
?s sdmx-dimension:refPeriod year:2010 .
}
GRAPH g-meta: {
?dataset dcterms:title ?title .
}
}
ORDER BY ?title
} %s
""" % limit)
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

