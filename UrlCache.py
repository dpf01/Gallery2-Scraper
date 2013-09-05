from urlparse import urlparse
import errno
import hashlib
import os
import time
import urllib2

def _mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

def _open_url_with_retries(url):
  attempts = 3
  delay = 1
  while True:
    try:
      return urllib2.urlopen(url)
    except urllib2.URLError as e:
      attempts -= 1
      if attempts <= 0:
        raise
      print 'Failed to fetch URL, retrying in %ds: %s' % (delay, url)
      time.sleep(delay)
      delay *= 2

def _copy_data_to_disk(fd, filename):
  try:
    with open(filename, 'wb') as f:
      data = fd.read()
      f.write(data)
      return data
  except:
    os.remove(filename)
    raise

class UrlCache(object):
  def __init__(self, root_dir):
    self.root = root_dir
    self.list = os.path.join(self.root, 'files.txt')

  def get(self, url):
    '''Get the data from a URL.  The page will be cached to disk so no
    network access is needed on a subsequent fetch.  This disrespects
    typical notions of a web cache, since pages are always cached and
    never expire.'''
    filename = self._get_cached_url_filename(url)
    if os.path.exists(filename):
      with open(filename, 'rb') as f:
        return f.read()
    return self._add_url_to_cache(url, filename)

  def _get_cached_url_filename(self, url):
    url_hash = hashlib.sha224(url).hexdigest()
    extension = os.path.splitext(urlparse(url).path)[1].strip().lower()
    dir = os.path.join(self.root, url_hash[:2]) #, url_hash[2:4])
    _mkdir_p(dir)
    return os.path.join(dir, url_hash + extension)

  def _add_url_to_cache(self, url, filename):
    # Download the file and write it to disk.
    url_fd = _open_url_with_retries(url)
    data = _copy_data_to_disk(url_fd, filename)

    # Write the file-to-url mapping to a list.
    try:
      with open(self.list, 'a') as f:
        f.write(filename + ' -- ' + url + '\n')
    except:
      pass

    # Return the downloaded file data.
    return data
