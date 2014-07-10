#!/usr/bin/env python

# semanticCorrelation: similarity between statistical concepts

from nltk.corpus import wordnet
import nltk
from SPARQLWrapper import SPARQLWrapper, JSON
import argparse
import logging
import csv
from gensim import corpora, models, similarities

class SemanticCorrelation():
    
    def __init__(self, __endpoint, __logLevel, __outfile, __infile = None):
        self.log = logging.getLogger('SemanticCorrelation')
        self.log.setLevel(__logLevel)

        self.endpoint = __endpoint
        self.outfile = __outfile

        self.log.debug('Setting up data structures...')
        self.concepts = []
        self.datasets = []
        self.similarity = {} # keys are tuples (concept_1, concept_2)

        self.log.debug('Querying endpoint at %s...' % self.endpoint)
        self.queryEndpoint()
        # self.readLocalFile(__infile)
        self.log.debug('Computing semantic similarity...')
        # self.computeWordnetSimilarity()
        self.computeLSI()
        self.computeLSISimilarity()
        # print self.similarity
        self.log.debug('Serializing to %s...' % self.outfile)
        self.serializeSimilarity(self.outfile)

    def readLocalFile(self, infile):
        with open(infile, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='\"')
            for row in csvreader:
                self.concepts.append(row[0])

    def queryEndpoint(self):
        sparql = SPARQLWrapper(self.endpoint)
        self.log.debug('Setting query...')
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

        PREFIX g-void: <http://worldbank.270a.info/graph/void>
        PREFIX g-meta: <http://worldbank.270a.info/graph/meta>
        PREFIX g-climates: <http://worldbank.270a.info/graph/world-bank-climates>
        PREFIX g-finances: <http://worldbank.270a.info/graph/world-bank-finances>
        PREFIX g-projects: <http://worldbank.270a.info/graph/world-bank-projects-and-operations>
        PREFIX g-indicators: <http://worldbank.270a.info/graph/world-development-indicators>

        SELECT DISTINCT ?dataset ?title
        WHERE {
        GRAPH g-indicators: {
        ?s qb:dataSet ?dataset .
        ?s sdmx-dimension:refPeriod year:2013 .
        }
        GRAPH g-meta: {
        ?dataset dcterms:title ?title .
        }
        }
        ORDER BY ?title
        """)
        sparql.setReturnFormat(JSON)
        self.log.debug('Querying endpoint...')
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            self.concepts.append(result["title"]["value"])
            self.datasets.append(result["dataset"]["value"])
        self.log.debug('Fecthed %s results' % len(self.concepts))

    def computeWordnetSimilarity(self):
        # We put all these in a NxN matrix to pair all of them
        for i in range(len(self.concepts)):
            for j in range(len(self.concepts)):
                # Look for all sysnsets and get first
                # If some not found, similarity = -1
                synsetsA = wordnet.synsets(self.concepts[i])
                synsetsB = wordnet.synsets(self.concepts[j])
                similarity = None
                if synsetsA and synsetsB:
                    similarity = synsetsA[0].path_similarity(synsetsB[0])
                self.similarity[(i,j)] = similarity

    def computeLSI(self):
        # stoplist = set('for a of the and to in as'.split())
        texts = [[word for word in nltk.word_tokenize(document.lower()) if word not in nltk.corpus.stopwords.words('english')] for document in self.concepts]

        # remove words that appear only once
        all_tokens = sum(texts, [])
        tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
        texts = [[word for word in text if word not in tokens_once] for text in texts]
        # print texts
        
        self.dictionary = corpora.Dictionary(texts)
        self.dictionary.save('/tmp/deerwester.dict')
        # print(dictionary)

        self.corpus = [self.dictionary.doc2bow(text) for text in texts]
        corpora.MmCorpus.serialize('/tmp/deerwester.mm', self.corpus)
        # print(corpus)

        self.tfidf = models.TfidfModel(self.corpus)
        corpus_tfidf = self.tfidf[self.corpus]
        self.lsi = models.LsiModel(corpus_tfidf, id2word=self.dictionary, num_topics=2) # initialize an LSI transformation
        corpus_lsi = self.lsi[corpus_tfidf] # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi
        # self.lsi.print_topics(2)

        self.index = similarities.MatrixSimilarity(self.lsi[self.corpus]) # transform corpus to LSI space and index it

    def computeLSISimilarity(self):
        for c in range(len(self.concepts)):
            doc = self.concepts[c]
            vec_bow = self.dictionary.doc2bow(doc.lower().split())
            vec_lsi = self.lsi[vec_bow] # convert the query to LSI space

            sims = self.index[vec_lsi] # perform a similarity query against the corpus
            sims = sorted(enumerate(sims), key=lambda item: -item[1])
            for sim in sims:
                self.similarity[(c, sim[0])] = sim[1]

    def querySimilarity(self, a, b):
        if a in self.concepts and b in self.concepts:
            indexA = self.concepts.index(a)
            indexB = self.concepts.index(b)
            self.log.info("Similarity between %s and %s is %s" % (self.concepts[indexA],
                                                                  self.concepts[indexB],
                                                                  self.similarity[(indexA, indexB)]))
        else:
            if a not in self.concepts:
                self.log.info("%s not found in %s" % (a, self.endpoint))
            if b not in self.concepts:
                self.log.info("%s not found in %s" % (b, self.endpoint))

    def serializeSimilarity(self, outfile):
        with open(outfile, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',',
                                    quotechar='\"', quoting=csv.QUOTE_MINIMAL)
            for i in range(len(self.concepts)):
                for j in range(len(self.concepts)):
                    csvwriter.writerow([self.datasets[i], 
                                        self.datasets[j], 
                                        self.similarity[(i,j)]])


if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Computes semantic similarities between all concepts retrieved via SPARQL")
    parser.add_argument('--endpoint', '-e',
                        help = "SPARQL endpoint to query", 
                        required = True)
    parser.add_argument('--limit', '-l',
                        help = "Number of max results to retrieve", 
                        required = False)
    parser.add_argument('--verbose', '-v',
                        help = "Be verbose -- debug logging level",
                        required = False, 
                        action = 'store_true')
    parser.add_argument('--query-a', '-qa',
                        help = "First concept to compare",
                        required = True)
    parser.add_argument('--query-b', '-qb',
                        help = "Second concept to compare",
                        required = True)
    parser.add_argument('--outfile', '-o',
                        help = "Output CSV file to write similarities",
                        required = True)
    parser.add_argument('--infile', '-i',
                        help = "Read from local file instead of endpoint",
                        required = False)

    args = parser.parse_args()

    # Logging
    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG
    logging.basicConfig(level=logLevel)
    logging.info('Initializing...')

    # Instance
    semcor = SemanticCorrelation(args.endpoint, logLevel, args.outfile, args.infile)

    logging.info('Done.')
