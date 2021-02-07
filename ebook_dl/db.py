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
            resource_url TEXT,
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
                        (book_id, book_info.tn_url)
                    )
            self.conn.commit()
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db insertion book_info error: {e}')


    def select_profile_urls(self):
        self.create_connection()
        rows = []
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT url from profile')
            rows = [row[0] for row in cur.fetchall()]
        except sqlite3.Error as e:
            Db._LOGGER.error(f'Db selection error: {e}')
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


    def close_connection(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    db = Db()
    db.DB_FILE = '../ebook-dl.db'
    #db.create_connection()
    #db.create_table(db.SQL_CREATE_BOOK_PROFILE_PAGE_URLS_TABLE)
    #db.insert_profile_urls(['url1', 'url2'])
    #l = db.select_profile_urls()
    class BookInfo:
        def __init__(self):
            self.title = ''
            self.details = ''
            self.description = ''
            self.tn_url = ''
    bookInfo1, bookInfo2 = BookInfo(), BookInfo()
    bookInfo1.title = 'book title 1'
    bookInfo1.details = 'book details 1'
    bookInfo1.description = 'book description 1'
    bookInfo1.tn_url = 'tn_url 1'
    bookInfo2.title = 'book title 2'
    bookInfo2.details = 'book details 2'
    bookInfo2.description = 'book description 2'
    bookInfo2.tn_url = 'tn_url 2'
    db.store_book_info_collection([bookInfo1, bookInfo2])
    #db.close_connection()
