from urlparse import urlparse
import errno
import hashlib
import os
import urllib
import urllib2

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

class UrlCache(object):
  def __init__(self, root_dir):
    self.root = root_dir
    self.list = os.path.join(self.root, 'files.txt')

  def _get_cached_url_filename(self, url):
    url_hash = hashlib.sha224(url).hexdigest()
    extension = os.path.splitext(urlparse(url).path)[1].strip().lower()
    dir = os.path.join(self.root, url_hash[:2]) #, url_hash[2:4])
    mkdir_p(dir)
    return os.path.join(dir, url_hash + extension)

  def _add_url_to_cache(self, url, filename):
    # Download the file and write it to disk.
    url_fd = urllib2.urlopen(url)
    try:
      with open(filename, 'wb') as f:
        data = url_fd.read()
        f.write(data)
    except:
      os.remove(filename)
      raise

    # Write the file-to-url mapping to a list.
    try:
      with open(self.list, 'a') as f:
        f.write(filename + ' -- ' + url + '\n')
    except:
      pass

    # Return the downloaded file data.
    return data

  def get(self, url):
    filename = self._get_cached_url_filename(url)
    if os.path.exists(filename):
      with open(filename, 'rb') as f:
        return f.read()
    return self._add_url_to_cache(url, filename)

