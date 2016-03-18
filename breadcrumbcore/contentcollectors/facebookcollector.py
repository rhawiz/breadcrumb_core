import json

import requests

USER_FEED_URL_BASE = "https://graph.facebook.com/me?access_token={}&fields=feed.include_hidden(true)"
TEST_ACCESS_TOKEN = "CAACxjKIpqZBoBAIsC35PVaZAWpRGvWglhj9beB3AzMFD32xpXFbp1pZAUTLZCG2f0OHeOzVYvMTT5I1j72FDqUTNhpClwyhRbIKVcXBd7wexv5m1B3NCZCkrs21Iadm1KxZCW6VY9CKUsquYoMMtx00aovUlWf16I7pLE4xgnCUMHS9GnXK763xQskpcqmzS7v3V4ZAb4KmkgZDZD"


class FacebookCollector:
    def __init__(self, access_token, sentiment_analyser=None, min_date=None, max_date=None):
        self.access_token = access_token
        self.sentiment_analyser = sentiment_analyser
        self.min_date = min_date
        self.max_date = max_date

    def run(self):
        self.content = []
        user_feed_url = self._construct_url()

        user_feed_request = requests.get(user_feed_url).json()
        user_feed_paginated = user_feed_request.get('feed')

        if not user_feed_paginated:
            raise ValueError("Could not retrieve Facebook feed with the provided access token.\nFacebook response:\n\t{}".format(
                json.dumps(user_feed_request)))

        all_user_feed = user_feed_paginated.get('data')

        # Go to next page ofo user feeds, until we reach the end
        while user_feed_paginated:
            if 'paging' in user_feed_paginated:
                user_feed_url = user_feed_paginated.get('paging').get('next', None)
                user_feed_paginated = requests.get(user_feed_url).json()
                all_user_feed += user_feed_paginated.get('data')
            else:
                user_feed_paginated = None

        for feed in all_user_feed:
            if 'message' in feed:
                # Perform sentiment analysis if a analyser function is passed in
                if self.sentiment_analyser:
                    try:
                        sent_dict = self.sentiment_analyser(feed.get('message'))
                        feed['analysis'] = sent_dict
                    except:
                        continue
                self.content.append(feed)

        return self.content

    def _construct_url(self):
        url = USER_FEED_URL_BASE.format(self.access_token)
        return url

if __name__ == "__main__":
    fc = FacebookCollector(access_token=TEST_ACCESS_TOKEN)
    print fc.run()
