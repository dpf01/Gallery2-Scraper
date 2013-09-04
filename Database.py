import sqlite3

class Schema(object):
  def __init__(self):
    self.field_defs = {
      'album' : [
        'id                INTEGER PRIMARY KEY AUTOINCREMENT',
        'parent            INTEGER REFERENCES album(id)',
        'name              TEXT',
        'short_desc        TEXT',
        'long_desc         TEXT',
        'date              TEXT',
        'album_url         TEXT',
        'highlight_pic_url TEXT',
        'num_items         INTEGER',
        'tot_items         INTEGER',
        'num_views         INTEGER',
        'num_comments      INTEGER',
        'state             INTEGER',
        ],

      'image' : [
        'id                INTEGER PRIMARY KEY AUTOINCREMENT',
        'parent            INTEGER REFERENCES album(id)',
        'name              TEXT', # AKA title?
        'short_desc        TEXT',
        'long_desc         TEXT',
        'date              TEXT',
        'image_page_url    TEXT',
        'full_size_img_url TEXT',
        'width             INTEGER',
        'height            INTEGER',
        'num_views         INTEGER',
        'num_comments      INTEGER',
        'state             INTEGER',
        ],

      'size' : [
        'id                INTEGER PRIMARY KEY AUTOINCREMENT',
        'parent            INTEGER REFERENCES image(id)',
        'width             INTEGER',
        'height            INTEGER',
        'page_url          TEXT',
        'image_url         TEXT',
        'is_full_size      BOOLEAN',
        ],

      'img_comment' : [
        'id                INTEGER PRIMARY KEY AUTOINCREMENT',
        'parent            INTEGER REFERENCES image(id)',
        'comment           TEXT',
        'author            TEXT',
        'date              TEXT',
        ],

      'alb_comment' : [
        'id                INTEGER PRIMARY KEY AUTOINCREMENT',
        'parent            INTEGER REFERENCES image(id)',
        'comment           TEXT',
        'author            TEXT',
        'date              TEXT',
        ],
      }

    self.field_names = { t: [ fd.split()[0] for fd in fds ]
                         for t, fds in self.field_defs.iteritems() }

  def create_tables(self, fname):
    with sqlite3.connect(fname) as con:
      cur = con.cursor()
      for table, field_list in self.field_defs.iteritems():
        field_str = ',\n  '.join(field_list)
        cmd = 'CREATE TABLE IF NOT EXISTS %s (\n  %s );' % (table, field_str)
        #print cmd
        cur.execute(cmd);

  def fields(self, table):
    return self.field_names[table]


class DbException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class Database(object):
  def __init__(self, fname):
    self.fname = fname
    self.schema = Schema()

  def make_tables(self):
    self.schema.create_tables(self.fname)

  def add_row(self, table, data):
    self._verify_fields_are_in_schema(table, data)
    values = [ data.get(f) for f in self.schema.fields(table) ]
    places = ','.join(['?'] * len(values))
    cmd = 'INSERT INTO %s VALUES (%s)' % (table, places)
    cur = self._run_cmd(cmd, values)
    return cur.lastrowid

  def count_rows(self, table, criteria=None):
    self._verify_table_is_in_schema(table)
    cmd = 'SELECT COUNT(*) FROM %s %s' % (table, self._get_where(criteria))
    return self._run_cmd(cmd).fetchone()[0]

  def get_rows(self, table, criteria=None):
    self._verify_table_is_in_schema(table)
    cmd = 'SELECT * FROM %s %s' % (table, self._get_where(criteria))
    cur = self._run_cmd(cmd)
    return [ self._build_row(table, row) for row in cur.fetchall() ]
    # Returning an iterator locks the database, so updates aren't allowed.
    # Had to just return a list for scrape_image_sizes() to work.
    # TODO: return a cursor so calling code can update last-row?
    #while True:
    #  row = cur.fetchone()
    #  if not row:
    #    return
    #  yield self._build_row(table, row)

  def _get_where(self, criteria):
    if not criteria:
      return ''
    return 'WHERE (%s)' % criteria  # Danger, SQL injection!

  def get_row_by_field(self, table, field, value):
    self._verify_field_is_in_schema(table, field)
    cmd = 'SELECT * FROM %s WHERE %s=?' % (table, field)
    cur = self._run_cmd(cmd, [value])
    rows = cur.fetchall()
    if not rows or len(rows) == 0:
      raise DbException('No rows returned from query: ' + cmd)
    if len(rows) > 1:
      raise DbException('Multiple rows (%d) returned for query: %s'
        % (len(rows), cmd))
    return self._build_row(table, rows[0])

  def _build_row(self, table, row):
    return dict(zip(self.schema.fields(table), row))

  def update_row_by_field(self, table, field, value, data):
    self._verify_field_is_in_schema(table, field)
    self._verify_fields_are_in_schema(table, data)
    set_str = ', '.join([ f + '=?' for f, v in data.iteritems() ])
    set_vals = [ v for f, v in data.iteritems() ]
    cmd = 'UPDATE %s SET %s WHERE %s=?' % (table, set_str, field)
    self._run_cmd(cmd, set_vals + [value])

  def _verify_table_is_in_schema(self, table):
    if not self.schema.fields(table):
      raise DbException('Invalid table: ' + table)

  def _verify_field_is_in_schema(self, table, field):
    if not field in self.schema.fields(table):
      raise DbException('Invalid field: ' + field)

  def _verify_fields_are_in_schema(self, table, data):
    s = self.schema.fields(table)
    invalid = [ f for f, v in data.iteritems() if not f in s ]
    if invalid:
      raise DbException('Invalid field: ' + invalid)

  def _run_cmd(self, cmd, values=None):
    if values == None:
      values = []
    #print cmd, values
    with sqlite3.connect(self.fname) as con:
      cur = con.cursor()
      cur.execute(cmd, tuple(values))
      return cur
