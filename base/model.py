from ConfigParser import ConfigParser
from DBUtils.PersistentDB import PersistentDB

import MySQLdb
import re


def x_str(s):
    return '' if s is None else str(s)


class Model():
    def __init__(self, config_file, db_section=None):
        self.db_section = db_section
        self.config_file = config_file
        self.config = ConfigParser()
        self.config.read(self.config_file)
        self.conn = None
        self.cursor = None
        self.reset_var()
        self.pool = None

    def open_pool(self):
        self.pool = PersistentDB(MySQLdb, host=self.config.get(self.db_section, 'dbhost'),
                                 user=self.config.get(self.db_section, 'dbuser'),
                                 passwd=self.config.get(self.db_section, 'dbpwd'),
                                 db=self.config.get(self.db_section, 'dbname'),
                                 charset='utf8')

    def open_conn_cursor(self, pool):
        self.conn = pool.connection()
        self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)

    def close_conn_cursor(self):
        self.cursor.close()
        self.conn.close()

    def is_number(self, s):
        if type(s) is str:
            intstr = ['Infinity', 'infinity', 'nan', 'inf', 'NAN', 'INF']
            if intstr.count(s.lower()) or re.match(r'[0-9]+(e|E)[0-9]+', s):
                return False

        try:
            float(s)
            return True
        except Exception:
            pass

        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except Exception:
            pass

        return False

    def value_update(self, data, primary):
        try:
            if not isinstance(primary, list):
                primaries = primary.replace(' ', '').split(',')
            else:
                primaries = primary
            sets = list()
            keys = data.keys()
            for key in keys:
                if key not in primaries:
                    if data[key] is not None:
                        try:
                            data[key] = data[key].encode('utf-8')
                        except Exception:
                            pass

                        if self.is_number(data[key]):
                            sets.append('{0} = {1}'.format(str(key), data[key]))
                        else:
                            sets.append('{0} = "{1}"'.format(str(key), MySQLdb.escape_string(str(data[key]))))
                    else:
                        sets.append('{} = NULL'.format(str(key)))

            return ", ".join(sets)
        except Exception, e:
            raise Exception(e)

    def reset_var(self):
        self.q_update_set = None
        self.q_select = None
        self.q_where = None
        self.q_join = None
        self.q_order = None
        self.sql = None
        self.sql_insert = None
        self.sql_delete = None
        self.delete_all = None
        self.sql_update = None
        self.q_group_by = None
        self.q_limit = None

    def select(self, table, alias=None, field="*"):
        if isinstance(field, list):
            field = ", ".join(field)
        if alias is None:
            alias = table
        self.q_select = "SELECT {} FROM {} {}".format(field, table, alias)

    def join(self, table, alias, using=None, on=None, join_type=''):
        condition = ''
        if using:
            condition = "USING({})".format(using)
        elif on:
            condition = "ON {}".format(on)
        if join_type.upper() not in ['LEFT', 'RIGHT', 'INNER']:
            join_type = ''
        q_join = "{} JOIN {} {} {}".format(join_type.upper(), table, alias, condition)
        if self.q_join:
            self.q_join = "{} {}".format(self.q_join, q_join)
        else:
            self.q_join = q_join

    def order(self, by=None, reverse=False, random=False):
        order_type = "ASC"
        if reverse:
            order_type = "DESC"
        if random:
            q_order = 'RAND()'
        elif by:
            q_order = '{} {}'.format(by, order_type)
        if self.q_order:
            self.q_order = '{}, {}'.format(self.q_order, q_order)
        else:
            self.q_order = "ORDER BY {}".format(q_order)

    def limit(self, offset=None, limit=None):
        if offset and limit:
            self.q_limit = "LIMIT {}, {}".format(offset, limit)
        elif limit:
            self.q_limit = "LIMIT {}".format(limit)

    def where(self, condition, operator='AND'):
        if isinstance(condition, list):
            pass
        if self.q_where:
            self.q_where = "{} {} {}".format(self.q_where, operator, condition)
        else:
            self.q_where = 'WHERE {}'.format(condition)

    def exact_where(self, column, value, operator='AND'):
        if column and value:
            self.where("{} = '{}'".format(column, MySQLdb.escape_string(value)), operator)

    def group_by(self, field):
        self.q_group_by = "GROUP BY {}".format(field)

    def insert(self, table, data, update=False, key=None):
        if isinstance(data, dict):
            fields = []
            values = []
            for d in data:
                fields.append(d)
                if isinstance(data[d], unicode):
                    value = data[d].encode('utf-8')
                else:
                    value = data[d]
                values.append(MySQLdb.escape_string(str(value)))
            self.sql_insert = "INSERT INTO {}({}) VALUES ('{}')".format(table, ", ".join(fields), "', '".join(values))
            if update:
                value_update = self.value_update(data, key)
                self.sql_insert += ' ON DUPLICATE KEY UPDATE {}'.format(value_update)
        elif isinstance(data, list):
            fields = []
            values = []
            for dat in data:
                if not fields:
                    for d in dat:
                        fields.append(d)
                value = []
                for field in fields:
                    value.append(str(dat[field]))
                values.append("('{}')".format("', '".join(value)))
            self.sql_insert = "INSERT INTO {}({}) VALUES {}".format(table, ", ".join(fields), ", ".join(values))

    def delete(self, table, delete_all=False):
        self.sql_delete = "DELETE FROM {}".format(table)
        if delete_all is True:
            self.delete_all = True

    def update(self, table, data=None):
        if data:
            for column, value in data.iteritems():
                self.update_set(column, MySQLdb.escape_string(str(value)))
        self.sql_update = "UPDATE {}".format(table)

    def update_set(self, column, value, inc=None):
        if not self.q_update_set:
            self.q_update_set = list()

        if column and value:
            if inc is None:
                self.q_update_set.append("{} = '{}'".format(column, value))
            elif inc is False:
                self.q_update_set.append("{0} = {0} - {1}".format(column, value))
            else:
                self.q_update_set.append("{0} = {0} + {1}".format(column, value))

    def query(self, sql):
        self.sql = sql

    def execute(self, commit=True, count=False):
        rows = None
        rowscount = None
        if self.sql_insert:
            sql = self.sql_insert
            self.cursor.execute(sql)
        elif self.sql_delete and self.q_where:
            sql = "{} {}".format(self.sql_delete, self.q_where)
            self.cursor.execute(sql)
        elif self.sql_delete and self.sql_delete:
            sql = self.sql_delete
            self.cursor.execute(sql)
        elif self.sql_update and self.q_where:
            set_clause = ", ".join(self.q_update_set)
            sql = "{} SET {} {}".format(self.sql_update, set_clause, self.q_where)
            self.cursor.execute(sql)
        elif self.sql:
            sql = self.sql
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
        else:
            sql = "{} {} {} {} {} {}".format(x_str(self.q_select), x_str(self.q_join), x_str(self.q_where),
                                             x_str(self.q_group_by),
                                             x_str(self.q_order),
                                             x_str(self.q_limit))
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            if count:
                self.cursor.execute('SELECT FOUND_ROWS() AS rowscount')
                rowscount = self.cursor.fetchone()['rowscount']

        if commit:
            self.conn.commit()
        lastrowid = self.cursor.lastrowid
        self.reset_var()

        return Return(sql=sql, rows=rows, rowscount=rowscount, lastrowid=lastrowid)


class Return:
    def __init__(self, sql, rows, rowscount=0, lastrowid=None):
        self.sql = sql
        self.data = rows
        self.rowscount = rowscount
        self.fetchall = rows
        self.fetchone = dict()
        self.lastrowid = lastrowid
        if rows:
            self.fetchone = rows[0]
