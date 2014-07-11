SemanticCorrelation
===================

Playground to provide semantic similarity measures between
statistically correlated concepts 


## What is this?

A script that reads concept descriptions in (Linked Statistical)
datasets and outputs the semantic similarity (using
[LSI](http://www.cs.bham.ac.uk/~pxt/IDA/lsa_ind.pdf)) of all possible
pairs.

## Why?

It belongs to a [broader
effort](https://github.com/csarven/linked-dataset-similarity-correlation)
to study the relationship between correlation and semantic similarity
of datasets.

## How to use it?

`./semanticCorrelation.py [-e <endpoint> | -i <input.csv>] -o
<output.csv> [-v]`

## Example

`./semanticCorrelation.py -e http://worldbank.270a.info/sparql -o
similarities.csv -v`

## Dependencies

- Python 2.7.5
- NLTK 2.0.4
- SPARQLWrapper 1.5.2
- gensim 0.10.0

## Disclaimer

Author: [Albert Meroño-Peñuela](https://github.com/albertmeronyo)

License: [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)