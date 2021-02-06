#!/usr/bin/python3
# -*- conding:utf-8 -*-

from . import config
from .thread_manager import ThreadManager
from .db import Db

import re
import typer
import time
import requests
import logging
import rich
from tomd import Tomd
from bs4 import BeautifulSoup

class BookInfo:
    def __init__(self):
        self.title = ''
        self.preview_img = ''
        self.details = ''
        self.description = ''
        self.tn_url = ''


class Scraper:

    _MAIN_URL = 'https://itebooksfree.com/'
    _REQUEST_TIMEOUT = 15
    _LOGGER = logging.getLogger(__name__)


    def __init__(self):
        self._search_key = config.get('keyword')
        self.db = Db()
        self._book_profile_page_urls = []
        self._book_info_collection = []


    @staticmethod
    def _construct_search_api(search_key='', page=None):
        if search_key == '' and page is None:
            return Scraper._MAIN_URL
        elif search_key == '' and page:
            return f'{Scraper._MAIN_URL}/page/{page}'
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
        config.get('console').log(f'Thread {index} finished its job.')


    @staticmethod
    def _get_book_info_from_bs(book_bs):
        bookInfo = BookInfo()
        content_bs = book_bs.find_all('section', {'class': 'content'})
        if content_bs == []:
            return None
        content_bs = content_bs[0]
        title_bs = content_bs.find('h3', {'class': 'product-title'})
        if title_bs:
            bookInfo.title = title_bs.get_text()
        preview_bs = content_bs.find('div', {'class': 'preview-pic'})
        if preview_bs:
            bookInfo.preview_img = preview_bs.find('img').get('src')
        details_bs = content_bs.find('div', {'class': 'details'})
        if details_bs:
            details_list_bs = details_bs.find('ul', {'class': 'list-unstyled'})
            if details_list_bs:
                bookInfo.details = details_list_bs.get_text()
        body_bs_list = content_bs.find_all('div', {'class': 'body'})
        if len(body_bs_list) == 6:
            description_bs = body_bs_list[3]
            bookInfo.description = Tomd(str(description_bs)).markdown
        download_bs = content_bs.find('span', {'class': 'tn-download'})
        if download_bs:
            bookInfo.tn_url = download_bs.get('tn-url')


    @staticmethod
    def _run_collect_book_info(thread_pools, index, url_workload, extra_workload, profile_urls):
        thread_book_info_collection = []
        start_index, workload = Scraper._calculate_start_index_and_workload(
            index, url_workload, extra_workload
        )
        for url in profile_urls[start_index:start_index+workload]:
            book_bs = Scraper._start_get_bs_obj(Scraper._MAIN_URL + url)
            book_info = Scraper._get_book_info_from_bs(book_bs)
            thread_book_info_collection.append(book_info)
        thread_pools[index] = thread_book_info_collection


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
        typer.echo(f'There are {styled_page_count} page(s) in total.')
        with config.get('console').status('[bold green]retrieving book profile page urls...') as status:
            self._book_profile_page_urls = Scraper._retrieve_book_profile_page_urls_from_page(main_bs)
            if page_count > 1:
                self._retrieve_book_profile_page_urls_from_other_page(page_count - 1)
        styled_book_count = typer.style(str(len(self._book_profile_page_urls)), fg=typer.colors.MAGENTA, bold=True)
        typer.echo(f'There are {styled_book_count} book urls in total.')
        self.db.store_profile_page_urls(self._book_profile_page_urls)
        typer.echo('Done.')


    def _profile_urls_status(self):
        filename_pattern = re.compile('^/book/(.*)/[0-9]*$')
        unique_book_names = []
        for url in self._book_profile_page_urls:
            match = re.fullmatch(filename_pattern, url)
            if match:
                unique_book_names.append(match.group(1))
        table = rich.table.Table(show_header=True, header_style='magenta')
        table.add_column('Item', style='dim')
        table.add_column('Count', width=12)
        table.add_row('Profile url count', str(len(self._book_profile_page_urls)))
        table.add_row('Unique book names from urls', str(len(set(unique_book_names))))
        config.get('console').print(table)
        rich.print()


    def _collect_book_info_from_profile_pages(self):
        thread_manager = ThreadManager()
        thread_manager.thread_job_distribution(len(self._book_profile_page_urls), ThreadManager.THREAD_RETRIEVE_RESOURCE_JOB)
        thread_manager.thread_job_preparation(
            Scraper._run_collect_book_info,
            ThreadManager.THREAD_RETRIEVE_RESOURCE_JOB,
            self._book_profile_page_urls
        )
        self._book_info_collection = []
        thread_manager.thread_job_handling(self._book_info_collection)


    def collect_book_info(self):
        self._book_profile_page_urls = self.db.select_profile_urls()
        self._profile_urls_status()
        if self._book_profile_page_urls == []:
            rich.print('There is no record in [bold]profile[/bold] table, probably need to run [bold]search[/bold] command first.')
            rich.print(':monkey: :pile_of_poo:')
            return
        self._collect_book_info_from_profile_pages()