import re
import Util

IMAGE = 1
ALBUM = 2
ALBUM_PREFIX = 'Album: '

def _check_empty_page(soup, element):
  empty = soup('div', 'gbEmptyAlbum')
  if not empty:
    print "Album has no %s and isn't empty." % element
  return []

def _get_thumbs_from_soup(soup):
  '''Get a list of thumbnails from the soup, as Thumb objects.'''
  tables = soup('table', { 'id' : 'gsThumbMatrix' })
  if tables:
    table = tables[0]
    # Filter out the empty <td> elements used for table spacing.
    return [ t for td in table('td') for t in [Thumb(td)] if t.get_type() ]
  return _check_empty_page(soup, "thumbs")

def _get_other_page_urls(soup):
  '''Get a list of URLs for subsequent pages of this album.'''
  urls = []
  other_soup = soup
  while True:
    navigator_div = other_soup('div', 'block-core-Navigator')
    if not navigator_div:
      break
    next_link = navigator_div[0]('a', 'next')
    if not next_link:
      break
    url = Util.full_url(next_link[0]['href'])
    urls.append(url)
    other_soup = Util.get_soup(url)
  if urls:
    return urls

  # If no next links were found, check for the "Page: 1 2 3 ... 33" <div>.
  pages_div = soup('div', 'block-core-Pager')
  if pages_div:
    pages = pages_div[0]
    return [ Util.full_url(a['href']) for a in pages('a') ]
  return _check_empty_page(soup, "pages")

def get_all_thumbs(page_url):
  '''Get all thumbnails for the given album URL, including those
  on subsequent pages of the album.'''
  soup = Util.get_soup(page_url)
  urls = _get_other_page_urls(soup)
  soups = [soup] + [ Util.get_soup(url) for url in urls ]
  return [ t for s in soups for t in _get_thumbs_from_soup(s) ]

def find_albums_in(parent_url, regexp=None):
  '''Get thumbnails representing albums within the given parent album.
  If a regexp is provided, only albums matching it are returned.'''
  thumbs = get_all_thumbs(parent_url)
  if not regexp:
    return [ t for t in thumbs if t.get_type() == ALBUM ]
  else:
    return [ t for t in thumbs if t.get_type() == ALBUM
                              and re.search(regexp, t.get_name()) ]

class Thumb(object):
  '''A Thumb object encapsulates all the information that can be obtained
  from a thumbnail (and its associated text) on an album page.  A Thumb
  may represent an image or an album.'''
  def __init__(self, thumb_soup):
    self.thumb = thumb_soup
    self.type = self._get_type()
    if self.type:
      self.a = thumb_soup('a')[0]   # <a href=><img src= alt= longdesc=/></a>

      # Highlight pic may not be present in some cases, e.g., empty album.
      self.img = None
      if self.a('img'):
        self.img = self.a('img')[0]   # <img...>
        img_class = self.img['class']
        if img_class != 'giThumbnail':
          print 'Unexpected image class: ' + img_class

  def _get_type(self):
    try:
      thumb_class = self.thumb['class']
      if 'giItemCell' in thumb_class:
        return IMAGE
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

    result['page_url'] = Util.full_url(self.a['href'])

    if self.get_type() == ALBUM:
      if self.img:
        result['highlight_pic_url'] = Util.full_url(self.img['src'])

      # Album size <div> may not be present in some cases, e.g., empty album.
      size_div = self.thumb('div', 'size summary')
      if size_div:
        album_size = Util.contents(size_div)
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
