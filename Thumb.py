import re
import Util

ITEM = 1
ALBUM = 2
ALBUM_PREFIX = 'Album: '

def get_thumbs_from_soup(soup):
  '''Get a list of thumbnails on this page, as <td> elements'''
  table = soup('table', { 'id' : 'gsThumbMatrix' })[0]
  # Filter out the empty <td> elements used for table spacing.
  return [ t for td in table('td') for t in [Thumb(td)] if t.get_type() ]

def get_other_page_urls(soup):
  pages = soup('div', 'block-core-Pager')[0]
  # Return full URLs for pages 2, 3, ...
  return [ Util.full_url(a['href']) for a in pages('a') ]

def get_all_thumbs(album_url):
  soup = Util.get_soup(album_url)
  thumbs = get_thumbs_from_soup(soup)
  urls = get_other_page_urls(soup)
  for url in urls:
    soup = Util.get_soup(url)
    thumbs += get_thumbs_from_soup(soup)
  return thumbs

def find_albums_in(parent_album_url, regexp=None):
  thumbs = get_all_thumbs(parent_album_url)
  if not regexp:
    return [ t for t in thumbs if t.get_type() == ALBUM ]
  else:
    return [ t for t in thumbs if t.get_type() == ALBUM
                              and re.search(regexp, t.get_name()) ]

class Thumb(object):
  def __init__(self, thumb_soup):
    self.thumb = thumb_soup
    self.type = self._get_type()
    if self.type:
      self.a = thumb_soup('a')[0]   # <a href=><img src= alt= longdesc=/></a>
      self.img = self.a('img')[0]   # <img...>
      img_class = self.img['class']
      if img_class != 'giThumbnail':
        print 'Unexpected image class: ' + img_class

  def _get_type(self):
    try:
      thumb_class = self.thumb['class']
      if 'giItemCell' in thumb_class:
        return ITEM
      elif 'giAlbumCell' in thumb_class:
        return ALBUM
      else:
        print 'Unknown thumbnail type: ' + thumb_class
    except:
      pass
    return None

  def get_type(self):
    return self.type

  def get_name(self):
    try: name1 = self.img['alt'] # My Album
    except: name1 = None

    try: name2 = contents(self.thumb('p', 'giTitle')) # Album: My Album
    except: name2 = None

    if not name2: return name1
    if self.get_thumb_type() == ThumbType.ALBUM:
      if name2.startswith(ALBUM_PREFIX):
        name2 = name2[len(ALBUM_PREFIX):]
    if name1 != name2:
      print 'Item has two names:'
      print '  1. ' + name1
      print '  2. ' + name2
    return name2

  def get_short_desc(self):
    try: return contents(self.thumb('p', 'giDescription'))
    except: return None

  def get_long_desc(self):
    try: return self.img['longdesc']
    except: return None

  def get_a_href(self):
    return Util.full_url(self.a['href'])

  def get_info(self):
    result = {}
    #result['type'] = self.type
    result['name'] = self.get_name()
    result['short_desc'] = self.get_short_desc()
    result['long_desc'] = self.get_long_desc()

    #owner = Util.contents(self.thumb('div', 'owner summary'))
    #result['owner'] = Util.get_match('Owner: (.*)', owner)

    album_date = Util.contents(self.thumb('div', 'date summary'))
    result['date'] = Util.date(Util.get_match('Date: ([-/0-9]*)', album_date))

    if self.get_type() == ITEM:
      result['image_page_url'] = self.get_a_href()
    else:
      result['album_url'] = self.get_a_href()
      result['highlight_pic_url'] = Util.full_url(self.img['src'])
      album_size = Util.contents(self.thumb('div', 'size summary'))
      num_items = Util.get_match('Size: ([0-9]*) items?', album_size)
      tot_items = Util.get_match('([0-9]*) items? total', album_size) or num_items
      result['num_items'] = num_items
      result['tot_items'] = tot_items

    # Only appears if item has been viewed.
    view_div = self.thumb('div', 'viewCount summary')
    if view_div:
      album_views = Util.contents(view_div)
      result['num_views'] = Util.get_match('Views: ([0-9]*)', album_views)
    else:
      result['num_views'] = '0'

    # Only appears if there are actually comments.
    comment_div = self.thumb('div', 'summary-comment summary')
    if comment_div:
      album_comments = Util.contents(comment_div)
      result['num_comments'] = Util.get_match('Comments: ([0-9]*)', album_comments)

    return result
