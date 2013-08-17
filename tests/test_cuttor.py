# -*- coding=utf-8 -*-

from yaha import Cuttor

str = '唐成真是唐成是个唐成'
cuttor = Cuttor()

#cuttor.add_regex(re.compile('\d+', re.I|re.U))
#surname = SurnameCutting()
#cuttor.add_stage(surname)
surname = SurnameCutting2()
cuttor.add_stage(surname)

seglist = cuttor.cut(str)
print ','.join(list(seglist))
#seglist = cuttor.cut_topk(str, 3)
#for seg in seglist:
#    print ','.join(seg)

#for s in cut_to_sentence(str.decode('utf8')):
#    print s
