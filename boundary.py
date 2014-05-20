from Corpus.CorpusReader import CorpusReader
from Corpus.BoundaryDetector import BoundaryDetector
import ConfigParser
from nltk.corpus import stopwords
from os import listdir
from os.path import isfile, join
from nltk import word_tokenize
CONFIG_PATH = "config.ini"

def filter_names(name_set) :
    ''' From the list of names, remove the names which are stopwords '''
    def remove_stopwords(tup) :
        l = list(tup)
        while len(l) > 0 :
            if l[0].lower() in stopwords.words('english') :
                l.pop(0)
            else :
                break
        while len(l) > 0 :
            index = len(l) - 1
            if l[index].lower() in stopwords.words('english') :
                l.pop(index)
            else :
                break
        return l

    names = [remove_stopwords(n) for n in name_set]
    names = [n for n in names if len(n) > 0]
    return names

def extract_names():
    ''' returns a dictionary mapping proper names to their contexts in the
    corpus '''
    names = dict() # map name entity to list of contexts
    while corpus.has_next() :
        doc = corpus.get_next()
        # tuple => freq
        extracted = boundary.extract_ne_from_document(doc) #set
        extracted = filter_names(extracted)
        for name in extracted :
            name = tuple(name)
            if not names.has_key(name) :
                names[name] = []
            names[name].extend(doc.get_context(name)) # 2-gram in front and back, as a 2-ple of tuples
    return names


cfg = ConfigParser.ConfigParser()
cfg.read(CONFIG_PATH)
corpus_dir = cfg.get("Settings", "CorpusDir")
corpus = CorpusReader(corpus_dir)
boundary = BoundaryDetector(CONFIG_PATH, corpus_dir)

names = extract_names()
print names
corpus.reset()

