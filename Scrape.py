#!/usr/bin/env python

from urlparse import urljoin
import os
import re
import Database
import Thumb
import Util

# TODO: Iterate through pic resolutions, comments

class Scrape(object):
  def __init__(self, db_name):
    self.db_name = db_name
    self.db = Database.Database(self.db_name)
    self.db.make_tables()

  def scrape(self, parent_url, album_name=None):
    top_album = Thumb.find_albums_in(parent_url, album_name)[0]
    self.process_thumb(top_album)

  def process_thumb(self, thumb, parent_rowid=-1):
    thumb_info = thumb.get_info()
    thumb_info['parent'] = parent_rowid
    if thumb.get_type() == Thumb.ITEM:
      rowid = self.db.add_row('image', thumb_info)
      url = thumb_info['image_page_url']
      print "Added image %d: %s" % (rowid, url)
    else:
      rowid = self.db.add_row('album', thumb_info)
      url = thumb_info['album_url']
      print "Added album %d: %s" % (rowid, url)
      for thumb in Thumb.get_all_thumbs(url):
        self.process_thumb(thumb, rowid)

#def get_album_details(url):
#  soup = Util.get_soup(url)
#  album_div = soup('div', 'gbBlock gcBackground1')[0]
#  album_title = Util.contents(album_div('h2'))
#  # TODO: check the h2 contents vs. the album name from its thumbnail?
#def get_image_details(url):
#  soup = Util.get_soup(url)
#  full_size_img_url = soup('a', title='Full Size')[0]['href']

if __name__ == '__main__':
  Util.set_base_url('http://ender.snowburst.org:4747/gallery/v/Friends/')
  s = Scrape('gallery.db')
  s.scrape(Util.BASE_URL, 'Dan and Laurel')
