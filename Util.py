from urlparse import urljoin
import re
import HTMLParser
import BeautifulSoup
import UrlCache

CACHE_DIR = 'cache'
cache = UrlCache.UrlCache(CACHE_DIR)

def get_soup(url):
  '''Get the relevant part of the page'''
  response = cache.get(url)
  soup = BeautifulSoup.BeautifulSoup(response)
  return soup('div', id='gsContent')[0]

BASE_URL = ''

def assert_equals(a, b):
  if a != b:
    raise AssertionError('"%s" != "%s"' % (a, b))

def set_base_url(url):
  global BASE_URL
  BASE_URL = url

def full_url(url):
  return urljoin(BASE_URL, url)

unescaper = HTMLParser.HTMLParser()
def unescape_html(html):
  '''Unescape things like &amp; &lt; &quot;'''
  return unescaper.unescape(html)

def contents(blocks):
  b = blocks[0] if isinstance(blocks, list) else blocks
  return unescape_html(b.string.strip())

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
