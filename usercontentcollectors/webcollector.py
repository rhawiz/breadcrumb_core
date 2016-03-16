import json
import os

from searchengines.google_search import GoogleWebSearch


class WebCollector:
    def __init__(self, aliases, sentiment_analyer=None):
        self.aliases = aliases
        self.sentiment_analyser = sentiment_analyer

    def run(self):
        content = []
        for alias in self.aliases:
            google_search = GoogleWebSearch(query=alias, num=50, start=0)
            content += google_search.search(2)

        return json.dumps(content)


if __name__ == "__main__":
    wc = WebCollector(aliases=['Rawand Hawiz'])
    print wc.run()
