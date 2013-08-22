# -*- coding=utf-8 -*-
import sys, re, codecs
import cProfile
from yaha import Cuttor, RegexCutting, SurnameCutting, SurnameCutting2, SuffixCutting
from yaha.wordmaker import WordDict
from yaha.analyse import extract_keywords, near_duplicate, summarize1, summarize2, summarize3

str = '唐成真是唐成牛的长寿乡是个1998love唐成真诺维斯基'
cuttor = Cuttor()

# Get 3 shortest paths for choise_best
#cuttor.set_topk(3)

# Use stage 1 to cut english and number 
cuttor.set_stage1_regex(re.compile('(\d+)|([a-zA-Z]+)', re.I|re.U))

# Or use stage 2 to cut english and number 
#cuttor.add_stage(RegexCutting(re.compile('\d+', re.I|re.U)))
#cuttor.add_stage(RegexCutting(re.compile('[a-zA-Z]+', re.I|re.U)))

# Use stage 3 to cut chinese name
#surname = SurnameCutting()
#cuttor.add_stage(surname)

# Or use stage 4 to cut chinese name
surname = SurnameCutting2()
cuttor.add_stage(surname)

# Use stage 4 to cut chinese address or english name
suffix = SuffixCutting()
cuttor.add_stage(suffix)

#seglist = cuttor.cut(str)
#print '\nCut with name \n%s\n' % ','.join(list(seglist))

#seglist = cuttor.cut_topk(str, 3)
#for seg in seglist:
#    print ','.join(seg)

#for s in cuttor.cut_to_sentence(str):
#    print s

#str = "伟大祖国是中华人民共和国"
#str = "九孔不好看来"
#str = "而迈入社会后..."
str = "工信处女干事每月经过下属科室都要亲口交代24口交换机等技术性器件的安装工作"

#You can set WORD_MAX to 8 for better match
#cuttor.WORD_MAX = 8

#Normal cut
seglist = cuttor.cut(str)
print 'Normal cut \n%s\n' % ','.join(list(seglist))

#All cut
seglist = cuttor.cut_all(str)
print 'All cut \n%s\n' % ','.join(list(seglist))

#Tokenize for search
print 'Cut for search (term,start,end)'
for term, start, end in cuttor.tokenize(str.decode('utf-8'), search=True):
    print term, start, end

re_line = re.compile("\W+|[a-zA-Z0-9]+", re.UNICODE)
def sentence_from_file(filename):
    with codecs.open(filename, 'r', 'utf-8') as file:
        for line in file:
            for sentence in re_line.split(line):
                yield sentence

def make_new_word(file_from, file_save):
    word_dict = WordDict()
    #word_dict.add_user_dict('www_qq0')
    for sentence in sentence_from_file(file_from):
        word_dict.learn(sentence)
    word_dict.learn_flush()
    
    str = '我们的读书会也顺利举办了四期'
    seg_list = word_dict.cut(str)
    print ', '.join(seg_list)

    word_dict.save_to_file(file_save)

#最大熵算法得到新词
#def test():
#   make_new_word('qq0', 'www_qq0')
#cProfile.run('test()')
#test()

#test: Get key words from file
def key_word_test():
    filename = 'key_test.txt'
    with codecs.open(filename, 'r', 'utf-8') as file:
        content = file.read()
        keys = extract_keywords(content)
        #print ','.join(keys)
        print summarize1(content)
        print summarize2(content)
        print summarize3(content)
#key_word_test()

#比较文本的相似度
def compare_file():
    file1 = codecs.open('f1.txt', 'r', 'utf-8')
    file2 = codecs.open('f2.txt', 'r', 'utf-8')
    print 'the near of two files is:', near_duplicate(file1.read(), file2.read())
#compare_file()
