# -*- coding=utf-8 -*-
import sys, os.path, codecs, re, math
import collections
import threading

# ksp_dijkstra for default
from ksp_dijkstra import Graph, ksp_yen, quick_shortest
#note: a little error in ksp_dp
#from ksp_dp import Graph, ksp_yen

DICT_LOCK = threading.RLock()
DICT_INIT = False
class DICTS:
    LEN = 6
    MAIN,SURNAME,SUFFIX,EXT_STOPWORD,STOPWORD,QUANTIFIER = range(6)
    MAIN_DICT = {}
    SURNAME_DICT = {}
    DEFAULT = ['dict.dic', 'surname.dic', 'suffix.dic', 'ext_stopword.dic','stopword.dic', 'quantifier.dic']
    DEFAULT_DICT = []

class WordBase(object):
    def __init__(self):
        self.base_freq = 0
        self.base_ps = 0.0
        self.type = ''

class DictBase(object):
    def __init__(self):
        self._data = {}
        self.total = 0

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return (self._data)

    def __getitem__(self, node):
        if self._data.has_key(node):
            return self._data[node]
        else:
            return None
    
    def __iter__(self):
        return self._data.__iter__()
    
    def add_term(self, term, word):
        self._data[term] = word
        self.total += word.base_freq

    def normalize(self):
        #ignore which the total is zero
        if self.total == 0:
            return
        for term, word in self._data.iteritems():
            word.base_ps = math.log(float(word.base_freq)/self.total)

    def has_key(self, term):
        return self._data.has_key(term)

def get_dict(type):
    global DICT_INIT
    if type < 0 or type >= DICTS.LEN:
        return {}
    if DICT_INIT:
        return DICTS.DEFAULT_DICT[type]
    with DICT_LOCK:
        if DICT_INIT:
            return DICTS.DEFAULT_DICT[type]
        
        print >> sys.stderr, 'Start load dict...'
        for i in xrange(0, DICTS.LEN, 1):
            new_dict = DictBase()
            curpath = os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) )  )
            with codecs.open(os.path.join(curpath, 'dict', DICTS.DEFAULT[i]), "r", "utf-8") as file:
                for line in file:
                    tokens = line.split(" ")
                    term = tokens[0].strip()
                    word = WordBase()
                    if len(tokens) >= 2:
                        word.base_freq = int(tokens[1].strip())
                    if len(tokens) >= 3:
                        word.type = tokens[2].strip()
                    new_dict.add_term(term, word)
            new_dict.normalize()
            DICTS.DEFAULT_DICT.append(new_dict)
            DICT_INIT = True
        print >> sys.stderr, 'End load dict.'

    return DICTS.DEFAULT_DICT[type]

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

class CuttingBase(object):
    def __init__(self):
        self.stage = -1

    #def cut_stage1(self, cuttor, sentence, graph):
    #    pass
    #def cut_stage2(self, cuttor, sentence, graph):
    #    pass
    #def cut_stage3(self, cuttor, sentence, graph, start, end):
    #    pass
    #def cut_stage4(self, sentence, graph, contex):
    #    pass

class RegexCutting(CuttingBase):
    def __init__(self, rex, stage):
        super(CuttingBase, self).__init__()
        if stage == 1:
            self.stage = 1
            # TODO
        else:
            self.stage = 2
            self.cut_stage2 = self.cut_regex
        self.rex = rex

    def cut_regex(self, cuttor, sentence, graph):
        for m in self.rex.finditer(sentence):
            graph.add_edge(m.start(0),m.end(0), cuttor.default_prob)

class SurnameCutting(CuttingBase):
    def __init__(self):
        super(CuttingBase, self).__init__()
        self.stage = 3
        self.dict = get_dict(DICTS.SURNAME)

    def cut_stage3(self, cuttor, sentence, graph, start, end):
        klen = end-start
        if klen > 4:
            return

        if klen >= 2 and self.dict.has_key(sentence[start:start+1]):
            # TODO for this prob
            graph.add_edge(start,start+2, cuttor.refer_prob*0.8)
        if klen > 2 and self.dict.has_key(sentence[start:start+1]):
            graph.add_edge(start,start+3, cuttor.refer_prob*1.2)
        if klen > 2 and self.dict.has_key(sentence[start:start+2]):
            graph.add_edge(start,start+3, cuttor.refer_prob*1.2)
        if klen > 3 and self.dict.has_key(sentence[start:start+2]):
            graph.add_edge(start,start+4, cuttor.refer_prob*1.5)

class SurnameCutting2(CuttingBase):
    def __init__(self):
        super(CuttingBase, self).__init__()
        self.stage = 4
        self.dict = get_dict(DICTS.SURNAME)
        self.stop_dict = get_dict(DICTS.EXT_STOPWORD)
        
    def cut_stage4(self, cuttor, sentence, graph, contex):
        start = contex['index']
        path = contex['path']
        new_path = contex['new_path']
        n = len(path)
        i = start
        while i < n:
            klen = path[i]-path[i-1]
            if klen >= 1 and klen <= 2 and self.dict.has_key(sentence[path[i-1]:path[i]]):
                if i < n-2:
                    klen2 = path[i+1]-path[i]
                    klen3 = path[i+2]-path[i+1]
                    if klen2==1 and klen3==1 and not self.stop_dict.has_key(sentence[path[i+1]:path[i+2]]):
                        #get one name
                        new_path.append(path[i+2])
                        i += 3
                        continue
                    if klen2==1:
                        new_path.append(path[i+1])
                        i += 2
                    if klen2==2:
                        new_path.append(path[i+1])
                        i += 3
                        continue
                elif i < n-1:
                    klen2 = path[i+1]-path[i]
                    if klen2 <= 2 and klen2 >=1:
                        new_path.append(path[i+1])
                        i = path[i+1]
                        i += 2
                        continue
                else:
                    return i
            else:
                #next stage to doit
                return i
        return i

class SuffixCutting(CuttingBase):
    def __init__(self):
        super(CuttingBase, self).__init__()
        self.stage = 4
        self.dict = get_dict(DICTS.SUFFIX)
        self.stop_dict = get_dict(DICTS.EXT_STOPWORD)
    
    def cut_stage4(self, cuttor, sentence, graph, contex):
        start = contex['index']
        path = contex['path']
        new_path = contex['new_path']
        n = len(path)
        n2 = len(new_path)
        i = start
        modify = False

        klen = path[i]-path[i-1]
        if klen >= 1 and klen <= 2 and n2 > 2 and self.dict.has_key(sentence[path[i-1]:path[i]]):
            j = n2-1
            while j > 1:
                klen2 = new_path[j]-new_path[j-1]
                if klen2 == 1 and not self.stop_dict.has_key(sentence[new_path[j-1]:new_path[j]]):
                    new_path.pop()
                    contex['single'] -= 1
                    modify = True
                    j -= 1
                    continue
                if klen2 > 1 and cuttor.word_type(sentence[new_path[j-1]:new_path[j]], 'n'):
                    new_path.pop()
                    modify = True
                break
        if modify:
            new_path.append(path[i])
            return i+1
        else:
            return i

#base_class
class BaseCuttor(object):
    def __init__(self):
        self.WORD_MAX = 8
        self.refer_prob = 15.0
        self.default_prob = 150.0
        self.topk = 1
        self.__best_path = self.__cut_graph_simple
        self.stages = []
        self.stages.append([])
        self.stages.append([])
        self.stages.append([])
        self.stages.append([])

    def exist(self, term):
        pass
    def get_prob(self, term):
        pass
    def word_type(self, term, type):
        return False

    def add_regex(self, rex, stage=2):
        self.add_stage(RegexCutting(rex, stage))

    def add_stage(self, obj, stage=-1):
        new_stage = stage
        if new_stage == -1:
            new_stage = obj.stage
        if new_stage < 1 or new_stage > 4:
            return
        self.stages[new_stage-1].append(obj)

    def set_topk(self, topk):
        self.topk = topk
        if topk > 1:
            self.__best_path = self.__cut_graph_topk
        else:
            self.__best_path = self.__cut_graph_simple

    def get_graph(self, sentence):
        n = len(sentence)
        i,j = 0,0
        graph = Graph(n+1, self.default_prob)

        # stage2
        for stage in self.stages[1]:
            stage.cut_stage2(self, sentence, graph)

        while i < n:
            for j in xrange(i, min(n,i+self.WORD_MAX), 1):
                if self.exist(sentence[i:j+1]):
                    graph.add_edge(i,j+1,0-self.get_prob(sentence[i:j+1]))
                else:
                    # stage3
                    for stage in self.stages[2]:
                        stage.cut_stage3(self, sentence, graph, i, j+1)
            i += 1
            j = i
        return graph

    def __cut_graph_simple(self, sentence, graph):
        (_, path) = quick_shortest(graph)
        return path

    def choise_best(self, sentence, graph, items):
        paths = []
        for item in items:
            contex = {'path':item['path'],'new_path':[0], 'single':0, 'index':1}

            # stage4
            index = 1
            while index < len(item['path']):
                i = index
                for stage in self.stages[3]:
                    i = stage.cut_stage4(self, sentence, graph, contex)
                if i == index:
                    path = contex['path']
                    if path[i]-path[i-1] == 1:
                        contex['single'] += 1
                    contex['new_path'].append(path[i])
                    index += 1
                else:
                    index = i
                contex['index'] = index
            paths.append(contex)
            break
        sorted(paths, key=lambda p:p['single'])
        return paths[0]['new_path']

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
        return self.__cut_graph(sentence)

class Cuttor(BaseCuttor):
    
    def __init__(self):
        super(Cuttor, self).__init__()
        
        self.set_topk(3)
        self.dict = get_dict(DICTS.MAIN)

        self.refer_prob =  (0-math.log(3.0/self.dict.total))
        self.default_prob = 10.0*self.refer_prob

    def exist(self, term):
        return (term in self.dict)
    
    def word_type(self, term, type):
        word = self.dict[term]
        return (word.type.find(type)>=0)

    def get_prob(self, term):
        word = self.dict[term]
        if word:
            return word.base_ps
        else:
            return (0-self.default_prob)

