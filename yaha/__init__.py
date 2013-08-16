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

class CuttingBase(object):
    def __init__(self):
        self.do_stage1 = False
        self.do_stage2 = False
        self.do_stage3 = False
        self.do_stage4 = False

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
            self.do_stage1 = True
            # TODO
        else:
            self.do_stage2 = True
            self.cut_stage2 = self.cut_regex
        self.rex = rex

    def cut_regex(self, cuttor, sentence, graph):
        for m in self.rex.finditer(sentence):
            graph.add_edge(m.start(0),m.end(0), cuttor.default_prob)

class SurnameCutting(CuttingBase):
    def __init__(self, dict_file):
        super(CuttingBase, self).__init__()
        self.do_stage3 = True
        self.dict = {}
        
        with codecs.open(dict_file, "r", "utf-8") as file:
            for line in file:
                self.dict[line.strip()] = True

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
    def __init__(self, dict_file):
        super(CuttingBase, self).__init__()
        self.do_stage4 = True
        self.dict = {}
        
        with codecs.open(dict_file, "r", "utf-8") as file:
            for line in file:
                self.dict[line.strip()] = True

    def cut_stage4(self, cuttor, sentence, graph, contex):
        start = contex['index']
        path = contex['path']
        new_path = contex['new_path']
        n = len(path)
        i = start
        while i < n:
            klen = path[i]-path[i-1]
            print i, klen
            if klen >= 1 and klen <= 2 and self.dict.has_key(sentence[path[i-1]:path[i]]):
                print 'has_key', sentence[path[i-1]:path[i]]
                if i < n-2:
                    klen2 = path[i+1]-path[i]
                    klen3 = path[i+2]-path[i+1]
                    if klen2==1 and klen3==1:
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

    def add_regex(self, rex, stage=2):
        self.add_stage(RegexCutting(rex, stage), stage)

    def add_stage(self, obj, stage):
        if stage < 1 or stage > 4:
            return
        self.stages[stage-1].append(obj)

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
            stage_iter = iter(self.stages[3])
            index = 1
            while index < len(item['path']):
                i = index
                for stage in stage_iter:
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
            print contex
            paths.append(contex)
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

        self.refer_prob =  (0-math.log(3.0/self.total))
        self.default_prob = 10.0*self.refer_prob

        #self._log = lambda x: float('-inf') if not x else math.log(x)
        #self._prob = lambda x: self.freq[x] if x in self.freq else 0 if len(x)>1 else 1

    def exist(self, term):
        return (term in self.freq)

    def get_prob(self, term):
        #return self._log(self._prob(sentence[idx:x+1])/self.total)
        return self.freq.get(term, 0.0)

str = '唐成真是个好人'
cuttor = FileCuttor('dict.txt')

#cuttor.add_regex(re.compile('\d+', re.I|re.U))
#surname = SurnameCutting('dict/surname.dic')
#cuttor.add_stage(surname, 3)
surname = SurnameCutting2('dict/surname.dic')
cuttor.add_stage(surname, 4)

seglist = cuttor.cut(str)
print ','.join(list(seglist))
#seglist = cuttor.cut_topk(str, 3)
#for seg in seglist:
#    print ','.join(seg)

#for s in cut_to_sentence(str.decode('utf8')):
#    print s
