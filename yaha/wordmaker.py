# -*- coding=utf-8 -*-
import sys
import os, codecs, re, math
import collections
import threading
from yaha import BaseCuttor, WordBase, get_dict, DICTS

max_word_len = 5 
entropy_threshold = 1 
max_to_flush = 10000

class Word(WordBase):
    def __init__(self, id):
        super(WordBase, self).__init__()

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

# TODO has a better implement?
# How to add fields to Objects dynamically ?
MODIFY_LOCK = threading.RLock()
MODIFY_INIT = False
def modify_wordbase(word):
        word.process_freq = 1
        word.total_freq = 1
        word.valid = 0
        word.process_ps = 0.0
        word.id = id
        word.l_len = 0
        word.r_len = 0
        word.l = collections.Counter()
        word.r = collections.Counter()
        word.curr_ps = word.base_ps
        word.add = Word.add
        word.add_l = Word.add_l
        word.add_r = Word.add_r
        word.reset = Word.reset

def get_modified_dict():
    global MODIFY_INIT
    dict = get_dict(DICTS.MAIN)
    if MODIFY_INIT:
        return dict
    with MODIFY_LOCK:
        if MODIFY_INIT:
            return dict
        for word in dict:
            modify_wordbase(word)
        MODIFY_INIT = True
    return dict

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
                    if this_word.l_len > 0 and info_entropy(this_word.l, this_word.l_len) < entropy_threshold:
                        continue
                    if this_word.r_len > 0 and info_entropy(this_word.r, this_word.r_len) < entropy_threshold:
                        continue
                    this_word.valid += 1
                    this_word.curr_ps = math.log(float(this_word.total_freq+this_word.base_freq)/float(word_dict.base_total+word_dict.total/word_dict.id))

class WordDict(BaseCuttor):

    def __init__(self, new_dict=True):
        super(WordDict, self).__init__()

        self.dict = {}
        self.total = 0
        self.base_total = 0
        self.id = 0
        self.process_total = 0
        self.current_line = 0
        
        self.WORD_MAX = 5
        
        '''with codecs.open(dict_file, "r", "utf-8") as file:
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
            term.curr_ps = term.base_ps'''

        if not new_dict:
            # TODO for getting dict from MAIN_DICT
            self.dict = get_modified_dict()

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
        for s,need_cut in self.cut_to_sentence(sentence):
            if not need_cut:
                continue
            self.process.do_sentence(s, self)
            self.current_line += 1
            if self.current_line > max_to_flush:
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

    def save_to_file(self, filename, sorted=False):
        word_dict = self
        if sorted:
            final_words = []
            for word, term in word_dict.dict.iteritems():
                #if term.valid > word_dict.id/2 and term.base_freq == 0:
                # Use this to save more word
                if term.valid > 0 and term.base_freq == 0:
                    final_words.append(word)

            final_words.sort(cmp = lambda x, y: cmp(word_dict.get_word(y).total_freq, word_dict.get_word(x).total_freq))
            
            with codecs.open(filename, 'w', 'utf-8') as file:
                for word in final_words:
                    v = word_dict.get_word(word).total_freq
                    file.write("%s %d\n" % (word,v))
        else:
            with codecs.open(filename,'w','utf-8') as file:
                for word, term in word_dict.dict.iteritems():
                    if term.valid > 0 and term.base_freq == 0:
                        file.write("%s %d\n" % (word,term.total_freq))

