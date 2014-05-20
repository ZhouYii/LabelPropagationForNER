from os import listdir
import re, nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from os.path import isfile, join
from helper import *

def pass_filters(tok) :
    filters = [lambda w : w in stopwords.words('english'),  #Ignore stopwords
                lambda w : len(w) == 0,                     #Empty Token
                lambda w : w == '``' or w == "''"]          #Another form of empty token
#                lambda w : len(w) == 1 and not str.isalnum(w[0])] #Single punctuation tokens
    for test in filters :
        if test(tok) :
            return False
    return True

def split_to_clause(tok_seq) :
    ''' Main strategy is to consider the commas as start/end of a new clause '''
    if tok_seq.count(',') == 0 :
        return [tok_seq]
    comma_index = tok_seq.index(',')
    lbound = min(len(tok_seq), comma_index+1)
    if tok_seq.count(',') == 1 :
        # A, B
        return [seq for seq in [tok_seq[:comma_index], tok_seq[lbound:]] \
                    if len(seq) > 0]
    #A,B,C,D,E ...
    recurse = split_to_clause(tok_seq[lbound:])
    ret = [tok_seq[:comma_index]]
    ret.extend(recurse)
    return ret

def lemmatize(tok_list) :
    lemma = nltk.WordNetLemmatizer()

class Document :
    #Static alloc
    sent_chunker = nltk.data.load('tokenizers/punkt/english.pickle')
    def __init__(self, filepath) :
        f = open(filepath, "r")
        self.text = f.read().strip()
        #Split sentences and remove terminating punctuation
        self.sentences = [s[:len(s)-1] for s in Document.sent_chunker.tokenize(self.text)]
        self.clause_list = self.get_clauses()
        self.build_index(self.clause_list)
        f.close()

    def build_index(self, tok_list_seq) :
        ''' Builds the index, taking a list of token sequences. Indicies are
        unique : (clause_list_index, token_index)'''
        self.index = dict()
        for i in range(0, len(tok_list_seq)) :
            tokens = tok_list_seq[i]
            for j in range(0, len(tokens)) :
                index = (i,j)
                token = tokens[j]
                if not self.index.has_key(token) :
                    self.index[token] = list()
                self.index[token].append(index)

    def get_clauses(self) :
        clause_list = []
        for sentence in self.sentences:
            #tok_list = lemmatize(word_tokenize(sentence))
            tok_list = word_tokenize(sentence)
            tok_list = [w for w in tok_list if pass_filters(w)]
            clauses = split_to_clause(tok_list)
            clause_list.extend(clauses)
        return clause_list

    def get_token(self, clause_index, position_index) :
        ''' Returns a list, which allows easilly handling a non-existent index
        by list extension '''
        if clause_index in range(0, len(self.clause_list)) :
            clause = self.clause_list[clause_index]
            #print str(clause) + " " + str(len(clause)) + " " + str(position_index)
            if position_index in range(0, len(clause)) :
                return [clause[position_index]]
        return []

    def find_indicies(self, tokens) :
        ''' Find a list of starting indicies for the token list within this
        document '''
        if len(tokens) == 0 or not self.index.has_key(tokens[0]) :
            return []
        candidates = set(self.index[tokens[0]])
        for i in range(1, len(tokens)) :
            next_indicies = self.index[tokens[i]]
            candidates = candidates.intersection(set(next_indicies))
        return list(candidates)


    def get_context(self, tokens, size=2) :
        ret = []
        indicies = self.find_indicies(list(tokens))
        print "tokens:"+str(tokens)
        print "indicies:"+str(indicies)
        for index in indicies :
            fwd, rev = [], []
            print "index:"+str(index)
            doc_id, pos = index[0], index[1]
            print self.clause_list[doc_id][pos]
            for offset in range(0,size) :
                print self.get_token(doc_id, pos+len(tokens)+offset)
                fwd.extend(self.get_token(doc_id, pos+len(tokens)+offset))
                rev.extend(self.get_token(doc_id, pos-offset))
            ret.append( (fwd, rev) )
        return ret
