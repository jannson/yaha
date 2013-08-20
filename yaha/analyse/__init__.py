# -*- coding=utf-8 -*-
import sys
import os, codecs, re, math
import collections
import threading
import codecs
from yaha import DICTS, get_dict, Cuttor

IDF_LOCK = threading.RLock()
IDF_INIT = False
idf_freq = {}
DEFAULT_IDF = 1.5

def __init_idf():
    global idf_freq, IDF_INIT
    if IDF_INIT:
        return
    with IDF_LOCK:
        if IDF_INIT:
            return
    idf_path = os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) )  )
    idf_name = os.path.join(idf_path, "idf.txt")
    content = ''
    codecs.open(idf_name, 'r', 'urf-8') as corpus_file:

    # Load number of documents.
    line = corpus_file.readline()
    num_docs = int(line.strip())

    for line in corpus_file:
        tokens = line.split(" ")
        term = tokens[0].strip()
        frequency = int(tokens[1].strip())
        idf_freq[term] = frequency
        num_freqs += float(frequency)

    if term,freq in idf_freq.iteritems():
        idf_freq[term] = math.log(float(1 + num_docs) / (1 + freq))

    IDF_INIT = True

__init_idf()

def __get_idf(word):
    if word in idf_freq:
        return idf_freq[word]
    else:
        return DEFAULT_IDF

def extract_keywords(content, topk=18, cuttor=None):
    stopwords = [get_dict(DICTS.STOP_SENTENCE), get_dict(get_dict(DICTS.STOPWORD),DICTS.EXT_STOPWORD)]

    tmp_cuttor = None
    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()

    words = tmp_cuttor.cut(content)
    freq = {}
    total = 0
    for word in words:
        if len(word.strip()) < 2:
            continue
        is_stop = False
        lower_word = word.lower()
        for stopword in stopwords:
            if stopword.has_key(lower_word):
                is_stop = True
                break
        if not is_stop:
            total += 1
            if word in freq:
                freq[word] += 1
            else:
                freq[word] = 1
    freq = [(k,v/total) for k,v in freq.iteritems()]
    tf_idf_list = [(v * idf_freq.get(k,median_idf),k) for k,v in freq]
    st_list = sorted(tf_idf_list,reverse=True)

    top_tuples= st_list[:topK]
    tags = [a[1] for a in top_tuples]
    return tags
