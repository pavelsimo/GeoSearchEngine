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

class GeoInvertedIndex(object):
   """

   """
   def __init__(self, m_inverted_index = {}, m_dict_term_to_id = {}, 
            m_dict_id_to_term = {}, m_doc_hash_to_id = {}, m_doc_id_to_hash = {},
               cnt_term = 0, cnt_doc = 0):
      self.m_inverted_index = m_inverted_index
      self.m_dict_term_to_id = m_dict_term_to_id
      self.m_dict_id_to_term =  m_dict_id_to_term
      self.m_doc_hash_to_id = m_doc_hash_to_id
      self.m_doc_id_to_hash = m_doc_id_to_hash
      self.cnt_term = cnt_term
      self.cnt_doc  = cnt_doc

   def get_inverted_index(self):
      return self.m_inverted_index

   def get_term_id(self, term):
      return self.m_dict_term_to_id[term]

   def get_term(self, term_id):
      return self.m_dict_id_to_term[term_id]

   def get_doc_id(self, doc_hash):
      return self.m_doc_hash_to_id[doc_hash]

   def get_doc_hash(self, doc_id):
      return self.m_doc_id_to_hash[doc_id]

   def add_term(self, term):
      if term not in self.m_dict_term_to_id:
         self.m_dict_term_to_id[term] = self.cnt_term
         self.m_dict_id_to_term[self.cnt_term] = term
         self.cnt_term = self.cnt_term + 1
   
   def add_document(self, doc_hash):
      if doc_hash not in self.m_doc_hash_to_id:
         self.m_doc_hash_to_id[doc_hash] = self.cnt_doc
         self.m_doc_id_to_hash[self.cnt_doc]  = doc_hash
         self.cnt_doc = self.cnt_doc + 1 

   def add_index_entry(self, term_id, doc_id):
      if term_id not in self.m_inverted_index:
         self.m_inverted_index[term_id] = [doc_id]
      else:
         self.m_inverted_index[term_id].append(doc_id)

def main():  
   pass

if __name__ == '__main__':
   main()
