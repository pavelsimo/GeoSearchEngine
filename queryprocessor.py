#!/usr/bin/python
# Copyright (C) 2011  Pavel Simo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import argparse
import sys
import re
try:
   import cPickle as pickle
except:
   import pickle
import pprint

from lib import gindex
from lib.stemming.porter2 import stem

class QueryProcessor(object):
   
   def __init__(self, index_file):
      pkl_file = open(index_file, 'rb')
      self.data = pickle.load(pkl_file)
      self.iindex = self.data.get_inverted_index()
      pkl_file.close()
   
   @staticmethod
   def term_normalize(term):
      res = ''.join(e for e in term if e.isalpha())
      res = stem(res.lower())
      return res
   
   def get_data(self):
      return self.data
   
   def get_posting_list(self, term):
      res = []
      try:
         res = self.iindex[self.data.get_term_id(term)]
      except KeyError as e:
         print 'error: KeyError {0}'.format(e)
      return res
   
   def intersect(self, X, Y):
      res = []
      p1 = 0
      p2 = 0
      while p1 < len(X) and p2 < len(Y):
         if X[p1] == Y[p2]:
            res.append(X[p1])
            p1 = p1 + 1
            p2 = p2 + 1
         else:
            if X[p1] < Y[p2]:
               p1 = p1 + 1
            else:
               p2 = p2 + 1
      return res
   
   def print_inverted_index(self):
      for term_id in self.iindex:
         print u'{0} = ('.format(self.data.get_term(term_id)),
         for doc_id in self.iindex[term_id]:
            print u'{0}'.format(doc_id),
         print ')'
   
   def query(self, S):
      words = S.split()
      if len(words) == 1:
         return self.get_posting_list(QueryProcessor.term_normalize(words[0]))
      res = self.get_posting_list(words[0])
      for i in xrange(1, len(words)):
         res = self.intersect(res, self.get_posting_list(QueryProcessor.term_normalize(words[i])))
      return res
      
def main():  
   """

   """
   parser = argparse.ArgumentParser(description='create_index')
   parser.add_argument('-q', '--query', action="store", dest="query", default='great music')
   results = parser.parse_args()

   qprocessor = QueryProcessor('inverted-index.pkl')
   #qprocessor.print_inverted_index()
   res = qprocessor.query(results.query)
   print 'Query Result of {0}:'.format(results.query)
   for i in xrange(0, len(res)):
      print '{0}: {1}'.format(res[i], qprocessor.get_data().get_doc_hash(res[i]))

if __name__ == '__main__':
   main()
