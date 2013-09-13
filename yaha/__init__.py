# -*- coding=utf-8 -*-
import sys, os.path, codecs, re, math
import collections
import threading
import tempfile
import random
import cPickle as pickle
import time

# ksp_dijkstra for default
from ksp_dijkstra import Graph, ksp_yen, quick_shortest
#note: a little error in ksp_dp
#from ksp_dp import Graph, ksp_yen

DICT_LOCK = threading.RLock()
DICT_INIT = False
class DICTS:
    LEN = 7
    MAIN,SURNAME,SUFFIX,EXT_STOPWORD,STOPWORD,QUANTIFIER,STOP_SENTENCE = range(7)
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

    def iteritems(self):
        return self._data.iteritems()
    
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

def __get_sentence_dict():
    cutlist = " .[。，,！……!《》<>\"':：？\?、\|“”‘’；]{}（）{}【】()｛｝（）：？！。，;、~——+％%`:“”＂'‘\n\r"
    if not isinstance(cutlist, unicode):
        try:
            cutlist = cutlist.decode('utf-8')
        except UnicodeDecodeError:
            cutlist = cutlist.decode('gbk','ignore')
    cutlist_dict = {}
    for c in list(cutlist):
        word = WordBase()
        cutlist_dict[c] = word
    return cutlist_dict

# TODO do it better Only use installed=False in google app
# Not temp_file support in GAE
installed = True
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
        t1 = time.time()
        curpath = os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) )  )
        tmp_file = ''
        if installed:
            tmp_file = os.path.join(tempfile.gettempdir(), "yaha.cache")
        else:
            tmp_file = os.path.join(curpath,'dict','yaha.cache')
            print tmp_file
        load_ok = True

        # Use pickle to load dict
        if installed:
            if os.path.exists(tmp_file):
                tmp_file_time = os.path.getmtime(tmp_file)
                for p in DICTS.DEFAULT:
                    if tmp_file_time < os.path.getmtime(os.path.join(curpath, 'dict', p)):
                        load_ok = False
                        break
                if load_ok:
                    try:
                        DICTS.DEFAULT_DICT = pickle.load(open(tmp_file, 'rb'))
                        print >> sys.stderr, 'Load dict from: ' + tmp_file
                    except:
                        DICTS.DEFUALT_DICT = []
                        load_ok = False
            else:
                load_ok = False
        else:
            try:
                DICTS.DEFAULT_DICT = pickle.load(open(tmp_file, 'rb'))
                print >> sys.stderr, 'Load dict from: ' + tmp_file
            except:
                print >> sys.stderr, 'Error load dict from: ' + tmp_file
                DICTS.DEFUALT_DICT = []
                load_ok = False

        if not load_ok:
            for i in xrange(0, DICTS.LEN-1, 1):
                new_dict = DictBase()
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

            # The sentence_dict is alwayse at last
            DICTS.DEFAULT_DICT.append(__get_sentence_dict())
            
            if installed:
                # save to tempfile
                tmp_file = os.path.join(tempfile.gettempdir(), "yaha.cache")
                print >> sys.stderr, 'save dicts to tmp_file: ' + tmp_file
                try:
                    tmp_suffix = "."+str(random.random())
                    with open(tmp_file+tmp_suffix,'wb') as temp_cache_file:
                        pickle.dump(DICTS.DEFAULT_DICT, temp_cache_file, protocol=pickle.HIGHEST_PROTOCOL)
                    if os.name=='nt':
                        import shutil
                        replace_file = shutil.move
                    else:
                        replace_file = os.rename
                    replace_file(tmp_file + tmp_suffix, tmp_file)
                except:
                    print >> sys.stderr, "dump temp file failed."
                    import traceback
                    print >> sys.stderr, traceback.format_exc()

        print >> sys.stderr, 'End load dict ', time.time() - t1, "seconds."
        DICT_INIT = True

    return DICTS.DEFAULT_DICT[type]

class CuttingBase(object):
    def __init__(self):
        self.stage = -1

    #def cut_stage1(self, cuttor, sentence):
    #    pass
    #def cut_stage2(self, cuttor, sentence, graph):
    #    pass
    #def cut_stage3(self, cuttor, sentence, graph, start, end):
    #    pass
    #def cut_stage4(self, sentence, graph, contex):
    #    pass

class RegexCutting(CuttingBase):
    # Not surpport stage 1 now
    def __init__(self, rex, stage=2):
        super(CuttingBase, self).__init__()
        self.stage = 2
        #self.cut_stage2 = self.cut_regex
        self.rex = rex

    def cut_stage2(self, cuttor, sentence, graph):
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
            #print 'surname', klen, sentence[path[i-1]:path[i]]
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
                        i += 2
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
        
        #print 'suffix', i, sentence[path[i-1]:path[i]]

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
        #self.WORD_MAX = 8
        # Use 6 is better, but it will not cut the word longer than 5
        self.WORD_MAX = 6
        self.refer_prob = 15.0
        self.default_prob = 150.0
        self.topk = 1
        self.__best_path = self.__cut_graph_simple
        self.stages = []
        self.stages.append([])
        self.stages.append([])
        self.stages.append([])
        self.stages.append([])
        self.sentence_dict = get_dict(DICTS.STOP_SENTENCE)
        self.stage1_regex = None
        self.fn_stage1 = self.__stage1_null

    def exist(self, term):
        pass
    def get_prob(self, term):
        pass
    def word_type(self, term, type):
        return False

    def cut_to_sentence(self, line):
        if not isinstance(line, unicode):
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError:
                line = line.decode('gbk','ignore')
        for s,need_cut in self.fn_stage1(line):
            if need_cut:
                if s != '':
                    str = ''
                    for c in s:
                        if self.sentence_dict.has_key(c):
                            if str != '':
                                yield (str, True)
                            str = ''
                            yield (c, False)
                        else:
                            str += c
                    if str != '':
                        yield (str, True)
            else:
                yield (s, False)

    # Only support one regex for stage1 now
    def set_stage1_regex(self, rex):
        if type(rex) == str:
            self.stage1_regex = re.compile(rex, re.I|re.U)
        else:
            self.stage1_regex = rex
        self.fn_stage1 = self.__do_stage1

    def __stage1_null(self, sentence):
        yield (sentence, True)

    def __do_stage1(self, sentence):
        start = 0
        for m in self.stage1_regex.finditer(sentence):
            yield (sentence[start:m.start(0)], True)
            yield (sentence[m.start(0):m.end(0)], False)
            start = m.end(0)
        yield (sentence[start:], True)

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

    def __new_path(self, sentence, graph, contex):
        path = contex['path']
        # stage4
        index = 1
        n_path = len(path)
        #print item['path']
        while index < n_path:
            i = index
            for stage in self.stages[3]:
                i = stage.cut_stage4(self, sentence, graph, contex)
                if i >= n_path:
                    break
                #print 'index', i
                contex['index'] = i
            if i >= n_path:
                break
            if path[i]-path[i-1] == 1:
                contex['single'] += 1
            contex['new_path'].append(path[i])
            index = i+1
            contex['index'] = index

    def __cut_graph_simple(self, sentence, graph):
        (_, path) = quick_shortest(graph)
        contex = {'path':path,'new_path':[0], 'single':0, 'index':1}
        self.__new_path(sentence, graph, contex=contex)
        return contex['new_path']

    def choise_best(self, sentence, graph, items):
        paths = []
        for item in items:
            path = item['path']
            contex = {'path':path,'new_path':[0], 'single':0, 'index':1}
            self.__new_path(sentence, graph, contex=contex)
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

    def __cut_all(self, sentence):
        graph = self.get_graph(sentence)

        old_j = -1
        for k,v in graph.iteritems():
            if len(v) == 1 and k > old_j:
                yield sentence[k:k+1]
            else:
                for j,_p in v.iteritems():
                    if j > k+1:
                        yield sentence[k:j]
                        old_j = j-1

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
        for s,need_cut in self.cut_to_sentence(sentence):
            if s == '':
                continue
            elif need_cut:
                for word in self.__cut_graph(s):
                    yield word
            else:
                yield s

    def cut_all(self, sentence):
        for s,need_cut in self.cut_to_sentence(sentence):
            if s == '':
                continue
            elif need_cut:
                for word in self.__cut_all(s):
                    yield word
            else:
                yield s
    
    def tokenize(self, unicode_sentence, search = False):
        if not isinstance(unicode_sentence, unicode):
            raise Exception("Yaha: the input parameter should be unicode.")
        start = 0
        if search:
            for term in self.cut(unicode_sentence):
                width = len(term)
                if width > 2:
                    for i in xrange(width - 1):
                        gram2 = term[i:i+2]
                        if self.exist(gram2):
                            yield (gram2,start+i,start+i+2)
                if width > 3:
                    for i in xrange(width - 2):
                        gram3 = term[i:i+3]
                        if self.exist(gram3):
                            yield (gram3, start+i, start+i+3)
                yield (term, start, start+width)
                start += width
        else:
            for term in self.cut(unicode_sentence):
                width = len(term)
                yield (term, start, start+width)
                start += width

class Cuttor(BaseCuttor):
    
    def __init__(self):
        super(Cuttor, self).__init__()
        
        #self.set_topk(3)
        self.dict = get_dict(DICTS.MAIN)

        self.refer_prob =  (0-math.log(3.0/self.dict.total))
        self.default_prob = 10.0*self.refer_prob

    def exist(self, term):
        word = self.dict[term]
        if word and word.base_freq > 0:
            return True
        return False
    
    def word_type(self, term, type):
        word = self.dict[term]
        if word:
            return (word.type.find(type)>=0)
        return False

    def get_prob(self, term):
        word = self.dict[term]
        if word:
            return word.base_ps
        else:
            return (0-self.default_prob)

    def get_freq(self, term):
        word = self.dict[term]
        if word:
            return word.base_freq
        else:
            return 0

