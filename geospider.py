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
import sys
import os
import re
import argparse
import socket
import string
import StringIO
import hashlib
import robotparser
import urlparse
import time
import logging
import urllib
import urllib2
import lxml.html
import ConfigParser
from lxml import etree
from collections import deque
from time import gmtime, strftime
from PIL import Image

from lib import termcolor
from lib import gsutils
from lib import gserror

__author_name__ = "Pavel Simo"
__author_email__ = "pavel.simo@gmail.com"
__author__ = "%(__author_name__)s <%(__author_email__)s>" % vars()
__date__ = "2011-10-06"
__license__ = "GPL"
__url__ = "http://pavelsimo.blogspot.com/"
__version__ = "0.1"

config = ConfigParser.ConfigParser()
config.read('config/geospider.cfg')
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description = GeoSpider._AGENT_DESCRIPTION)
    parser.add_argument('-u', '--url',   action="store", dest="url", 
          help='target uniform resource locator')
    parser.add_argument('-d', '--depth', action="store", type=int, dest="depth", 
          help='maximum depth threshold', default = GeoSpider._DEFAULT_DEPTH)
    parser.add_argument('-p', '--path',  action="store", dest="path", 
          help='storage path of the images and xml files', default = GeoSpider._DEFAULT_PATH)
    parser.add_argument('-t', '--socket-timeout',  action="store", type=int, dest="timeout", 
          help='socket connection time limit threshold', default = GeoSpider._SOCKET_TIMEOUT)

    results = parser.parse_args()

    if len(sys.argv) > 1:
        try:
            obj = GeoSpider(results.url, results.path, results.depth, results.timeout)
            obj.run()
        except KeyboardInterrupt as e:
            logging.error('Aborted')
            program_basename = os.path.basename(sys.argv[0])
            sys.stderr.write('{0}: error: {1}\n'.format(program_basename, 'Aborted'))
            sys.exit(1)
    else:
        parser.print_help()


class Node:
   """
      
   """
   def __init__(self, url, referer_url, depth):
      self.url = url
      self.referer_url = referer_url
      self.depth = depth

   def get_url(self):
      return self.url

   def get_depth(self):
      return self.depth
   
   def get_referer_url(self):
      return self.referer_url


class GeoSpiderDocument:
   """
   
   """
   def __init__(self, doc_id, latlng, base_url, referer_url, terms, img, img_data, exif_headers):
      self.doc_id = doc_id
      self.lat = latlng[0]
      self.lng = latlng[1]
      self.base_url = base_url
      self.referer_url = referer_url
      self.terms = terms
      self.img = img
      self.img_data = img_data
      self.exif_headers = exif_headers
      
   def set_doc_id(self, doc_id):
      self.doc_id = doc_id
   
   def set_lat(self, lat):
      self.lat = lat
      
   def set_lng(self, lng):
      self.lng = lng
   
   def set_base_url(self, base_url):
      self.base_url = base_url
      
   def set_referer_url(self, referer_url):
      self.referer_url = referer_url
   
   def set_terms(self, terms):
      self.terms = terms
   
   def set_img(self, img):
      self.img = img
      
   def set_img_data(self, img_data):
      self.img_data = img_data
   
   def set_exif_headers(self, exif_headers):
      self.exif_headers = exif_headers
   
   def get_doc_id(self):
      return self.doc_id
         
   def get_base_url(self):
      return self.base_url
      
   def get_referer_url(self):
      return self.referer_url
          
   def get_lat(self):
      return self.lat
   
   def get_lng(self):
      return self.lng
          
   def get_terms(self):
      return self.terms
      
   def get_img(self):
      return self.img
      
   def get_img_data(self):
      return self.img_data
      
   def get_exif_headers(self):
      return self.exif_headers


class GeoSpider(object):
   """
   
   
   """
   
   _ALL_BYTES             = string.maketrans('', '')
   _AGENT_NAME            = config.get('geospider', 'AGENT_NAME')
   _SOCKET_TIMEOUT        = config.getint('geospider', 'SOCKET_TIMEOUT')
   _DEFAULT_PATH          = config.get('geospider', 'DEFAULT_PATH')
   _MIN_IMAGE_WIDTH       = config.getint('geospider', 'MINIMUM_IMAGE_WIDTH')
   _MIN_IMAGE_HEIGHT      = config.getint('geospider', 'MINIMUM_IMAGE_HEIGHT')
   _RE_FILTER             = config.get('geospider', 'RE_FILTER')
   _GOOGLE_MAP_API_SENSOR = config.get('geospider', 'GOOGLE_MAP_API_SENSOR')
   _GOOGLE_MAP_API_URL    = config.get('geospider', 'GOOGLE_MAP_API_URL')
   _XML_HEADER_TAG        = config.get('geospider', 'XML_HEADER_TAG')
   _XML_DECLARATION       = config.getboolean('geospider', 'XML_DECLARATION')
   _XML_PRETTY_PRINT      = config.getboolean('geospider', 'XML_PRETTY_PRINT')
   _XML_ENCODING          = config.get('geospider', 'XML_ENCODING')
   _AGENT_DESCRIPTION     = config.get('geospider', 'AGENT_DESCRIPTION')
   _DEFAULT_DEPTH         = config.getint('geospider', 'DEFAULT_DEPTH')
   
   _HTTP_STATUS_MESSAGES = {
      100: 'Continue',
      101: 'Switching Protocols',
      200: 'OK',
      201: 'Created',
      202: 'Accepted',
      203: 'Non-Authoritative Information',
      204: 'No Content',
      205: 'Reset Content',
      206: 'Partial Content',
      300: 'Multiple Choices',
      301: 'Moved Permanently',
      302: 'Moved Temporarily',
      303: 'See Other',
      304: 'Not Modified',
      305: 'Use Proxy',
      306: 'Unused',
      307: 'Temporary Redirect',
      400: 'Bad Request',
      401: 'Unauthorized',
      402: 'Payment Required',
      403: 'Forbidden',
      404: 'Not Found',
      405: 'Method Not Allowed',
      406: 'Not Acceptable',
      407: 'Proxy Authentication Required',
      408: 'Request Time-out',
      409: 'Conflict',
      410: 'Gone',
      411: 'Length Required',
      412: 'Precondition Failed',
      413: 'Request Entity Too Large',
      414: 'Request-URI Too Large',
      415: 'Unsupported Media Type',
      416: 'Requested Range Not Satisfiable',
      417: 'Expectation Failed',
      500: 'Internal Server Error',
      501: 'Not Implemented',
      502: 'Bad Gateway',
      503: 'Service Unavailable',
      504: 'Gateway Time-out',
      505: 'HTTP Version not supported'
   }

   def __init__(self, base_url, path, depth, timeout):
      """Constructor.
            
      Args:
         base_url:
         depth:  
      """
      self.base_url = base_url
      self.path     = path
      self.depth    = depth
      self.timeout  = timeout
      self.seen_images = set()
      
      # geospider xml document
      self.root = etree.Element(GeoSpider._XML_HEADER_TAG)
      self.xml = etree.ElementTree(self.root)
      self.xml_filename = strftime("%Y%m%d%H%M%S", gmtime()) + '.xml'
      socket.setdefaulttimeout(self.timeout)
      
      logging.debug('base_url: %s', self.base_url)
      logging.debug('depth: %s', self.depth)
      logging.debug('agent: %s', GeoSpider._AGENT_NAME)
      logging.debug('timeout: %d', self.timeout)


   @staticmethod
   def http_status_message(code):
      """Returns the default HTTP status message for the given code.
      
       Args:
         code: the HTTP code for which we want a message
       """
      return GeoSpider._HTTP_STATUS_MESSAGES.get(code, 'None')


   def fetch(self, url):
      """ Returns a lxml document and the urllib2 response object for the URL requested.

      Args:
         url: A string with the uniform resource locator.
      """
      logging.info('Started - fetch')
      
      if re.search(GeoSpider._RE_FILTER, url):
         raise gserror.FetchError('regular expression filter error')
      
      try:
         response = urllib2.urlopen(url)
         html = response.read()
      except urllib2.URLError as e:
         if hasattr(e,'code'):
            raise gserror.FetchError('{0} {1}'.format(e.code, GeoSpider.http_status_message(e.code)))
         raise gserror.FetchError('url error')
      except socket.timeout:
         raise gserror.FetchError('socket timeout')
      except socket.error:
         raise gserror.FetchError('socket error')

      logging.info(termcolor.colored('content-type: %s' % (response.info().gettype()), 'yellow'))
      
      try:
         doc = lxml.html.document_fromstring(html)
         doc.make_links_absolute(url)
      except lxml.etree.XMLSyntaxError as e:
         raise gserror.FetchError('lxml parse error')

      logging.info('Finished - fetch')
      return doc, response


   def fetch_image(self, url, referer_url, terms):
      """ If it meets the size and metadata requirements, download the image referenced by the target URL.

         Args:
            url: A string with the uniform resource locator of the image
      """
      logging.info('Started - fetch_image')
      
      if re.search(GeoSpider._RE_FILTER, url):
         raise gserror.FetchError('regular expression filter error')         
      
      try:
         response = urllib2.urlopen(url)
         img_data = response.read()
         img_name = hashlib.sha224(img_data).hexdigest()
      except urllib2.URLError as e:
         if hasattr(e,'code'):
            raise gserror.FetchError('{0} {1}'.format(e.code, GeoSpider.http_status_message(e.code)))
         raise gserror.FetchError('url error')
      except socket.timeout:
         raise gserror.FetchError('socket timeout')
      except socket.error:
         raise gserror.FetchError('socket error')

      if img_name in self.seen_images:
         raise gserror.FetchError('previously crawled image error')
      
      self.seen_images.add(img_name)
      
      try:
         img = Image.open(StringIO.StringIO(img_data))
      except IOError:
         raise gserror.FetchError('could not open the image error')       
      
      if img.format != "JPEG":
         raise gserror.FetchError('incorrect image format %s' % img.format)
      
      if img.size[0] < GeoSpider._MIN_IMAGE_WIDTH or img.size[1] < GeoSpider._MIN_IMAGE_HEIGHT:
         raise gserror.FetchError('the image size (%d,%d) does not reach the minimum threshold' % img.size)
      
      try:
         exif_header = gsutils.get_exif_header(img)
      except gserror.EmptyExifHeaderError as e:
         raise gserror.FetchError('exif header not found')

      logging.info(termcolor.colored('exif-header: %s' % (exif_header), 'green'))
         
      try:
         latlng = gsutils.get_latlng(exif_header)
      except gserror.EmptyLatLngError as e:
         raise gserror.FetchError('coordinates not found')
      
      logging.info(termcolor.colored('image coordinates: (%.6f, %.6f)' % latlng, 'magenta'))
      logging.info(termcolor.colored('image size: (%d,%d)' % img.size, 'magenta'))
      logging.info(termcolor.colored('image name: {0}.jpg'.format(img_name), 'magenta'))
      
      img_path = os.path.join(self.path, '{0}.jpg'.format(img_name))
      if os.path.isfile(img_path):
         raise gserror.FetchError('previously storaged image error')
      
      gsdoc = GeoSpiderDocument(img_name, latlng, url, referer_url, 
                  terms, img, img_data, exif_header)
      
      try:
         self.save(gsdoc)
      except gserror.GeocodeResponseError as e:
         raise gserror.FetchError('google api error {0}'.format(e))
      except urllib2.URLError:
         raise gserror.FetchError('could not connect to google map api')
      except ValueError:
         raise gserror.FetchError('value error could not save the xml document')
      except IOError:
         raise gserror.FetchError('input/output error')
      except socket.timeout:
         raise gserror.FetchError('socket timeout')
      except socket.error:
         raise gserror.FetchError('socket error')
      logging.info('Finished - fetch_image')


   def save_image(self, img_path, img_data):
      """ Storage in disk the image with the given img_path.
      
         Args:
            img_path:
            img_data:
      """
      logging.info('Started - save_image')
      try:
         img_file = open(img_path,'wb')
         img_file.write(img_data)
         img_file.close()
      except IOError:
         raise
      logging.info('Finished - save_image')


   def save(self, gsdoc):
      """ FIXME
         
         Args: 
            gsdoc: 
      """
      logging.info('Started - save')

      params = {}
      params['latlng'] = "%.6f,%.6f" % (gsdoc.get_lat(), gsdoc.get_lng())
      params['sensor'] = GeoSpider._GOOGLE_MAP_API_SENSOR
      url = "%s?%s" % (GeoSpider._GOOGLE_MAP_API_URL, urllib.urlencode(params))
      
      logging.info('google_map_api_config_parameters: %s\n', params)
      logging.info('google_map_api_url: %s',url)
      
      try:
         req = urllib2.Request(url)
         response = urllib2.urlopen(req)
         googleapi_xml = response.read()
      except urllib2.URLError as e:
         raise
      except socket.timeout:
         raise
      
      googleapi_doc = etree.fromstring(googleapi_xml)
      status_message = googleapi_doc.find('.//status').text
      
      logging.info('status message: %s',status_message)      
      if status_message != "OK":
         raise gserror.GeocodeResponseError(status_message)
      
      img_path = os.path.join(self.path, '{0}.jpg'.format(gsdoc.get_doc_id()))
      self.save_image(img_path, gsdoc.get_img_data())
      
      logging.info(termcolor.colored('\n%s' % (etree.tostring(googleapi_doc)), 'yellow'))
      
      doc = etree.SubElement(self.root,'doc')
      doc_id = etree.SubElement(doc,'id')
      doc_id.text = gsdoc.get_doc_id()
      url = etree.SubElement(doc,'url')
      url.text = gsdoc.get_base_url()
      referer_url = etree.SubElement(doc,'referer_url')
      referer_url.text = gsdoc.get_referer_url()
      
      exif_header = gsdoc.get_exif_headers()
      exif_date_time = exif_header.get('DateTime', None)
      exif_make = exif_header.get('Make', None)
      exif_model = exif_header.get('Model', None)
      exif_software = exif_header.get('Software', None)
      
      if exif_date_time:
         logging.info('exif_date_time: %s',exif_date_time)
         timestamp = etree.SubElement(doc,'timestamp')
         timestamp.text = exif_date_time.translate(GeoSpider._ALL_BYTES, 
            GeoSpider._ALL_BYTES[:32]).strip()
      if exif_make:
         logging.info('exif_make: %s',exif_make)
         make = etree.SubElement(doc,'make')
         make.text = exif_make.translate(GeoSpider._ALL_BYTES, 
            GeoSpider._ALL_BYTES[:32]).strip()
      if exif_model:
         logging.info('exif_model: %s',exif_model)
         model = etree.SubElement(doc,'model')
         model.text = exif_model.translate(GeoSpider._ALL_BYTES, 
            GeoSpider._ALL_BYTES[:32]).strip()
      if exif_software:
         logging.info('exif_software: %s',exif_software)
         software = etree.SubElement(doc,'software')
         software.text = exif_software.translate(GeoSpider._ALL_BYTES, 
            GeoSpider._ALL_BYTES[:32]).strip()

      img = gsdoc.get_img()
      
      if img:
         img_width = etree.SubElement(doc,'width')
         img_width.text = str(img.size[0])
         img_height = etree.SubElement(doc,'height')
         img_height.text = str(img.size[1])      
      
      terms = etree.SubElement(doc,'terms')
      terms.text = " ".join(gsdoc.get_terms())
      
      location = etree.SubElement(doc,'location')

      lat = etree.SubElement(location,'lat')
      lat.text = str(gsdoc.get_lat())
      lng = etree.SubElement(location,'lng')
      lng.text = str(gsdoc.get_lng())

      for elem in googleapi_doc.findall('.//address_component'):
         address_component = etree.SubElement(location,'address_component')
         for node in elem:
            address_component_node  = etree.SubElement(address_component,node.tag)
            address_component_node.text = node.text
   
      xml_path = os.path.join(self.path, self.xml_filename)
      
      try:
         f = open(xml_path,'wb')
         self.xml.write(f, xml_declaration = GeoSpider._XML_DECLARATION, 
                           pretty_print = GeoSpider._XML_PRETTY_PRINT, 
                           encoding = GeoSpider._XML_ENCODING)
         f.close()
      except IOError:
         raise
      
      logging.info('Finished - save')


   def extract_terms(self, doc):
      #FIXME: add more html tags
      """
         
         Args: 
            doc: 
      """
      logging.info('Started - extract_terms')
      terms = []
      for e in doc.findall(".//title"):
         words = e.text_content()
         if words:
            terms.extend(words.split())
      for e in doc.findall(".//meta"):
         words = e.get('content')
         if words:
            terms.extend(words.split())
      logging.info(termcolor.colored('keywords = %s' % (terms), 'cyan'))
      logging.info('Finished - extract_terms')
      return terms


   def run(self):
      """ 
      
      """
      logging.info('Started - run')
      
      rp = None
      queue = deque([Node(self.base_url, self.base_url, 0)])
      seen = set()
      
      #FIXME: handle the correct exception
      try:
         rp = robotparser.RobotFileParser()
         rp.set_url(urlparse.urljoin(self.base_url,'robots.txt'))
         rp.read()
      except:
         rp = None
         logging.error(termcolor.colored('The robots.txt file does not exist.','red'))
   
      while queue:
         try:
            cur = queue.popleft() 
         except IndexError:
            break
         if cur.get_depth() > self.depth or cur.get_url() in seen:
             continue
         
         # robots.txt 
         if rp:
            if not rp.can_fetch("*", cur.get_url()):
               logging.error(termcolor.colored('robots.txt can not fetch this page', 'red'))
               continue
         
         seen.add(cur.get_url())
         logging.info(termcolor.colored('depth={0} url={1}'.format(cur.get_depth(), cur.get_url()), 'blue'))
         
         try:
            data = self.fetch(cur.get_url())
            doc = data[0]
            response = data[1]
         except gserror.FetchError as e:
            logging.error(termcolor.colored('could not fetch the document: {0}'.format(e),'red'))
            continue
         
         if response.info().gettype() not in ['text/html', 'application/xhtml+xml']:
            continue

         terms = self.extract_terms(doc)
         
         for img in doc.findall('.//img'):
            img_src = img.get('src')
            img_alt = img.get('alt')
            img_title = img.get('title')
            logging.info('alt = %s title = %s src = %s', img_alt, img_title, img_src)
            seen.add(img_src)
            try:
               self.fetch_image(img_src, cur.get_referer_url(), terms)
            except gserror.FetchError as e:
               logging.error(termcolor.colored('could not fetch the image: {0}'.format(e),'red'))
         
         for element, attribute, link, pos in doc.iterlinks():
            if not link.startswith(self.base_url):
               continue
            nxt = Node(link, cur.get_url(), cur.get_depth() + 1)
            queue.appendleft(nxt)
            logging.info(u'depth={0} url={1}'.format(nxt.get_depth(), nxt.get_url()))
      logging.info('Finished - run')


if __name__ == '__main__':
   main()

