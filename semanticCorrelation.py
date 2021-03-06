#!/usr/bin/env python

# semanticCorrelation: similarity between statistical concepts

from nltk.corpus import wordnet
import nltk
from SPARQLWrapper import SPARQLWrapper, JSON
import argparse
import logging
import csv
from gensim import corpora, models, similarities
import sys

import myquery

class SemanticCorrelation():
    
    def __init__(self, __logLevel, __outfile, __endpoint = None, __infile = None, __ntopics = 200, __iters = 2):
        self.log = logging.getLogger('SemanticCorrelation')
        self.log.setLevel(__logLevel)

        self.endpoint = __endpoint
        self.outfile = __outfile
        self.infile = __infile
        self.ntopics = int(__ntopics)
        self.iters = int(__iters)

        self.log.info('Setting up data structures...')
        self.concepts = []
        self.identifiers = []
        self.similarity = {} # keys are tuples (concept_1, concept_2)

        if self.endpoint:
            self.log.info('Querying endpoint at %s...' % self.endpoint)
            self.queryEndpoint()
        else:
            self.log.info('Reading local CSV cache %s...' % self.infile)
            self.readLocalFile(self.infile)
        self.log.info('Computing semantic similarity with %s topics...' % self.ntopics)
        # self.computeWordnetSimilarity()
        self.computeLSI()
        self.computeLSISimilarity()
        # print self.similarity
        self.log.info('Serializing to %s...' % self.outfile)
        self.serializeSimilarity(self.outfile)

    def readLocalFile(self, infile):
        with open(infile, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='\"')
            next(csvreader, None)  # skip the headers
            for row in csvreader:
                self.identifiers.append(row[0])
                self.concepts.append(row[1])

    def queryEndpoint(self):
        sparql = SPARQLWrapper(self.endpoint)
        self.log.debug('Setting query...')
        sparql.setQuery(myquery.SPARQL_QUERY)
        sparql.setReturnFormat(JSON)
        self.log.debug('Querying endpoint...')
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            self.concepts.append(result["title"]["value"])
            self.identifiers.append(result["identifier"]["value"])
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
        tokenizer = nltk.tokenize.RegexpTokenizer('\(.*\)|[\s\.\,\%\:\$]+', gaps=True)
        texts = [[word for word in tokenizer.tokenize(document.lower()) if word not in nltk.corpus.stopwords.words('english')] for document in self.concepts]
        self.log.debug(texts)

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
        self.lsi = models.LsiModel(corpus_tfidf, power_iters=self.iters, id2word=self.dictionary, num_topics=self.ntopics) # initialize an LSI transformation
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
                self.log.debug([sim, self.concepts[c], self.concepts[sim[0]]])

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
            csvwriter.writerow(["datasetX", "datasetY", "similarity"])
            for i in range(len(self.concepts)):
                for j in range(len(self.concepts)):
                    if i <= j:
                        csvwriter.writerow([self.identifiers[i], 
                                            self.identifiers[j], 
                                            self.similarity[(i,j)]])

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Computes semantic similarities between all concepts retrieved via SPARQL")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--endpoint', '-e',
                        help = "Read literals from SPARQL endpoint")
    input_group.add_argument('--infile', '-i',
                        help = "Read from local CSV cache")
    parser.add_argument('--verbose', '-v',
                        help = "Be verbose -- debug logging level",
                        required = False, 
                        action = 'store_true')
    parser.add_argument('--topics', '-t',
                        help = "Number of topics for the LSI (default 200)",
                        required = False,
                        default = 200)
    parser.add_argument('--iters', '-it',
                        help = "Number of power iterations (default 2)",
                        required = False,
                        default = 2)
    parser.add_argument('--outfile', '-o',
                        help = "Output CSV file to write similarities",
                        required = True)

    args = parser.parse_args()

    # Logging
    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG
    logging.basicConfig(level=logLevel)
    logging.info('Initializing...')

    # Instance
    semcor = SemanticCorrelation(logLevel, args.outfile, args.endpoint, args.infile, args.topics, args.iters)

    logging.info('Done.')
