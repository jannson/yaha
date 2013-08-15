# -*- coding=utf-8 -*-
import sys

import os, codecs, re, math
import cProfile
import collections
from prob_cut import BaseCutter

max_word_len = 5 
entropy_threshold = 1 
re_line = re.compile("\W+|[a-zA-Z0-9]+", re.UNICODE)
accepted_line = re.compile(ur"(\d+-\d+-\d+|\[[^\]]+\])")

class Word:
    def __init__(self, id):
        self.process_freq = 1
        self.total_freq = 1
        self.valid = 0
        self.process_ps = 0.0
        self.id = id
        self.l_len = 0
        self.r_len = 0
        self.l = collections.Counter()
        self.r = collections.Counter()
        self.base_freq = 0
        self.base_ps = 0.0
        self.curr_ps = 0.0

    def add(self):
        self.process_freq += 1
        self.total_freq += 1

    def add_l(self, word):
        if word in self.l:
            self.l[word] += 1
        else:
            self.l[word] = 1
        self.l_len += 1
    
    def add_r(self, word):
        if word in self.r:
            self.r[word] += 1
        else:
            self.r[word] = 1
        self.r_len += 1

    def reset(self, id):
        self.process_freq = 1
        self.id = id
        self.l_len = 0
        self.r_len = 0
        self.l = collections.Counter()
        self.r = collections.Counter()

def info_entropy(words, total):
    result = 0 
    for word, cnt in words.iteritems():
        p = float(cnt) / total
        result -= p * math.log(p)
    return result

class Process(object):
    def __init__(self, id):
        self.id = id
        self.words = []
        self.cache_lines = []
    
    def add_words(self, word):
        self.words.append(word)

    def do_sentence(self, sentence, word_dict):
        l = len(sentence)
        wl = min(l, max_word_len)
        self.cache_lines.append(sentence)
        for i in xrange(1, wl + 1): 
            for j in xrange(0, l - i + 1): 
                if j == 0:
                    if j < l-i:
                        word_dict.add_word_r(sentence[j:j+i], sentence[j+i])
                    else:
                        word_dict.add_word(sentence[j:j+i])
                else:
                    if j < l-i:
                        word_dict.add_word_lr(sentence[j:j + i], sentence[j-1], sentence[j+i])
                    else:
                        word_dict.add_word_l(sentence[j:j+i], sentence[j-1])

    def calc(self, word_dict):
        # calc all ps first
        for word in self.words:
            this_word = word_dict.get_word(word)
            this_word.process_ps = float(this_word.process_freq)/word_dict.process_total
    
        # then calc the ps around the word
        for word in self.words:
            this_word = word_dict.get_word(word)
            if len(word) > 1:
                p = 0
                for i in xrange(1, len(word)):
                    t = word_dict.ps(word[0:i]) * word_dict.ps(word[i:])
                    p = max(p, t)
                if p > 0 and this_word.process_freq >= 3 and this_word.process_ps / p > 100:
                    left_info_entropy = info_entropy(this_word.l, this_word.l_len)
                    right_info_entropy = info_entropy(this_word.r, this_word.r_len)
                    if this_word.l_len > 0 and left_info_entropy < entropy_threshold:
                        continue
                    if this_word.r_len > 0 and right_info_entropy < entropy_threshold:
                        continue
                    this_word.valid += 1
                    this_word.curr_ps = math.log(float(this_word.total_freq+this_word.base_freq)/float(word_dict.base_total+word_dict.total/word_dict.id))

class WordDict(BaseCuttor):

    def __init__(self, base_dict):
        self.dict = {}
        self.total = 0
        self.base_total = 0
        self.id = 0
        self.process_total = 0
        self.current_line = 0
        
        self.WORD_MAX = 5
        
        with codecs.open(base_dict, "r", "utf-8") as file:
            for line in file:
                tokens = line.split(" ")
                word = tokens[0].strip()
                if len(tokens) >= 2:
                    this_word = Word(0)
                    freq = int(tokens[1].strip())
                    this_word.base_freq = freq
                    self.dict[word] = this_word
                    self.base_total += freq
        
        #normalize
        for word, term in self.dict.iteritems():
            term.base_ps = math.log(float(term.base_freq)/self.base_total)
            term.curr_ps = term.base_ps

        self.new_process()

    def add_user_dict(self, filename):
        with codecs.open(filename, "r", "utf-8") as file:
            for line in file:
                tokens = line.split(" ")
                word = tokens[0].strip()
                if len(tokens) >= 2:
                    freq = int(tokens[1].strip())
                    if word in self.dict:
                        this_word = self.dict[word]
                        this_word.base_freq += freq
                        self.base_total += freq
                    else:
                        this_word = Word(0)
                        this_word.base_freq = freq
                        self.dict[word] = this_word
                        self.base_total += freq
        #normalize
        for word, term in self.dict.iteritems():
            term.base_ps = math.log(float(term.base_freq)/self.base_total)
            term.curr_ps = term.base_ps
    
    def exist(self, word):
        if word not in self.dict:
            return False
        this_word = self.dict[word]
        return (this_word.curr_ps < 0.0) or (this_word.valid > self.id/2)

    def get_prob(self, word):
        if word in self.dict:
            return self.dict[word].curr_ps
        else:
            return 0.0
    
    def new_process(self):
        self.id += 1
        self.process = Process(self.id)
        self.process_total = 0
        return self.process
    
    def add_word(self, word):
        this_word = None
        if word in self.dict:
            this_word = self.dict[word]
            if self.id == this_word.id:
                this_word.add()
            else:
                this_word.reset(self.id)
                self.process.add_words(word)
        else:
            this_word = Word(self.id)
            self.dict[word] = this_word
            self.process.add_words(word)
        self.process_total += 1
        self.total += 1
        return this_word

    def learn(self, sentence):
        self.process.do_sentence(sentence, self)
        self.current_line += 1
        if self.current_line > 10000:
            self.process.calc(self)
            self.new_process()
            self.current_line = 0

    def learn_flush(self):
        self.process.calc(self)
        self.new_process()
        self.current_line = 0

    def cut_and_learn(self, sentence):
        self.learn(sentence)
        self.cut(sentence)

    def add_word_l(self, word, l):
        w = self.add_word(word)
        w.add_l(l)
    
    def add_word_r(self, word, r):
        w = self.add_word(word)
        w.add_r(r)
    
    def add_word_lr(self, word, l, r):
        w = self.add_word(word)
        w.add_l(l)
        w.add_r(r)

    def ps(self, word):
        if word in self.dict and self.dict[word].id == self.id:
            return self.dict[word].process_ps
        else:
            return 0.0

    def get_word(self, word):
        return self.dict[word]

def sentence_from_file(filename):
    with codecs.open(filename, 'r', 'utf-8') as file:
        for line in file:
            if not accepted_line.match(line):
                for sentence in re_line.split(line):
                    yield sentence

def save_to_file(filename, word_dict):
    final_words = [] 
    for word, term in word_dict.dict.iteritems():
        if term.valid > word_dict.id/2 and term.base_freq == 0:
            final_words.append(word)

    final_words.sort(cmp = lambda x, y: cmp(word_dict.get_word(y).total_freq, word_dict.get_word(x).total_freq))
    
    file = open(filename, 'w')

    for word in final_words:
        v = word_dict.get_word(word).total_freq
        file.write("%s %d\n" % (word,v))

    file.close()

def test():
    filename = 'qq6'
    word_dict = WordDict('dict.txt')
    #for sentence in sentence_from_file(filename):
    #    word_dict.learn(sentence)
    #word_dict.learn_flush()
    word_dict.add_user_dict('www_qq0')
    
    str = '我们的读书会也顺利举办了四期'
    seg_list = word_dict.cut(str)
    print ', '.join(seg_list)

    #save_to_file('www_'+filename, word_dict)

#cProfile.run('test()')
test()
