import random
import socket
from time import sleep

import requests
from bs4 import BeautifulSoup
from utils.netutils import generate_request_header

from breadcrumbcore.utils.utils import get_hash

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
GOOGLE_IMAGE_SEARCH_URL_BASE = "https://www.google.co.uk/search?tbm=isch&q={search_query}&safe=off&nfpr=1"
GOOGLE_IMAGE_SEARCH_FILTER_TYPE = "itp:{img_search_type}"

GOOGLE_SEARCH_FILTER = "&tbs="
GOOGLE_SEARCH_FILTER_DATE = "cdr:1,cd_min:{min_date},cd_max:{max_date}"

socket.setdefaulttimeout(10)


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
        attempts = 0
        while not self.stop_search and page < self.pages:
            url = self._construct_url(page)
            page += 1
            header = generate_request_header()
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
            unwanted_head_list = ["/url?url=", "/url?q="]
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
            result_hash = get_hash(short_text + link_url)
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
