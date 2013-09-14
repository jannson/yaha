# -*- coding=utf-8 -*-
import sys,os,codecs,re
import os.path
from whoosh import spelling as whoosh_spelling
from whoosh.automata import fst
from whoosh.filedb.filestore import FileStorage
from heapq import heappush, heapreplace
from yaha.wordmaker import WordDict as WordDict1
from yaha.wordmaker2 import WordDict as WordDict2

class YahaCorrector(whoosh_spelling.Corrector):
    """Suggests corrections based on the content of a raw
    :class:`whoosh.automata.fst.GraphReader` object.

    By default ranks suggestions based on the edit distance.
    """

    def __init__(self, word_file, graph_file):
        dirname = os.path.dirname(graph_file)
        st = FileStorage(dirname)
        f = st.open_file(graph_file)
        gr = fst.GraphReader(f)
        self.graph = gr

        self.dict = {}
        with codecs.open(word_file,'r','utf-8') as file:
            for line in file:
                tokens = line.split(" ")
                if len(tokens) >= 2:
                    self.dict[tokens[0].strip()] = int(tokens[1].strip())
    
    def suggest(self, text, limit=8, maxdist=2, prefix=1):
        _suggestions = self._suggestions

        heap = []
        seen = set()
        for k in xrange(1, maxdist + 1):
            for item in _suggestions(text, k, prefix):
                if item[1] in seen:
                    continue
                seen.add(item[1])

                # Note that the *higher* scores (item[0]) are better!
                if len(heap) < limit:
                    heappush(heap, item)
                elif item > heap[0]:
                    heapreplace(heap, item)

            # If the heap is already at the required length, don't bother going
            # to a higher edit distance
            if len(heap) >= limit:
                break

        sugs = sorted(heap, key=lambda item: (0 - item[0], item[1]))
        return [sug for _, sug in sugs]

    def _suggestions(self, text, maxdist, prefix):
        if self.dict.has_key(text):
            yield (len(text)*10 + self.dict.get(text,0)*5, text)
        for sug in fst.within(self.graph, text, k=maxdist, prefix=prefix):
            # Higher scores are better, so negate the edit distance
            yield ((0-maxdist)*100 + len(sug)*10 + self.dict.get(sug,0), sug)

re_line = re.compile("\W+|[a-zA-Z0-9]+", re.UNICODE)
def words_train(in_file, word_file, graph_file):

    # Can only use a exists word_file to make graph_file
    if in_file is not None:
        #Auto create words from in_file
        file_size = os.path.getsize(in_file)
        word_dict = None
        if file_size > 3*1024*1024:
            # A little more quick but inaccurate than WordDict1
            word_dict = WordDict2()
            print >> sys.stderr, 'please wait, getting words from file', in_file
        else:
            word_dict = WordDict1()
        with codecs.open(in_file, 'r', 'utf-8') as file:
            for line in file:
                for sentence in re_line.split(line):
                    word_dict.learn(sentence)
        word_dict.learn_flush()
        print >> sys.stderr, 'get all words, save word to file', word_file
        
        word_dict.save_to_file(word_file)
        print >> sys.stderr, 'save all words completely, create word graphp', graph_file

    words = []
    with codecs.open(word_file,'r','utf-8') as file:
        for line in file:
            tokens = line.split(" ")
            if len(tokens) >= 2:
                words.append(tokens[0].strip())
    words = sorted(words)

    whoosh_spelling.wordlist_to_graph_file(words, graph_file)
    print >> sys.stderr, 'words_train ok'
