#!/usr/bin/env python

from urlparse import urljoin
import os
import re
import Database
import Image
import Thumb
import Util

# TODO: Iterate through pic resolutions, comments

class Scrape(object):
  def __init__(self, db_name):
    self.db_name = db_name
    self.db = Database.Database(self.db_name)
    self.db.make_tables()

  def scrape_thumbs(self, parent_url, album_name=None):
    thumb = Thumb.find_albums_in(parent_url, album_name)[0]
    if not self.is_scrape_thumbs_complete(thumb):
      self._process_thumb(thumb)
      assert self.is_scrape_thumbs_complete(thumb)

  def is_scrape_thumbs_complete(self, thumb):
    info = thumb.get_info()
    try:
      row = self.db.get_row_by_field('album', 'album_url', info['album_url'])
    except Database.DbException:
      return False

    Util.assert_equals(row['parent'], -1)
    for item in ['name', 'date', 'num_items', 'tot_items']:
      Util.assert_equals(str(row[item]), str(info[item]))
    num_albums = self.db.count_rows('album', 'parent > 0')
    num_images = self.db.count_rows('image', 'parent > 0')
    Util.assert_equals(num_albums + num_images, row['tot_items'])
    print ('"%s" has been scraped: %s sub-albums, %s images'
           % (row['name'], num_albums, num_images))
    return True

  def _process_thumb(self, thumb, parent_rowid=-1):
    thumb_info = thumb.get_info()
    thumb_info['parent'] = parent_rowid
    if thumb.get_type() == Thumb.IMAGE:
      rowid = self.db.add_row('image', thumb_info)
      url = thumb_info['image_page_url']
      print 'Added image %d: %s' % (rowid, url)
    else:
      rowid = self.db.add_row('album', thumb_info)
      url = thumb_info['album_url']
      print 'Added album %d: %s' % (rowid, url)
      for child in Thumb.get_all_thumbs(url):
        self._process_thumb(child, rowid)

  def scrape_image_sizes(self):
    images = self.db.get_rows('image')
    for img_info in images:
      rowid = img_info['id']
      url = img_info['image_page_url']
      image = Image.Image(url)
      update_info = image.get_update_info()
      self.db.update_row_by_field('image', 'id', rowid, update_info)
      print update_info['full_size_img_url'],
      for size_info in image.get_size_infos():
        size_info['parent'] = rowid
        self.db.add_row('size', size_info)
        print '%sx%s' % (size_info['width'], size_info['height']),
      print ''


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
  s.scrape_thumbs(Util.BASE_URL, 'Dan and Laurel')
  s.scrape_image_sizes()
