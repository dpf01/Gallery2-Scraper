import Util

def _get_size(block):
  size_text = Util.contents(block)
  return Util.get_match('([0-9]+x[0-9]+)', size_text)

def _get_img_tag(soup):
  img_div = soup('div', { 'id' : 'gsImageView' })[0]
  img = img_div('img')[0]
  return img

class Image(object):
  '''An Image object is created based on the image pages for each resolution
  of a given image.'''
  def __init__(self, image_page_url):
    self.main_page_url = image_page_url
    main_soup = Util.get_soup(image_page_url)
    sizes_div = main_soup('div', 'block-core-PhotoSizes giInfo')[0]
    selects = sizes_div('select') # 0 or 1 select tags.
    if selects:
      options = selects[0]('option')
      self.full_size_img_url = ''
      self.full_size = _get_size(sizes_div('a')[0])
      self.width, self.height = self._get_dimensions(self.full_size)
      self.size_info = [ self._get_size_info(opt) for opt in options ]
    else: # Only one size for this image.
      img = _get_img_tag(main_soup)
      self.full_size_img_url = Util.full_url(img['src'])
      self.full_size = _get_size(sizes_div)
      self.width, self.height = self._get_dimensions(self.full_size, img)
      self.size_info = []

  def _get_size_info(self, opt):
    size = Util.contents(opt)
    link = Util.full_url(opt['value'])
    selected = opt.has_key('selected') and opt['selected'] == 'selected'
    if selected and link == self.main_page_url + '?g2_imageViewsIndex=0':
      link = self.main_page_url
    page_soup = Util.get_soup(link)
    img = _get_img_tag(page_soup)

    info = {}
    info['width'], info['height'] = self._get_dimensions(size, img)
    info['page_url'] = link
    info['image_url'] = Util.full_url(img['src'])
    info['is_full_size'] = size == self.full_size
    if info['is_full_size']:
      self.full_size_img_url = info['image_url']
    return info

  def _get_dimensions(self, size, img=None):
    if size and 'x' in size: # Size can be 'Unknown'.
      w, h = size.split('x')
      if img:
        Util.assert_equals(w, img['width'])
        Util.assert_equals(h, img['height'])
    elif img and img.has_key('width') and img.has_key('height'): # Unlikely
      w = img['width']
      h = img['height']
    else:
      print 'No size info for image: ' + self.main_page_url
      w = None
      h = None
    return (w, h)

  def get_size_infos(self):
    return self.size_info

  def get_update_info(self):
    result = {}
    result['full_size_img_url'] = self.full_size_img_url
    result['width'] = self.width
    result['height'] = self.height
    return result
