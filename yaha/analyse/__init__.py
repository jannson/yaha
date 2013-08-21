# -*- coding=utf-8 -*-
import sys
import os, codecs, re, math
import collections
import threading
import codecs
from math import sqrt
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
    # the idf.txt file is make by whoosh,
    # I will put this code to extra/idfmake.py 21/08/13 08:39:22
    idf_name = os.path.join(idf_path, "idf.txt")
    content = ''
    num_freqs = 0
    with codecs.open(idf_name, 'r', 'utf-8') as corpus_file:
        # Load number of documents.
        line = corpus_file.readline()
        num_docs = int(line.strip())

        for line in corpus_file:
            tokens = line.split(" ")
            term = tokens[0].strip()
            frequency = int(tokens[1].strip())
            idf_freq[term] = frequency
            num_freqs += float(frequency)

        for term,freq in idf_freq.iteritems():
            idf_freq[term] = math.log(float(1 + num_docs) / (1 + freq))

    IDF_INIT = True

__init_idf()

median_idf = sorted(idf_freq.values())[len(idf_freq)/2]

def extract_keywords(content, topk=18, cuttor=None):
    stopwords = get_dict(DICTS.STOPWORD)

    tmp_cuttor = None
    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()
        #support for number and english 21/08/13 08:43:23
        tmp_cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))

    words = tmp_cuttor.cut(content)
    freq = {}
    total = 0
    for word in words:
        if len(word.strip()) < 2:
            continue
        lower_word = word.lower()
        if stopwords.has_key(lower_word):
            continue
        #TODO only leave the 'n' word? 21/08/13 09:13:36
        if tmp_cuttor.exist(lower_word) and not tmp_cuttor.word_type(lower_word, 'n'):
            continue
        total += 1
        if word in freq:
            freq[lower_word] += 1
        else:
            freq[lower_word] = 1
    freq = [(k,v/total) for k,v in freq.iteritems()]
    tf_idf_list = [(v * idf_freq.get(k,median_idf),k) for k,v in freq]
    st_list = sorted(tf_idf_list, reverse=True)

    top_tuples = st_list[:topk]
    keys = [a[1] for a in top_tuples]
    return keys

def near_duplicate(content1, content2, cuttor=None):
    tmp_cuttor = None
    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()
        tmp_cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))
    file_words = {}
    stopwords = [get_dict(DICTS.STOP_SENTENCE), get_dict(DICTS.EXT_STOPWORD), get_dict(DICTS.STOPWORD)]

    seg_list = tmp_cuttor.cut(content1)
    for w in seg_list:
        is_drop = False
        lw = w.lower()
        for stopword in stopwords:
            if stopword.has_key(lw):
                is_drop = True
                break
            if is_drop:
                continue
            if lw not in file_words.keys():
                file_words[lw] = [1,0]
            else:
                file_words[lw][0] += 1
    
    seg_list = tmp_cuttor.cut(content2)
    for w in seg_list:
        is_drop = False
        lw = w.lower()
        for stopword in stopwords:
            if stopword.has_key(lw):
                is_drop = True
                break
            if is_drop:
                continue
            if lw not in file_words.keys():
                file_words[lw] = [0,1]
            else:
                file_words[lw][1] += 1

    sum_2 = 0
    sum_file1 = 0
    sum_file2 = 0
    for word in file_words.values():
        sum_2 += word[0]*word[1]
        sum_file1 += word[0]**2
        sum_file2 += word[1]**2

    rate = sum_2/(sqrt(sum_file1*sum_file2))
    return rate
