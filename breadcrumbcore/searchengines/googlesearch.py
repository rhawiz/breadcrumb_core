import json
import random
import socket
import urllib
import urlparse
from time import sleep

import requests
from bs4 import BeautifulSoup
from breadcrumbcore.utils.netutils import generate_request_header

from breadcrumbcore.utils.utils import get_hash8

"""
    Google Web Search URL usage
    Example: https://www.google.co.uk/search?q=SEARCH+QUERY&start=0&num=50&tbs=cdr:1,cd_min:01/03/2013,cd_max:16/03/2016
    ---Parameters---
    q: Search Query
    tbs: Filters
        cdr:1 : Add time range filter
            cd_min: Min Date (dd/mm/yyyy)
            cd_max: Max Date (dd/mm/yyyy)

"""
GOOGLE_WEB_SEARCH_URL_BASE = "https://www.google.com/search?q={search_query}&start={start}&num={num}"

GOOGLE_SEARCH_FILTER = "&tbs="
GOOGLE_SEARCH_FILTER_DATE = "cdr:1,cd_min:{min_date},cd_max:{max_date}"

UNWANTED_URL_HEAD_LIST = ["/url?url=", "/url?q="]


class GoogleWebSearch:
    def __init__(self, query, wait=-1, start=0, num=50, min_date=None, max_date=None, pages=1):
        self.query = query
        self.wait = wait
        self.start = start
        self.num = num
        self.min_date = min_date
        self.max_date = max_date
        self.pages = pages

    def search(self):
        self.results = []
        self.global_hashes = []
        self.stop_search = False

        page = 0
        while not self.stop_search and page < self.pages:
            url = self._construct_url(page)
            page += 1
            header = generate_request_header()
            attempts = 0
            # proxy_dict = generate_proxy_dict()
            try:
                # request_response = br.open(url)
                attempts += 1
                request_response = requests.get(url, headers=header)

            except Exception, e:
                print e
                continue
            html_response = request_response.text
            # html_response = request_response.read()

            content = self._scrape_page(html_response)
            if not len(content):
                break
            self.results += content

            if self.wait == -1:
                # Wait between 1.0 and 5.0 seconds before making the next request to prevent getting blocked.
                wait_time = random.uniform(1.0, 5.0)
                sleep(wait_time)

        return self.results

    def _construct_url(self, page):
        query = self.query
        start = self.start + (page * self.num)
        num = self.num
        BASE_URL = GOOGLE_WEB_SEARCH_URL_BASE.format(search_query=query, start=start, num=num)
        min_date = self.min_date or ""
        max_date = self.max_date or ""
        if self.min_date or self.max_date:
            BASE_URL += GOOGLE_SEARCH_FILTER + GOOGLE_SEARCH_FILTER_DATE
            BASE_URL = BASE_URL.format(min_date=min_date, max_date=max_date)

        return BASE_URL

    def _scrape_page(self, html):
        soup = BeautifulSoup(html, "html.parser")
        raw_content = soup.find_all('div', attrs={'class': 'g'})
        results = []
        for content in raw_content:
            link_tag = content.find('a')
            link_url = link_tag.get('href').split('&sa')
            if not len(link_url):
                continue
            link_url = link_url[0]
            unwanted_head_list = UNWANTED_URL_HEAD_LIST
            for unwanted_head in unwanted_head_list:
                if link_url.find(unwanted_head) > -1:
                    link_url = link_url[len(unwanted_head):]

            link_text = link_tag.get_text()
            short_text = content.find('span', attrs={'class': 'st'})
            if short_text is None:
                continue

            short_text = short_text.get_text().encode('ascii', errors='ignore')

            # We'll hash the short text + link url, and if it exists in the list of global hashes,
            #   then we will stop scraping as we've reached google's last page
            result_hash = get_hash8(short_text + link_url)
            if result_hash in self.global_hashes:
                self.stop_search = True
                return []

            self.global_hashes.append(result_hash)

            content = {
                'url': link_url,
                'url_text': link_text,
                'text': short_text
            }

            results.append(content)

        return results


"""
    Google Image Search URL usage
    Example URL: https://www.google.co.uk/search?q=SEARCH+QUERY&safe=off&nfpr=1&tbs=cdr:1,cd_min:01/03/2016,cd_max:10/03/2016,itp:face&tbm=isch
    ----Parameters----
    q: Search Query
    tbs: Filters
        cdr:1 : Add time range filter
            cd_min: Min Date (dd/mm/yyyy)
            cd_max: Max Date (dd/mm/yyyy)
        itp: Search Type
            face: Face Photos
            photo: Photograps
            clipart: Drawings
            linedrawing: Line drawings
            animated: GIFS

"""
GOOGLE_IMAGE_SEARCH_BASE_URL = "https://www.google.co.uk/search?tbm=isch&q={search_query}&safe=off&nfpr=1&tbs=itp:{search_type}"




class GoogleImageSearch:
    def __init__(self, query, wait=-1, start=0, min_date=None, max_date=None, num=50, search_type=None):
        self.query = query
        self.wait = wait
        self.start = start
        self.num = num
        self.min_date = min_date
        self.max_date = max_date
        if search_type in ("all", "face", "photo", "clipart", "linedrawing", "animated"):
            self.search_type = search_type
        else:
            self.search_type = "all"

    def search(self):
        results = []
        stop_search = False
        page = 0

        while not stop_search:
            url = self._construct_url()
            print url
            page += 1
            header = generate_request_header()
            # proxy_dict = generate_proxy_dict()
            attempts = 0
            try:
                # request_response = br.open(url)
                attempts += 1
                request_response = requests.get(url, headers=header)

            except Exception, e:
                print e
                continue

            html_response = request_response.text
            # html_response = request_response.read()

            content = self._scrape_page(html_response)
            results += content
            # if self.wait == -1:
            #     # Wait between 1.0 and 5.0 seconds before making the next request to prevent getting blocked.
            #     wait_time = random.uniform(1.0, 5.0)
            #     sleep(wait_time)

            stop_search = True
        return results

    def _construct_url(self):
        query = self.query
        BASE_URL = GOOGLE_IMAGE_SEARCH_BASE_URL.format(search_query=query, search_type=self.search_type)
        min_date = self.min_date or ""
        max_date = self.max_date or ""
        if self.min_date or self.max_date:
            BASE_URL = "{}{}{}".format(BASE_URL,",",GOOGLE_SEARCH_FILTER_DATE)
            BASE_URL = BASE_URL.format(min_date=min_date, max_date=max_date)

        return BASE_URL

    def _scrape_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        raw_content = soup.find_all('div', attrs={'class': 'rg_di rg_el ivg-i'})
        results = []

        for img_container in raw_content:
            meta = img_container.find("div", attrs={"class":"rg_meta"})
            meta_dict = json.loads(meta.contents[0])
            url_text = meta_dict.get("pt")
            short_text = meta_dict.get("s")
            img_url = meta_dict.get("ou")
            page_url = meta_dict.get("ru")
            content = {
                'img_url': img_url,
                'page_url': page_url,
                'url_text': url_text,
                'text': short_text
            }
            results.append(content)

        return results

if __name__ == "__main__":
    src = GoogleWebSearch(query="Rawand Hawiz")
    content = src.search()
    print content