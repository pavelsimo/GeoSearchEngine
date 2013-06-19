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

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from lib import gserror

__EXIF_GPS_INFO              = "GPSInfo"
__EXIF_TAG_GPS_LATITUDE      = "GPSLatitude"
__EXIF_TAG_GPS_LATITUDE_REF  = "GPSLatitudeRef"
__EXIF_TAG_GPS_LONGITUDE     = "GPSLongitude"
__EXIF_TAG_GPS_LONGITUDE_REF = "GPSLongitudeRef"

def get_exif_header(image):
   """Returns a dictionary from the exif header of an PIL Image. Also converts the GPS Tags.

   Args:
      image: 
   """
   try:
      info = image._getexif()
   except:
      raise gserror.EmptyExifHeaderError('could not found the exif header')
   
   if not info:
      raise gserror.EmptyExifHeaderError('empty exif header')
   
   exif_header = {}   
   for tag, value in info.items():
      tag_id = TAGS.get(tag, tag)
      if tag_id == __EXIF_GPS_INFO:
         gps_info = {}
         for t in value:
            gps_tag_id = GPSTAGS.get(t, t)
            gps_info[gps_tag_id] = value[t]
         exif_header[tag_id] = gps_info
      else:
         exif_header[tag_id] = value
   return exif_header


def get_latlng(exif_header):
   """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_header above).
   
   Args:
      exif_header: 
   """
   if __EXIF_GPS_INFO not in exif_header:
      raise gserror.EmptyLatLngError('could not found the IFD GPSInfo')
   
   gps_info = exif_header[__EXIF_GPS_INFO]
   gps_latitude = gps_info.get(__EXIF_TAG_GPS_LATITUDE, None)
   gps_latitude_ref = gps_info.get(__EXIF_TAG_GPS_LATITUDE_REF, None)
   gps_longitude = gps_info.get(__EXIF_TAG_GPS_LONGITUDE, None)
   gps_longitude_ref = gps_info.get(__EXIF_TAG_GPS_LONGITUDE_REF, None)
   
   if not gps_latitude or not gps_latitude_ref or not gps_longitude or not gps_longitude_ref:
      raise gserror.EmptyLatLngError('empty IFD GPSInfo 1-4')
   
   try:
      lat = to_degree(gps_latitude)
      lng = to_degree(gps_longitude)
   except ZeroDivisionError:
      raise gserror.EmptyLatLngError('zero division error')

   if gps_latitude_ref != "N":
      lat = -lat   
   if gps_longitude_ref != "E":
      lng = -lng
   
   return lat, lng


def to_degree(latlng):
   """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format.
   
   Args:
      latlng: 
   """
   d = float(latlng[0][0]) / float(latlng[0][1])
   m = float(latlng[1][0]) / float(latlng[1][1])
   s = float(latlng[2][0]) / float(latlng[2][1])
   return d + (m / 60.0) + (s / 3600.0)
