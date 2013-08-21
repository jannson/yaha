# -*- coding: UTF-8 -*-
import sys, os, os.path
import codecs
from django.utils.encoding import force_unicode
from django.db.models import Count

import yaha
from yaha.analyse import ChineseAnalyzer 

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

try:
    import whoosh
except ImportError:
    raise MissingDependency("The 'whoosh' backend requires the installation of 'Whoosh'. Please refer to the documentation.")

# Bubble up the correct error.
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, IDLIST, STORED, TEXT, KEYWORD, NUMERIC, BOOLEAN, DATETIME, NGRAM, NGRAMWORDS
from whoosh.fields import ID as WHOOSH_ID
from whoosh import index, query, sorting, scoring
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.filedb.filestore import FileStorage, RamStorage
from whoosh.searching import ResultsPage
from whoosh.writing import AsyncWriter

def _from_python(value):
    """
    Converts Python values to a string for Whoosh.

    Code courtesy of pysolr.
    """
    if hasattr(value, 'strftime'):
        if not hasattr(value, 'hour'):
            value = datetime(value.year, value.month, value.day, 0, 0, 0)
    elif isinstance(value, bool):
        if value:
            value = 'true'
        else:
            value = 'false'
    elif isinstance(value, (list, tuple)):
        value = u','.join([force_unicode(v) for v in value])
    elif isinstance(value, (int, long, float)):
        # Leave it alone.
        pass
    else:
        value = force_unicode(value)
    return value

use_file_storage = True
storage = None
key_path = 'key_index'
if use_file_storage and not os.path.exists(key_path):
    os.mkdir(key_path)
storage = FileStorage(key_path)
index_fieldname = 'content'
schema_fields = {
        'id': WHOOSH_ID(stored=True, unique=True),
}
schema_fields[index_fieldname] = TEXT(stored=True, analyzer=ChineseAnalyzer())
schema = Schema(**schema_fields)

accepted_chars = re.compile(ur"[\u4E00-\u9FA5]+", re.UNICODE)
accepted_line = re.compile(ur"\d+-\d+-\d+")

def get_content(filename):
    accepted_line = re.compile(ur"\d+-\d+-\d+")
    file = codecs.open(filename, 'r', 'utf-8')
    content = ''
    names = []
    drop = 0
    for line in file.readlines():
        if accepted_line.match(line):
            line_names = accepted_chars.findall(line)
            for l_n in line_names:
                if l_n not in names:
                    names.append(l_n)
        else:
            drop += 1
            if drop % 8 == 0:
                content += line
    file.close()
    return (content, names)

def add_doc():
    index = storage.open_index(schema=schema)
    writer = index.writer()
    
    #parser = QueryParser(index_fieldname, schema=schema)
    #parsed_query = parser.parse('%s:%s' % ('id', qq_id))
    #parsed_query = parser.parse('%s:%s' % ('id', qq_id))
    #writer.delete_by_query(query)
    #writer.commit()

    content,names = get_content('qq7')
    
    doc = {}
    doc['id'] = _from_python(qq_id)
    doc[index_fieldname] = content
    
    try:
        writer.add_document(**doc)
        writer.commit()
        #writer.update_document(**doc)
    except Exception, e:
        raise

def write_db():
    index = storage.create_index(schema)
    writer = index.writer()
    
    # read doc from Database by using django
    for dou in Preview.objects.all():
        doc = {}
        doc['id'] = _from_python(str(dou.id))
        text = dou.description
        doc[index_fieldname] = text
        try:
            writer.update_document(**doc)
        except Exception, e:
            raise

    #add_doc(index, writer)
    writer.commit()

def search_db():
    index = storage.open_index(schema=schema)
    searcher = index.searcher()
    parser = QueryParser(index_fieldname, schema=schema)
    parsed_query = parser.parse('%s:%s' % ('id', qq_id))
    raw_results = searcher.search(parsed_query)
    
    _,names = get_content('qq7')

    corpus_filename = 'name_qq7'
    terms = {}
    corpus_file = codecs.open(corpus_filename, "r", "utf-8")
    for line in corpus_file:
        tokens = line.split(" ")
        term = tokens[0].strip()
        frequency = int(tokens[1].strip())
        terms[term] = frequency

    n_terms = {}
    corpus_filename = 'dict.txt'
    corpus_file = codecs.open(corpus_filename, "r", "utf-8")
    for line in corpus_file:
        tokens = line.split(" ")
        term = tokens[0].strip()
        if len(tokens) >= 3 and tokens[2].find('n')>=0:
            n_terms[term] = tokens[2]
        else:
            n_terms[term] = ''
    keys = []
    for keyword, score in raw_results.key_terms(index_fieldname, docs=1000, numterms=240):
        if keyword in names:
            continue
        if terms.has_key(keyword):
            if not n_terms.has_key(keyword):
                keys.append(keyword)
            elif n_terms.has_key(keyword) and n_terms[keyword].find('n')>=0:
                keys.append(keyword)
        #keys.append(keyword)
    print ', '.join(keys)
    #print len(raw_results)
    #for result in raw_results:
    #    print result[index_fieldname]

def key_all():
    index = storage.open_index(schema=schema)
    searcher = index.searcher()
    reader = searcher.reader()
    cnt = 0
    filename = 'idf.txt'
    accepted_chars = re.compile(ur"[\u4E00-\u9FA5]+", re.UNICODE)
    file = codecs.open(filename, "w", "utf-8")
    file.write('%s\n' % reader.doc_count_all() )
    for term in reader.field_terms('content'):
    #for term in reader.most_frequent_terms('content', 100):
        if not accepted_chars.match(term):
            continue
        term_info = reader.term_info('content', term)
        file.write('%s %d %d\n' % (term, term_info.doc_frequency(), term_info.max_weight()) )
    file.close()
write_db()
add_doc()
search_db()
key_all()
