# -*- coding=utf-8 -*-
import sys, re
from yaha import Cuttor, RegexCutting, SurnameCutting2, SuffixCutting

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

seglist = cuttor.cut(str)
print '\nCut with name \n%s\n' % ','.join(list(seglist))

#seglist = cuttor.cut_topk(str, 3)
#for seg in seglist:
#    print ','.join(seg)

#for s in cuttor.cut_to_sentence(str):
#    print s

str = "伟大祖国是中华人民共和国"

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
