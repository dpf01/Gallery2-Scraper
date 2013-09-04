import Util

class Image(object):
  '''An Image object is created based on the image pages for each resolution
  of a given image.
  '''
  def __init__(self, image_page_url):
    main_soup = Util.get_soup(image_page_url)
    sizes_div = main_soup('div', 'block-core-PhotoSizes giInfo')[0]
    select = sizes_div('select')[0]
    self.main_page_url = image_page_url
    self.full_size_img_url = ''
    self.full_size = Util.contents(sizes_div('a')[0])
    self.width, self.height = self.full_size.split('x')
    self.size_info = [ self._get_size_info(opt) for opt in select('option') ]

  def _get_size_info(self, opt):
    size = Util.contents(opt)
    link = Util.full_url(opt['value'])
    selected = opt.has_key('selected') and opt['selected'] == 'selected'
    if selected and link == self.main_page_url + '?g2_imageViewsIndex=0':
      link = self.main_page_url
    page_soup = Util.get_soup(link)
    img_div = page_soup('div', { 'id' : 'gsImageView' })[0]
    img = img_div('img')[0]

    info = {}
    self._add_size_to_info(info, size, link, img)
    info['page_url'] = link
    info['image_url'] = Util.full_url(img['src'])
    info['is_full_size'] = size == self.full_size
    if info['is_full_size']:
      self.full_size_img_url = link
    return info

  def _add_size_to_info(self, info, size, link, img):
    if size != 'Unknown':
      info['width'], info['height'] = size.split('x')
      Util.assert_equals(info['width'], img['width'])
      Util.assert_equals(info['height'], img['height'])
    elif img.has_key('width') and img.has_key('height'): # Unlikely
      info['width'] = img['width']
      info['height'] = img['height']
    else:
      print 'No size info for image: ' + link

  def get_size_infos(self):
    return self.size_info

  def get_update_info(self):
    result = {}
    result['full_size_img_url'] = self.full_size_img_url
    result['width'] = self.width
    result['height'] = self.height
    return result
