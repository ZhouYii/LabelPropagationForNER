from BoundaryDetector import BoundaryDetector
from document import Document
from os.path import isfile, join
from os import listdir

class CorpusReader :
    def __init__(self, corpus_path) :
        if corpus_path == None :
            return
        self.path = corpus_path
        self.read_head = 0

    def get_docs_list(self) :
        files= [join(self.path,f) for f in listdir(self.path) \
                    if isfile(join(self.path, f))]
        return files

    def init_boundary_detector(self, config_path) :
        self.boundary_detector = BoundaryDetector(config_path, path=self.path)

    def get_next(self) :
        ''' Gets the next file in the corpus in the Document format '''
        filepath = self.get_docs_list()[self.read_head]
        self.read_head += 1
        doc = Document(filepath)
        return doc

    def has_next(self) :
        return self.read_head < len(self.get_docs_list())

    def reset(self) :
        self.read_head = 0


