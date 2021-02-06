#!/usr/bin/python3
# -*- conding:utf-8 -*-

import sqlite3
import logging

class Db:

    DB_FILE = 'ebook-dl.db'
    _LOGGER = logging.getLogger(__name__)

    SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE = """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL UNIQUE
        );"""


    def __init__(self):
        self.conn = None

    def create_connection(self):
        try:
            self.conn = sqlite3.connect(self.DB_FILE)
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db connection error: {e}')
    

    def create_table(self, create_table_sql):
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db create table error: {e}')


    def insert_profile_urls(self, urls):
        sql = """ REPLACE INTO profile (url) VALUES (?) """
        try:
            cur = self.conn.cursor()
            for url in urls:
                cur.execute(sql, (url,))
            self.conn.commit()
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db insertion error: {e}')


    def store_profile_page_urls(self, profile_page_urls):
        self.create_connection()
        self.create_table(self.SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE)
        self.insert_profile_urls(profile_page_urls)
        self.close_connection()


    def close_connection(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    db = Db()
    db.create_connection()
    db.create_table(db.SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE)
    db.insert_profile_urls(['url1', 'url2'])
    db.close_connection()
