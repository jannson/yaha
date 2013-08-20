# -*- coding=utf-8 -*-
import sys
import os, codecs, re, math
import collections
import threading
from yaha import DICTS, get_dict

IDF_LOCK = threading.RLock()
def __get_idf(word):
    ;
