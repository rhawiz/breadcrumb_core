import json
import re
import unicodedata

import requests
from bs4 import BeautifulSoup, Comment

from ai.sentimentanalyser import analyse_text as sa
from searchengines.google_search import GoogleWebSearch
from utils.netutils import generate_request_header


class WebCollector:
    def __init__(self, aliases, sentiment_analyer=None, min_date=None, max_date=None):
        self.aliases = aliases
        self.sentiment_analyser = sentiment_analyer
        self.min_date = min_date
        self.max_date = max_date

    def run(self):
        self.content = []
        for alias in self.aliases:
            google_search = GoogleWebSearch(query=alias, num=25, start=0, pages=1,
                                            min_date=self.min_date, max_date=self.max_date)
            google_search_results = google_search.search()
            for g_result in google_search_results:
                url = g_result.get("url")
                url_text = g_result.get("url_text")
                short_text = g_result.get("text")
                print url, url_text, short_text
                try:
                    response = requests.get(url, headers=generate_request_header())
                except Exception, e:
                    print e
                    continue
                html = response.text
                if self.sentiment_analyser:
                    if response.status_code == 200:
                        analysis = self._analyse_html(html, alias)
                        if not analysis:
                            analysis = self.sentiment_analyser(short_text)
                    else:
                        analysis = self.sentiment_analyser(short_text)

                output = g_result
                output['alias'] = alias
                output['analysis'] = analysis
                self.content.append(output)
        return self.content

    def get_content(self):
        return self.content

    def json(self, sort_by=None):

        if sort_by == 'pos' or sort_by == 'neutral' or sort_by == 'neg':
            return json.dumps(sorted(self.content, key=lambda k: k['analysis']['probability'][sort_by], reverse=True))

        return json.dumps(self.content)

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
    wc = WebCollector(sentiment_analyer=sa, aliases=["Rawand Hawiz"])
    wc.run()
    print wc.get_content()
