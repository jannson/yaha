# -*- coding=utf-8 -*-
import sys, os.path, codecs, re, math
import collections

# ksp_dijkstra for default
from ksp_dijkstra import Graph, ksp_yen, quick_shortest
#note: a little error in ksp_dp
#from ksp_dp import Graph, ksp_yen

cutlist = " .[。，,！……!《》<>\"':：？\?、\|“”‘’；]{}（）{}【】()｛｝（）：？！。，;、~——+％%`:“”＂'‘\n\r"
if not isinstance(cutlist, unicode):
    try:
        cutlist = cutlist.decode('utf-8')
    except UnicodeDecodeError:
        cutlist = cutlist.decode('gbk','ignore')
cutlist_dict = {}
for c in list(cutlist):
    cutlist_dict[c] = True
def cut_to_sentence(line):
    str = ''
    for c in line:
        if cutlist_dict.has_key(c):
            yield str
            str = ''
        else:
            str += c
    if str != '':
        yield str

#base_class
class BaseCuttor(object):
    def __init__(self):
        self.WORD_MAX = 8
        self.topk = 1
        self.__best_path = self.__cut_graph_simple

    def exist(self, term):
        pass
    def get_prob(self, term):
        pass

    def set_topk(self, topk):
        self.topk = topk
        if topk > 1:
            self.__best_path = self.__cut_graph_topk
        else:
            self.__best_path = self.__cut_graph_simple

    def get_graph(self, sentence):
        n = len(sentence)
        i,j = 0,0
        graph = Graph(n+1)
        while i < n:
            for j in xrange(i, min(n,i+self.WORD_MAX), 1):
                if self.exist(sentence[i:j+1]):
                    graph.add_edge(i,j+1,0-self.get_prob(sentence[i:j+1]))
            i += 1
            j = i
        return graph

    def __cut_graph_simple(self, sentence, graph):
        (_, path) = quick_shortest(graph)
        return path

    def choise_best(self, sentence, graph, items):
        return items[0]['path']

    def __cut_graph_topk(self, sentence, graph):
        items = ksp_yen(graph, 0, graph.N-1, self.topk)
        return self.choise_best(sentence, graph, items)
    
    def __cut_graph(self, sentence):
        graph = self.get_graph(sentence)
        path = self.__best_path(sentence, graph)
        
        for i in xrange(1, len(path), 1):
            yield sentence[path[i-1]:path[i]]

    def cut_topk(self, sentence, topk):
        if not isinstance(sentence, unicode):
            try:
                sentence = sentence.decode('utf-8')
            except UnicodeDecodeError:
                sentence = sentence.decode('gbk','ignore')

        graph = self.get_graph(sentence)
        items = ksp_yen(graph, 0, graph.N-1, topk)

        for item in items:
            words = []
            path = item['path']
            for i in xrange(1, len(path), 1):
                words.append(sentence[path[i-1]:path[i]])
            yield words

    def cut(self, sentence):
        if not isinstance(sentence, unicode):
            try:
                sentence = sentence.decode('utf-8')
            except UnicodeDecodeError:
                sentence = sentence.decode('gbk','ignore')
        seg_list =  self.__cut_graph(sentence)
        for seg in seg_list:
            print seg

class FileCuttor(BaseCuttor):
    
    def __init__(self, filename):
        super(FileCuttor, self).__init__()
        
        self.set_topk(3)
        self.freq = collections.defaultdict(int)
        self.total = 0

        with codecs.open(filename, "r", "utf-8") as file:
            for line in file:
                tokens = line.split(" ")
                term = tokens[0].strip()
                if len(tokens) >= 2:
                    freq = int(tokens[1].strip())
                    self.freq[term] = freq
                    self.total += freq
        self.freq = dict([(k,math.log(float(v)/self.total)) for k,v in self.freq.iteritems()]) #normalize
        #self._log = lambda x: float('-inf') if not x else math.log(x)
        #self._prob = lambda x: self.freq[x] if x in self.freq else 0 if len(x)>1 else 1

    def exist(self, term):
        return (term in self.freq)

    def get_prob(self, term):
        #return self._log(self._prob(sentence[idx:x+1])/self.total)
        return self.freq.get(term, 0.0)

str = '唐成功成回家'
cuttor = FileCuttor('dict.txt')
seglist = cuttor.cut_topk(str, 3)
for seg in seglist:
    print ','.join(seg)

#for s in cut_to_sentence(str.decode('utf8')):
#    print s
