from urlparse import urljoin
import re
import HTMLParser
import BeautifulSoup
import Site
import UrlCache

_CACHE_DIR = 'cache'
_cache = UrlCache.UrlCache(_CACHE_DIR)

def check_get_url(url):
  return _cache.check_get(url)

def get_soup(url):
  '''Get the relevant part of the page'''
  response = _cache.get(url)
  soup = BeautifulSoup.BeautifulSoup(response)
  return soup('div', id='gsContent')[0]

def full_url(url):
  return urljoin(Site.BASE_URL, url)

_unescaper = HTMLParser.HTMLParser()
def unescape_html(html):
  '''Unescape things like &amp; &lt; &quot;'''
  return _unescaper.unescape(html)

def contents(blocks):
  b = blocks[0] if isinstance(blocks, list) else blocks
  return unescape_html(b.contents[0].strip())

def date(text):
  return re.sub(
    #   ---month---      ----day----      ---19xx-----|----20xx---
    r'^([0-1]?[0-9])[-/]([0-3]?[0-9])[-/](19[0-9][0-9]|20[0-9][0-9])$',
    r'\3-\1-\2', text)

def get_match(regexp, text):
  try:
    return re.search(regexp, text).group(1)
  except:
    return None

def assert_equals(a, b):
  if a != b:
    raise AssertionError('"%s" != "%s"' % (a, b))
