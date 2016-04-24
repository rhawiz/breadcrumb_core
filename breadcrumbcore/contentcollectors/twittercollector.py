import json
import time

import tweepy
from breadcrumbcore.ai.sentimentanalyser import analyse_text

class TwitterCollector:
    def __init__(self, key, secret, consumer_key, consumer_secret, sentiment_analyser=None, min_date=None,
                 max_date=None):
        self.key = key
        self.secret = secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.sentiment_analyser = sentiment_analyser
        self.min_date = min_date or 0
        self.max_date = max_date or int(time.time())

    def run(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.key, self.secret)
        api = tweepy.API(auth)
        timeline = api.user_timeline(count=500)
        self.content = []
        for status in timeline:
            created_at_timestamp = int(time.mktime(status.created_at.timetuple()))
            data = {
                "text":status.text,
                "id":status.id,
                "created_at_timestamp":created_at_timestamp,
                "url":"https://twitter.com/{}/status/{}".format(status.author.screen_name,status.id)
            }

            if self.sentiment_analyser:
                analysis = self.sentiment_analyser(status.text)
                data['analysis'] = analysis

            self.content.append(data)

        return self.content


if __name__ == "__main__":
    key = "718466809184317441-wcvWbGjyD935PagRcM3IQAA9H60tQy6"
    secret = "pQgEQJQXSRINVuaVr5240zSdnRZIHT6GHZvROEYDnyBug"
    consumer_key = "5xbL8ZrvE1eSzINQfLKgPYVPE"
    consumer_secret = "ZxrB9fg2J1ZB8V16Bt6jIQ61nBOmUK74WryiP1yK3ZRkUmNRIx"
    fc = TwitterCollector(key=key, secret=secret, consumer_key=consumer_key, consumer_secret=consumer_secret)
    content = fc.run()
    print content
    print json.dumps(content)
