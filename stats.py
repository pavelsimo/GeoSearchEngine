#!/usr/bin/python
import os
import argparse
import sys
import string
import re
from PIL import Image

from lib import gsutils

__CONTROL_CH = string.maketrans('', '')

img_cnt = 0
img_gps_cnt = 0
dirpath  = '.'
m_dev = {}

parser = argparse.ArgumentParser(description='picanalyzer')
parser.add_argument('-p', action="store", dest="path", default='.')
results = parser.parse_args()
dirpath = results.path
google_map_url = "http://maps.googleapis.com/maps/api/staticmap?center=0,0&zoom=1&size=640x480&sensor=false"
google_map_params = ""

for root, dirs, files in os.walk(dirpath):
   for name in files:
      filename = os.path.join(root,name)
      img = None
      exif_header = None
      try:
         img = Image.open(filename)
      except:
         img = None
      if img:
         img_cnt = img_cnt + 1
         try:
            exif_header = gsutils.get_exif_header(img)
         except:
            exif_header = None
            
         if exif_header:
            try:
               latlng = gsutils.get_latlng(exif_header)
            except:
               latlng = [None,None]
            if latlng[0] and latlng[1]:
               google_map_params = google_map_params + "&markers=color:red%7C" + "%.6f,%.6f" % (latlng[0],latlng[1]) 
               img_gps_cnt = img_gps_cnt + 1
               exif_model = exif_header.get("Model", '')
               if len(exif_model) == 0:
                  exif_model = 'None'
               exif_model = exif_model.translate(__CONTROL_CH, __CONTROL_CH[:32])
               m_dev[exif_model] = m_dev.get(exif_model,0) + 1
               print "%s %s (%.6f,%.6f)" % (exif_model.ljust(45), filename.ljust(80), latlng[0], latlng[1])

if img_cnt > 0:
   print '\n%s%d'   % ('total images'.ljust(25),img_cnt)
   print '%s%d'     % ('images with gps'.ljust(25),img_gps_cnt)
   print '%s%.2f%%' % ('percentage with gps'.ljust(25) ,100.0 * img_gps_cnt / img_cnt)
   if img_gps_cnt > 0:
      lst_keys = m_dev.keys()
      lst_keys.sort()
      for e in lst_keys:
         print '[%2d] %s %.2f%%' % (m_dev[e], e.ljust(40), 100.0 * m_dev[e] / img_gps_cnt)
else:
   print 'images not found'
   
#print len(google_map_url + google_map_params)   
#print google_map_url + google_map_params

   
