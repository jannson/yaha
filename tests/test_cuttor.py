# -*- coding=utf-8 -*-
import sys
from yaha import Cuttor, SurnameCutting2, SuffixCutting

str = '唐成真是唐成牛强乡是个唐成真'
cuttor = Cuttor()

#cuttor.add_regex(re.compile('\d+', re.I|re.U))
#surname = SurnameCutting()
#cuttor.add_stage(surname)

surname = SurnameCutting2()
cuttor.add_stage(surname)

suffix = SuffixCutting()
cuttor.add_stage(suffix)

seglist = cuttor.cut(str)
print ','.join(list(seglist))
#seglist = cuttor.cut_topk(str, 3)
#for seg in seglist:
#    print ','.join(seg)

#for s in cut_to_sentence(str.decode('utf8')):
#    print s
