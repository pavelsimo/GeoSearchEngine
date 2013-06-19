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
from lxml import etree
from lib.stemming.porter2 import stem
from lib import gindex

try:
   import cPickle as pickle
except:
   import pickle

class GeoIndexer(object):
   """
      
   """
   _MIN_LENGTH_WORD = 3

   _STOP_WORDS = {'a', 'about', 'above', 'above', 'across', 'after', 'afterwards', 'again', 
      'against', 'all', 'almost', 'alone', 'along', 'already', 'also','although',
      'always','am','among', 'amongst', 'amoungst', 'amount',  'an', 'and', 'another',
      'any','anyhow','anyone','anything','anyway', 'anywhere', 'are', 'around', 'as',
      'at', 'back','be','became', 'because','become','becomes', 'becoming', 'been', 
      'before', 'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 
      'between', 'beyond', 'bill', 'both', 'bottom','but', 'by', 'call', 'can', 
      'cannot', 'cant', 'co', 'con', 'could', 'couldnt', 'cry', 'de', 'describe', 
      'detail', 'do', 'done', 'down', 'due', 'during', 'each', 'eg', 'eight', 
      'either', 'eleven','else', 'elsewhere', 'empty', 'enough', 'etc', 'even', 
      'ever', 'every', 'everyone', 'everything', 'everywhere', 'except', 'few', 
      'fifteen', 'fify', 'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 
      'formerly', 'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get',
      'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her', 'here', 
      'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him', 
      'himself', 'his', 'how', 'however', 'hundred', 'ie', 'if', 'in', 'inc', 
      'indeed', 'interest', 'into', 'is', 'it', 'its', 'itself', 'keep', 'last', 
      'latter', 'latterly', 'least', 'less', 'ltd', 'made', 'many', 'may', 'me', 
      'meanwhile', 'might', 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 
      'move', 'much', 'must', 'my', 'myself', 'name', 'namely', 'neither', 'never', 
      'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not', 
      'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once', 'one', 'only',
      'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out',
      'over', 'own','part', 'per', 'perhaps', 'please', 'put', 'rather', 're', 'same',
      'see', 'seem', 'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 
      'should', 'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some', 
      'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 
      'still', 'such', 'system', 'take', 'ten', 'than', 'that', 'the', 'their', 
      'them', 'themselves', 'then', 'thence', 'there', 'thereafter', 'thereby', 
      'therefore', 'therein', 'thereupon', 'these', 'they', 'thickv', 'thin', 'third',
      'this', 'those', 'though', 'three', 'through', 'throughout', 'thru', 'thus', 
      'to', 'together', 'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two', 
      'un', 'under', 'until', 'up', 'upon', 'us', 'very', 'via', 'was', 'we', 'well', 
      'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter',
      'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether', 'which', 
      'while', 'whither', 'who', 'whoever', 'whole', 'whom', 'whose', 'why', 'will', 
      'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours', 'yourself',
      'yourselves', 'the'}


   def __init__(self, path):
      self.path = path
      self.inv_ind = gindex.GeoInvertedIndex()
      self.posting_lst = []
      self.url_regex = re.compile(
              r'^(?:http|ftp)s?://' # http:// or https://
              r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
              r'localhost|' #localhost...
              r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
              r'(?::\d+)?' # optional port
              r'(?:/?|[/?]\S+)$', re.IGNORECASE)
      
      # stats
      self.countries = set()
      self.cities = set()
      self.establishment = set()
      self.neighborhoods = set()
      self.routes = set()
      self.tot_pic_per_year = {}
      self.tot_docs = 0

   @staticmethod
   def term_normalize(term):
      res = ''.join(e for e in term if e.isalpha())
      res = stem(res.lower())
      return res
   
   def get_inv_ind(self):
      return self.inv_ind

   def get_xml_file(self, path):
      try:
         f = open(path,'r')
         xml = f.read()
         f.close()
      except IOError:
         raise IOError('could not open the xml file')
      return xml


   def is_url(self, url):
      if self.url_regex.match(url):
         return True
      return False

   def add_index_entry(self, term, doc_id):
      self.get_inv_ind().add_term(term)
      term_id = self.get_inv_ind().get_term_id(term)
      self.get_inv_ind().add_index_entry(term_id, doc_id)   

   def add_xml_entry(self, xml):
      root = etree.fromstring(xml)
      for doc in root.findall('.//doc'):
         self.tot_docs = self.tot_docs + 1
         
         doc_hash = doc.find('.//id')
         doc_timestamp = doc.find('.//timestamp')
         doc_width = doc.find('.//width')
         doc_height = doc.find('.//height')
         doc_url = doc.find('.//url')
         doc_terms = doc.find('.//terms')
            
         if hasattr(doc_hash,'text'):
            self.get_inv_ind().add_document(doc_hash.text)
            pass

         if hasattr(doc_timestamp,'text'):
            year = doc_timestamp.text[:4]
            self.tot_pic_per_year[year] = self.tot_pic_per_year.get(year, 0) + 1
         else:
            self.tot_pic_per_year['None'] = self.tot_pic_per_year.get('None', 0) + 1
            
         if hasattr(doc_width,'text'):
            pass      
            
         if hasattr(doc_height,'text'):
            pass
            
         if hasattr(doc_terms,'text'):
            if doc_terms.text:
               terms = doc_terms.text.split()
               pos = 0
               for t in terms:
                  pos = pos + 1
                  if t in GeoIndexer._STOP_WORDS or self.is_url(t):
                     continue
                  term = GeoIndexer.term_normalize(t)
                  if len(term) >= GeoIndexer._MIN_LENGTH_WORD:
                     doc_id = self.get_inv_ind().get_doc_id(doc_hash.text)
                     self.posting_lst.append((term, doc_id))

         if hasattr(doc_url,'text'):
            pass
         
         for address_component in doc.findall('.//address_component'):
            address_component_type = address_component.find('.//type')
            address_component_long_name = address_component.find('.//long_name')

            ok = False
            if hasattr(address_component_type,'text'):
               if address_component_type.text == 'country':
                  self.countries.add(address_component_long_name.text)
               elif address_component_type.text == 'administrative_area_level_1':
                  self.cities.add(address_component_long_name.text)
               elif address_component_type.text == 'establishment':
                  self.establishment.add(address_component_long_name.text)
               elif address_component_type.text == 'neighborhood':
                  self.neighborhoods.add(address_component_long_name.text)
               elif address_component_type.text == 'route':
                  self.routes.add(address_component_long_name.text)

   def write_file(self, path, data):
      try:
         file = open(path,'wb')
         file.write(data)
         file.close()
      except IOError:
         print 'i/o error'

   def save(self):
      buffer = pickle.dumps(self.get_inv_ind())
      self.write_file('inverted-index.pkl', buffer)

   def run(self):
      for root, dirs, files in os.walk(self.path):
         for name in files:
            path = os.path.join(root, name)
            ext = os.path.splitext(path)[1][1:].strip()
            if ext == 'xml':
               xml = self.get_xml_file(path)
               self.add_xml_entry(xml)
      self.posting_lst.sort()
      for post in self.posting_lst:
         self.add_index_entry(post[0],post[1]);
      self.save()
      
      print u'Total number of documents indexed: {0}\n'.format(self.tot_docs)
      print u'Total pictures per year: {0}\n'.format(self.tot_pic_per_year)
      print u'Total number of countries: {0}\n{1}\n'.format(len(self.countries), self.countries)
      print u'Total number of cities: {0}\n{1}\n'.format(len(self.cities), self.cities)
      print u'Total pictures per year: {0}\n'.format(self.tot_pic_per_year)
      print u'Total number of establishments: {0}\n{1}\n'.format(len(self.establishment),self.establishment)
      print u'Total number of neighborhoods: {0}\n{1}\n'.format(len(self.neighborhoods),self.neighborhoods)
      print u'lst {0}'.format(self.posting_lst)

def main():  
   parser = argparse.ArgumentParser(description='create_index')
   parser.add_argument('-d', '--directory', action="store", dest="path", default='.')
   results = parser.parse_args()
   path = results.path
   obj = GeoIndexer(path)
   obj.run()

if __name__ == '__main__':
   main()
