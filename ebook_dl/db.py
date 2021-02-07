#!/usr/bin/python3
# -*- conding:utf-8 -*-

import sqlite3
import logging

class BookInfo:
    def __init__(self):
        self.id = ''
        self.title = ''
        self.details = ''
        self.description = ''
        self.tn_url = []
        self.resource_url = []


class BookUrl:
    def __init__(self, id='', book_id='', tn_url='', resource_url=''):
        self.id = id
        self.book_id = book_id
        self.tn_url = tn_url
        self.resource_url = resource_url


class Db:

    DB_FILE = 'ebook-dl.db'
    _LOGGER = logging.getLogger(__name__)

    SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE = """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL UNIQUE
        );"""

    SQL_CREATE_BOOK_INFO_TABLE = """
        CREATE TABLE IF NOT EXISTS book_info (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            details TEXT,
            description TEXT
        );"""
    
    SQL_CREATE_BOOK_URL_TABLE = """
        CREATE TABLE IF NOT EXISTS book_url (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            tn_url TEXT NOT NULL UNIQUE,
            resource_url TEXT DEFAULT (''),
            FOREIGN KEY (book_id) REFERENCES book_info (id)
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
        sql = """ INSERT OR IGNORE INTO profile (url) VALUES (?) """
        try:
            cur = self.conn.cursor()
            for url in urls:
                cur.execute(sql, (url,))
            self.conn.commit()
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db insertion profile error: {e}')


    def update_book_url_collection(self, book_url_collection):
        sql = """ 
            UPDATE book_url
            SET resource_url = ?
            WHERE id = ?
        """
        try:
            cur = self.conn.cursor()
            for book_url in book_url_collection:
                cur.execute(sql, (book_url.resource_url, book_url.id))
            self.conn.commit()
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db update book url error: {e}')


    def insert_book_info_collection(self, info_collection):
        sql_insert_book_info = """
            INSERT OR IGNORE INTO book_info (title,details,description) VALUES (?,?,?)
        """
        sql_select_book_info = """
            SELECT id FROM book_info WHERE title=?
        """
        sql_insert_book_url = """
            INSERT OR IGNORE INTO book_url (book_id,tn_url) VALUES (?,?)
        """
        try:
            cur = self.conn.cursor()
            for book_info in info_collection:
                cur.execute(
                    sql_insert_book_info, 
                    (
                        book_info.title,
                        book_info.details,
                        book_info.description
                    )
                )
            self.conn.commit()
            for book_info in info_collection:
                cur.execute(sql_select_book_info, (book_info.title,))
                book_record = cur.fetchone()
                if book_record and book_info.tn_url:
                    book_id = book_record[0]
                    cur.execute(
                        sql_insert_book_url,
                        (book_id, book_info.tn_url[0])
                    )
            self.conn.commit()
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db insertion book_info error: {e}')


    def select_all_profile_urls(self):
        self.create_connection()
        rows = []
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT url FROM profile')
            rows = [row[0] for row in cur.fetchall()]
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db selection all profile urls error: {e}')
        finally:
            self.close_connection()
        return rows


    def select_all_book_urls(self, use_resource_url=False):
        if use_resource_url:
            sql = 'SELECT * FROM book_url WHERE resource_url <> ""'
        else:
            sql = 'SELECT * FROM book_url WHERE resource_url = ""'
        self.create_connection()
        rows = []
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            rows = [BookUrl(row[0], row[1], row[2], row[3]) for row in cur.fetchall()]
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db selection all book urls error: {e}')
        finally:
            self.close_connection()
        return rows


    def store_profile_page_urls(self, profile_page_urls):
        if not profile_page_urls:
            return
        self.create_connection()
        self.create_table(self.SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE)
        self.insert_profile_urls(profile_page_urls)
        self.close_connection()


    def store_book_info_collection(self, book_info_collection):
        if not book_info_collection:
            return
        self.create_connection()
        self.create_table(self.SQL_CREATE_BOOK_INFO_TABLE)
        self.create_table(self.SQL_CREATE_BOOK_URL_TABLE)
        self.insert_book_info_collection(book_info_collection)
        self.close_connection()


    def store_book_url_collection(self, book_url_collection):
        if not book_url_collection:
            return
        self.create_connection()
        self.update_book_url_collection(book_url_collection)
        self.close_connection()


    def close_connection(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    db = Db()
    db.DB_FILE = '../ebook-dl.db'
    #db.create_connection()
    #db.create_table(db.SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE)
    #db.insert_profile_urls(['url1', 'url2'])
    #l = db.select_all_profile_urls()
    bookInfo1, bookInfo2 = BookInfo(), BookInfo()
    bookInfo1.title = 'book title 1'
    bookInfo1.details = 'book details 1'
    bookInfo1.description = 'book description 1'
    bookInfo1.tn_url = ['tn_url 1']
    bookInfo2.title = 'book title 2'
    bookInfo2.details = 'book details 2'
    bookInfo2.description = 'book description 2'
    bookInfo2.tn_url = ['tn_url 2']
    db.store_book_info_collection([bookInfo1, bookInfo2])
    #db.close_connection()
