import json
import re
import unicodedata
from math import ceil

import requests
from breadcrumbcore.ai.sentimentanalyser import analyse_text as sa
from bs4 import BeautifulSoup, Comment
from breadcrumbcore.utils.netutils import generate_request_header

from breadcrumbcore.searchengines.googlesearch import GoogleWebSearch


class WebCollector:
    CONTENT_SEARCH_SPAN = 100

    def __init__(self, aliases, sentiment_analyer=None, min_date=None, max_date=None, results=50, debug=False):
        self.aliases = aliases
        self.sentiment_analyser = sentiment_analyer
        self.min_date = min_date
        self.max_date = max_date
        self.results = results
        self.debug = debug

    def run(self):
        num = 50
        pages = ceil(self.results / 50)

        if self.results < 50:
            pages = 1
            num = self.results

        self.content = []
        for alias in self.aliases:
            google_search = GoogleWebSearch(query=alias, num=num, start=0, pages=pages,
                                            min_date=self.min_date, max_date=self.max_date)
            google_search_results = google_search.search()
            for g_result in google_search_results:
                url = g_result.get("url")
                url_text = g_result.get("url_text", 'ignore')
                short_text = g_result.get("text", 'ignore')
                output = {
                    'url': url,
                    'url_text': url_text,
                    'short_text': short_text,
                    'alias': alias
                }

                if self.debug:
                    print url, url_text, short_text

                try:
                    response = requests.get(url, headers=generate_request_header())
                except Exception, e:
                    print e
                    continue

                if response.status_code == 200:
                    html = response.text
                    print type(html), isinstance(html,unicode)
                    try:
                        relevant_content = self._get_all_relevant_content(html, alias)
                    except TypeError, e:
                        print e
                        relevant_content = [short_text]
                else:
                    relevant_content = [short_text]
                output['relevant_content'] = relevant_content

                if self.sentiment_analyser:
                    content_to_analyse = relevant_content
                    if not content_to_analyse:
                        content_to_analyse = short_text
                    analysis = self.sentiment_analyser(content_to_analyse)
                    output['analysis'] = analysis

                self.content.append(output)
        return self.content

    def get_content(self):
        return self.content

    def json(self, sort_by=None):

        if sort_by == 'pos' or sort_by == 'neutral' or sort_by == 'neg':
            return json.dumps(sorted(self.content, key=lambda k: k['analysis']['probability'][sort_by], reverse=True))

        return json.dumps(self.content)

    def _get_all_relevant_content(self, html, alias):
        soup = BeautifulSoup(html, "html.parser")
        texts = soup.findAll(text=True)
        visible_text_list = filter(self._visible_element, texts)
        visible_text = ''
        for text in visible_text_list:
            visible_text += text + ' '
        visible_text = visible_text.replace('\n', ' ')
        visible_text = re.sub(' +', ' ', visible_text)

        visible_text = unicodedata.normalize('NFKD', visible_text).encode('ascii', 'ignore')

        matched_idx = self._find_all_idx(alias, visible_text)
        all_relevant_content = []
        for idx in matched_idx:
            min = idx - self.CONTENT_SEARCH_SPAN
            max = idx + self.CONTENT_SEARCH_SPAN
            if min < 0:
                min = 0
            if max >= len(visible_text):
                max = len(visible_text) - 1

            content = visible_text[min:max]
            content = content[content.find(" ") + 1:content.rfind(" ")]
            all_relevant_content.append(content)

        return all_relevant_content

    def _find_all_idx(self, phrase, text):
        indexes = []
        phrase = phrase.lower()
        text = text.lower()
        phrase_parts = phrase.split(' ')
        if len(phrase_parts) > 1:
            phrase_parts.insert(0, phrase)
        for i in phrase_parts:
            matches = [m.start(0) for m in re.finditer(i, text)]
            indexes += matches
        indexes = self._remove_in_span(indexes, self.CONTENT_SEARCH_SPAN)
        return indexes

    def _remove_in_span(self, list, span):
        list = sorted(list)
        new_list = []
        i = 0
        while i < len(list):
            idx = list[i]
            max = idx + span
            while i < len(list) - 1 and list[i + 1] <= max:
                i = i + 1
            i = i + 1

            new_list.append(idx)
        return new_list

    def _analyse_html(self, html, alias):
        soup = BeautifulSoup(html, "html.parser")
        texts = soup.findAll(text=True)
        visible_text_list = filter(self._visible_element, texts)
        visible_text = ''.join(visible_text_list)
        visible_text = visible_text.replace('\n', ' ')
        visible_text = re.sub(' +', ' ', visible_text)
        visible_text = unicodedata.normalize('NFKD', visible_text).encode('ascii', 'ignore')

        return self.sentiment_analyser(visible_text)

    def _visible_element(self, element):
        if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
            return False
        elif isinstance(element, Comment):
            return False
        return True


if __name__ == "__main__":
    wc = WebCollector(sentiment_analyer=sa, aliases=["Rawand Hawiz"], results=60)
    wc.run()
    print wc.json(sort_by='neg')
