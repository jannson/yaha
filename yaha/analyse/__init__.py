# -*- coding=utf-8 -*-
import sys
import os, codecs, re, math
import collections
import threading
import codecs
from math import sqrt
from yaha import DICTS, get_dict, Cuttor
from analyzer import ChineseAnalyzer

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

def __search_word(sentences, word):
    for s in sentences:
        if s.find(word)>=0:
            return s
    return ''

def summarize1(original_text, summary_size = 8, cuttor = None):
    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()
        tmp_cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))

    words_sorted = extract_keywords(original_text, 16, cuttor)
    summary_set = {}
    sentences = []
    for s,need in tmp_cuttor.cut_to_sentence(original_text):
        if need:
            sentences.append(s)

    for word in words_sorted:
        matching_sentence = __search_word(sentences, word)
        if matching_sentence <> '':
            summary_set[matching_sentence] = 1
            if len(summary_set) >= summary_size:
                break
    summary = []
    for s in sentences:
        if s in summary_set:
            summary.append(s)
    return ', '.join(summary)+'.'

N = 80  # Number of words to consider
CLUSTER_THRESHOLD = 5  # Distance between words to consider
TOP_SENTENCES = 8  # Number of sentences to return for a "top n" summary

def __score_sentences(sentences, important_words, cuttor):
    scores = []
    sentence_idx = -1

    for s in [list(cuttor.cut(s)) for s in sentences]:
        sentence_idx += 1
        word_idx = []

        # For each word in the word list...
        for w in important_words:
            try:
                # Compute an index for where any important words occur in the sentence

                word_idx.append(s.index(w))
            except ValueError, e: # w not in this particular sentence
                pass

        word_idx.sort()

        # It is possible that some sentences may not contain any important words at all
        if len(word_idx)== 0: continue

        # Using the word index, compute clusters by using a max distance threshold
        # for any two consecutive words

        clusters = []
        cluster = [word_idx[0]]
        i = 1
        while i < len(word_idx):
            if word_idx[i] - word_idx[i - 1] < CLUSTER_THRESHOLD:
                cluster.append(word_idx[i])
            else:
                clusters.append(cluster[:])
                cluster = [word_idx[i]]
            i += 1
        clusters.append(cluster)

        # Score each cluster. The max score for any given cluster is the score 
        # for the sentence

        max_cluster_score = 0
        for c in clusters:
            significant_words_in_cluster = len(c)
            total_words_in_cluster = c[-1] - c[0] + 1
            score = 1.0 * significant_words_in_cluster \
                * significant_words_in_cluster / total_words_in_cluster

            if score > max_cluster_score:
                max_cluster_score = score

        scores.append((sentence_idx, score))
    return scores

def summarize2(txt, cuttor=None):
    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()
        tmp_cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))
    
    sentences = []
    #TODO do it better 21/08/13 12:36:08
    for s,need in tmp_cuttor.cut_to_sentence(txt):
        if need:
            sentences.append(s)
    normalized_sentences = [s.lower() for s in sentences]

    top_n_words = extract_keywords(txt, N, tmp_cuttor)
    scored_sentences = __score_sentences(normalized_sentences, top_n_words, tmp_cuttor)

    top_n_scored = sorted(scored_sentences, key=lambda s: s[1])[-TOP_SENTENCES:]
    top_n_scored = sorted(top_n_scored, key=lambda s: s[0])
    top_n_summary=[sentences[idx] for (idx, score) in top_n_scored]
    return ', '.join(top_n_summary) + '.'

#
def summarize3(txt, cuttor=None):
    # TODO how to do this better 21/08/13 13:07:22
    # You can replace this with "import numpy", and of cause you have to
    # install the lib numpy
    name = "numpy"
    numpy = __import__(name, fromlist=[])

    if cuttor:
        tmp_cuttor = cuttor
    else:
        tmp_cuttor = Cuttor()
        tmp_cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))
    
    sentences = []
    #TODO do it better 21/08/13 12:36:08
    for s,need in tmp_cuttor.cut_to_sentence(txt):
        if need:
            sentences.append(s)
    normalized_sentences = [s.lower() for s in sentences]

    top_n_words = extract_keywords(txt, N, tmp_cuttor)
    scored_sentences = __score_sentences(normalized_sentences, top_n_words, tmp_cuttor)
    avg = numpy.mean([s[1] for s in scored_sentences])
    std = numpy.std([s[1] for s in scored_sentences])
    mean_scored = [(sent_idx, score) for (sent_idx, score) in scored_sentences
                   if score > avg + 0.5 * std]
    mean_scored_summary=[sentences[idx] for (idx, score) in mean_scored]
    return ', '.join(mean_scored_summary) + '.'
