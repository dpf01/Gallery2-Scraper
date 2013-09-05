#!/usr/bin/env python

from urlparse import urljoin
import os
import re
import Database
import Image
import Site
import Thumb
import Util

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
      row = self.db.get_row_by_field('album', 'page_url', info['page_url'])
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
    url = thumb_info['page_url']
    table = 'album' if thumb.get_type() == Thumb.ALBUM else 'image'
    rowid = self.db.add_row(table, thumb_info)
    print 'Added %s %d: %s' % (table, rowid, url)
    if thumb.get_type() == Thumb.ALBUM:
      for child in Thumb.get_all_thumbs(url):
        self._process_thumb(child, rowid)

  def scrape_image_sizes(self):
    if not self.is_scrape_image_sizes_complete():
      images = self.db.get_rows('image', 'full_size_img_url is null')
      for img_info in images:
        self._process_image(img_info)
      assert self.is_scrape_image_sizes_complete()

  def is_scrape_image_sizes_complete(self):
    done = self.db.count_rows('image', 'full_size_img_url not null')
    todo = self.db.count_rows('image', 'full_size_img_url is null')
    if todo > 0:
      print 'There are %d more images to get sizes for' % todo
      return False
    elif done > 0:
      print 'Image sizes have been scraped for %d images' % done
      return True
    else:
      print 'Oops, there are no images yet, need to scrape_thumbs() first'
      return False

  def _process_image(self, img_info):
    rowid = img_info['id']
    url = img_info['page_url']
    image = Image.Image(url)
    update_info = image.get_update_info()
    print rowid, url,
    for size_info in image.get_size_infos():
      size_info['parent'] = rowid
      self.db.add_row('size', size_info)
      print '%sx%s' % (size_info['width'], size_info['height']),
    # Do this last to ensure all sizes are recorded first.
    # TODO: this should be in a transaction, otherwise you may end up with
    # duplicate size info if the scraper is interrupted.
    self.db.update_row_by_field('image', 'id', rowid, update_info)
    print ''

  def scrape_comments(self):
    for table in ('image', 'album'):
      items = self.db.get_rows(table, 'num_comments > 0')
      for info in items:
        self._process_comments(table, info)
        print 'Saved comments for: ' + info['page_url']

  def _process_comments(self, table, info):
    rowid = info['id']
    url = info['page_url']
    # TODO.  Something like this:
    # 'block-comment-ViewComments' / 'one-comment' / p.comment, p.info
    comments = Comment.get_comments(url)
    for comment in comments:
      comment['parent'] = rowid
      self.db.add_row(table + '_comment', comment)

  def scrape_image_files(self):
    images = self.db.get_rows('image', 'full_size_img_url not null')
    in_cache_count = 0
    for img_info in images:
      rowid = img_info['id']
      url = img_info['full_size_img_url']
      if Util.check_get_url(url):
        in_cache_count += 1 # Image was already in cache.
      else:
        if in_cache_count > 0:
          print 'Found %d images already in cache' % in_cache_count
          in_cache_count = 0
        print 'Cached image #%d: %s' % (rowid, url)
    if in_cache_count > 0:
      print 'Found %d images in cache' % in_cache_count
    print 'A total of %d images are in the cache' % len(images)

if __name__ == '__main__':
  s = Scrape('gallery.db')

  # Scraping thumbnails is an all-or-nothing operation.  If it fails, delete
  # the database file (manually), fix code if needed, and start over.  Once
  # successfully completed, it will be skipped on subsequent runs.
  s.scrape_thumbs(Site.BASE_URL, Site.ALBUM_NAME)

  # Scraping image sizes is incremental.  Probably OK to interrupt this and
  # restart it later, although it might result in duplicate entries in the
  # 'size' table.
  s.scrape_image_sizes()

  # Scraping comments should be fast since all the HTML pages are already
  # in the cache, and not all pages have comments.  This code is incomplete.
  #s.scrape_comments() # TODO (maybe)

  # This is the interesting part: downloading the full-size image files.
  # Files are saved to the UrlCache.  No database updates are made, so this
  # is also interruptable.
  s.scrape_image_files()
