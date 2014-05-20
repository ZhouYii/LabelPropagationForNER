from helper import *
import ConfigParser
from os import listdir
from nltk.corpus import stopwords
from os.path import isfile, join
from document import Document
import copy

cfg, memoize = None, dict()
def strip_noise_tokens(tok_seq) :
    while len(tok_seq) > 0 :
        if is_pronoun_token(tok_seq[0]) :
            break
        tok_seq.pop(0)
    while len(tok_seq) > 0 :
        index = len(tok_seq) - 1
        if is_pronoun_token(tok_seq[index]) :
            break
        tok_seq.pop(index)

def eliminate_non_names(seq) :
    ''' Eliminate intermittent tokens which are not names or part of a name '''
    accumulator, i = [], 0
    while i < len(seq):
        tok = seq[i]
        i += 1
        if is_pronoun_token(tok) or len(tok) < 3 and tok.isalpha() :
            # See valid token, append to current sequence of names
            accumulator.append(tok)
        else :
            #strip_noise_tokens(accumulator)
            # Invalid token: if no tokens seen so far, keep popping.
            if len(accumulator) == 0 :
                continue
            # Invalid token: if valid tokens already have been seen, recurse
            else :
                ret = [accumulator]
                ret.extend(eliminate_non_names(seq[i+1:]))
                return ret

    if len(seq) == i :
        return [accumulator]

def token_sequence_preprocessing(seq_list) :
    ret = []
    for seq in seq_list :
        #Ignore empty sequences
        if len(seq) == 0 :
            continue
        #Chop starting capital
        #seq = seq[1:]
        #Reverse token sequence
        seq.reverse()
        #Partition by non-propername tokens
        chunks = eliminate_non_names(seq)
        if len(chunks) > 0 :
            ret.extend(chunks)
    return ret

class Node :
    ''' Component of trie. Maintains lowercase comparison by performing mutation
    when checking '''
    def __init__(self, tok) :
        self.tok = tok
        self.count = 0
        self.children = dict()

    def get_child(self, tok) :
        if not self.children.has_key(tok.lower()) :
            self.children[tok.lower()] = Node(tok)
        return self.children[tok.lower()]

    def train_tokens(self, tokens) :
        # Token sequence starts with same token as this node
        if len(tokens) == 0 or self.tok.lower() != tokens[0].lower() :
            return
        tokens.pop(0)
        self.count += 1
        if len(tokens) == 0 :
            return
        c = self.get_child(tokens[0])
        c.train_tokens(tokens)

    def get_score(self, tokens, denom) :
        if self.tok.lower() != tokens[0].lower() :
            return 0
        tokens.pop(0)
        if len(tokens) == 0 :
            ''' This is the destination node. Return Score '''
            if denom == 0 :
                # singleton name
                return 0.0
            return float(self.count)/float(denom)
        child = tokens[0].lower()
        if not self.children.has_key(child) :
            return 0
        else :
            node = self.children[child]
            return node.get_score(tokens, float(self.count))

    def printme(self, num_tab=0) :
        print '\t\t'*num_tab+self.tok+" - "+str(self.count)
        for c in self.children.values() :
            c.printme(num_tab+1)

class BoundaryDetector:
    def __init__(self, cfg_path, corpus_dir=None) :
        global cfg
        cfg = ConfigParser.ConfigParser()
        cfg.read(cfg_path)
        self.node_dict = dict()
        if corpus_dir != None :
            self.train_corpus(corpus_dir)

    def get_node(self, tok) :
        if not self.node_dict.has_key(tok) :
            self.node_dict[tok] = Node(tok)
        return self.node_dict[tok]

    def train_corpus(self, path) :
        files = [path+'/'+f for f in listdir(path) if isfile(join(path,f)) ]
        for f in files :
            self.train_document(Document(f))

    def train_document(self, doc) :
        window_size = int(cfg.get("BoundaryDetector","WindowSize"))
        sent_list = doc.clause_list
        seq_list = token_sequence_preprocessing(sent_list)
        for seq in seq_list :
            for i in range(0, len(seq)) :
                tmp = seq[i:min(i+window_size, len(seq))]
                self.get_node(seq[0]).train_tokens(tmp)
    
    def get_seq_score(self, tokens) :
        if len(tokens) == 0 or not self.node_dict.has_key(tokens[0]) :
            return 0
        return self.node_dict[tokens[0]].get_score(tokens,0)

    def extract_ne_from_document(self, doc) :
        results = set()
        memoize = dict() # reset global dict
        names = dict()
        chunks = token_sequence_preprocessing(doc.clause_list)
        chunk_index = 0
        for chunk in chunks :
            if len(chunk) == 1 :
                results = results.union((tuple(chunk),))
            else :
                name = self.extract_ne_from_sequence(chunk)[0]
                if name == None : 
                    continue
                name = [n[::-1] for n in name] #reverse tuple
                results = results.union(set(name))
            chunk_index += 1
        return results


    def extract_ne_wrapper(self, seq) :
        global memoize 
        memorize = dict()
        print self.extract_ne_from_sequence(seq)

    def extract_ne_from_sequence(self, tokens) :
        def join_partition(candidate, recursive) :
            if candidate == None :
                return (recursive,)
            if recursive == None :
                return (candidate,)
            #ret = [candidate[::-1]]
            ret = [candidate]
            for t in recursive :
                if type(t) is tuple :
                    #t = t[::-1] #Reverse the tuple
                    ret.append(t)
                else :
                    ret.append((t,))
            return tuple(ret)
        ''' Strictly just the boundary partitioning algorith. Assumes
        reversing/noreversing is applies to tokens sequence, as well as any
        pre-processing '''
        window_size = int(cfg.get("BoundaryDetector","WindowSize"))
        global memoize
        if memoize.has_key(tuple(tokens)) :
            return memoize[tuple(tokens)]

        max = (None, 0)
        if len(tokens) == 0 :
            return max
        for i in range(1, min(1+len(tokens),1+window_size)) :
            candidate = tokens[:i]
            candidate_score = self.get_seq_score(copy.deepcopy(candidate))
            #print "candidate:"+str(candidate)+" score:"+str(candidate_score)
            remaining = tokens[i:]
            r_partition, r_score = self.extract_ne_from_sequence(remaining)
            #r_partition = tuple_reverse(r_partition)
            total_score = r_score + candidate_score
            final_partitioning = join_partition(tuple(candidate), r_partition)

            if total_score > max[1] :
                max = (final_partitioning, total_score)

            if total_score == max[1] and \
                    length_measure(final_partitioning) > length_measure(max[0]) :
                max = (final_partitioning, total_score)

        memoize[tuple(tokens)] = max
        return max

def length_measure(tuples) :
    if tuples == None :
        return 0
    score = 0
    for t in tuples :
        if len(t) == 0 :
            continue
        score += len(t) - 1
    return score

def tuple_reverse(t) :
    if t == None :
        return None
    t = list(t)
    t.reverse()
    return tuple(t)
