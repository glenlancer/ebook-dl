#!/usr/bin/python3
# -*- conding:utf-8 -*-

from . import config
from .thread_manager import ThreadManager
from .db import Db

import typer
import time
import requests
import logging
from bs4 import BeautifulSoup


class Scraper:

    _MAIN_URL = 'https://itebooksfree.com/'
    _REQUEST_TIMEOUT = 15
    _LOGGER = logging.getLogger(__name__)


    def __init__(self):
        self._search_key = config.get('keyword')
        self.db = Db()
        self._book_profile_page_urls = []


    @staticmethod
    def _construct_search_api(search_key='', page=None):
        if search_key == '':
            return Scraper._MAIN_URL
        elif page is None:
            return f'{Scraper._MAIN_URL}/search/{search_key}'
        else:
            return f'{Scraper._MAIN_URL}/search/{search_key}/{page}'


    @staticmethod
    def _get_page(url):
        response = requests.get(
            url, 
            headers=config.get('fake_headers'),
            timeout=Scraper._REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.text


    @staticmethod
    def _get_bs_obj(url, retry_count):
        try:
            page_text = Scraper._get_page(url)
            return BeautifulSoup(page_text, 'html.parser')
        except Exception as e:
            Scraper._LOGGER.warning(f'{Scraper._get_bs_obj.__name__} exception: {e} for url: {url}')
            retry_count += 1
            # Sleep 1s to avoid stack overflow when sudden Internet
            # disconnection occurs.
            time.sleep(1)
            Scraper._LOGGER.warning(f'Re-try {Scraper._get_bs_obj.__name__} {retry_count} times')
            return Scraper._get_bs_obj(url, retry_count)


    @staticmethod
    def _start_get_bs_obj(url):
        return Scraper._get_bs_obj(url, 0)


    @staticmethod
    def _get_pagination_count(bs_obj):
        smaller_bs_obj = bs_obj.find('div', {'class': 'pagination'})
        if smaller_bs_obj is None:
            return 1
        pagination_bs = smaller_bs_obj.find(
            'span', {'class': 'text'}
        )
        if pagination_bs is None:
            return 1
        try:
            prefix_text = '1 / '
            suffix_text = ' Pages'
            pagination_text = pagination_bs.get_text()
            if pagination_text.startswith(prefix_text):
                pagination_text = pagination_text[len(prefix_text):]
            if pagination_text.endswith(suffix_text):
                pagination_text = pagination_text[:-len(suffix_text)]
            return int(pagination_text)
        except Exception as e:
            Scraper._LOGGER.warning(f'Pagination cast exception: {e}')
            return 1


    @staticmethod
    def _retrieve_book_profile_page_urls_from_page(bs_obj):
        urls = []
        for entry_card_bs_obj in bs_obj.find_all('div', {'class': 'card-body'}):
            link = entry_card_bs_obj.find('a')
            if 'href' in link.attrs:
                urls.append(link.attrs['href'])
        return urls


    @staticmethod
    def _calculate_start_index_and_workload(index, url_workload, extra_workload):
        if index < extra_workload:
            workload = url_workload + 1
            start_index = index * workload
        else:
            workload = url_workload
            start_index = extra_workload * (workload + 1) + (index - extra_workload) * workload
        return start_index, workload


    @staticmethod
    def _retrieve_profile_page_urls(page_index, search_key):
        index_page_url = Scraper._construct_search_api(search_key, page_index)
        page_bs = Scraper._start_get_bs_obj(index_page_url)
        return Scraper._retrieve_book_profile_page_urls_from_page(page_bs)


    @staticmethod
    def _run_profile_page_urls(thread_pools, index, url_workload, extra_workload, search_key):
        thread_profile_page_urls = []
        start_index, workload = Scraper._calculate_start_index_and_workload(
            index, url_workload, extra_workload
        )
        start_index += 2
        for i in range(start_index, start_index + workload):
            thread_profile_page_urls += Scraper._retrieve_profile_page_urls(i, search_key)
        thread_pools[index] = thread_profile_page_urls


    def _retrieve_book_profile_page_urls_from_other_page(self, page_count):
        thread_manager = ThreadManager()
        thread_manager.thread_job_distribution(page_count, ThreadManager.THREAD_PROFILE_PAGE_JOB)
        thread_manager.thread_job_preparation(
            Scraper._run_profile_page_urls,
            ThreadManager.THREAD_PROFILE_PAGE_JOB,
            self._search_key
        )
        thread_manager.thread_job_handling(self._book_profile_page_urls)


    def get_all_book_profile_page_urls(self):
        search_api = Scraper._construct_search_api(self._search_key)
        main_bs = Scraper._start_get_bs_obj(search_api)
        page_count = Scraper._get_pagination_count(main_bs)
        styled_page_count = typer.style(str(page_count), fg=typer.colors.MAGENTA, bold=True)
        typer.echo(f'There are {styled_page_count} pages in total.')
        typer.echo('Now start to retrieve book profile page urls...')
        self._book_profile_page_urls = Scraper._retrieve_book_profile_page_urls_from_page(main_bs)
        if page_count > 1:
            self._retrieve_book_profile_page_urls_from_other_page(page_count - 1)
        styled_book_count = typer.style(str(len(self._book_profile_page_urls)), fg=typer.colors.MAGENTA, bold=True)
        typer.echo(f'There are {styled_book_count} books in total.')
        self.db.store_profile_page_urls(self._book_profile_page_urls)
        typer.echo('Done.')