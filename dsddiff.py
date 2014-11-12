#!/usr/bin/env python

# dsddiff: similarity between RDF Data Cube DSDs

import argparse
import logging
import urllib2
import rdflib

class DSDDiff():
    
    def __init__(self, __logLevel, __dsds):
        self.log = logging.getLogger('SemanticCorrelation')
        self.log.setLevel(__logLevel)

        self.log.info('Setting up data structures...')
        self.dsd_uri_a = __dsds[0]
        self.dsd_uri_b = __dsds[1]
        self.dsd_a = rdflib.Graph()
        self.dsd_b = rdflib.Graph()

        # 1. Retrieve and load RDF data from specified URIs
        self.dsd_a.load(self.dsd_uri_a)
        self.dsd_b.load(self.dsd_uri_b)
        self.log.debug(self.dsd_a)
        self.log.debug(self.dsd_b)

        # 3. Compare the DSDs

        # 4. Show the result

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Computes similarity between two RDF Data Cube DSDs (Data Structure Definitions)")
    parser.add_argument('--verbose', '-v',
                        help = "Be verbose -- debug logging level",
                        required = False, 
                        action = 'store_true')
    parser.add_argument('--dsds', '-d',
                        help = "URIs of *two* DSDs to be compared",
                        required = True,
                        nargs = 2)

    args = parser.parse_args()

    # Logging
    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG
    logging.basicConfig(level=logLevel)
    logging.info('Initializing...')

    # Instance
    dsddiff = DSDDiff(logLevel, args.dsds)

    logging.info('Done.')
