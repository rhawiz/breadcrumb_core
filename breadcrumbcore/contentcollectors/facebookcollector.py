import json

import requests
import time

USER_FEED_URL_BASE = "https://graph.facebook.com/me?access_token={}&fields=id,name,feed.include_hidden(true).until({}).since({}){{message,permalink_url,created_time}}"
TEST_ACCESS_TOKEN = "CAACxjKIpqZBoBABZAGXfUq7k5rqTyTeZBpaPZCZAehZCf8ioTnn8N6gw3yuwxt4DmHZBe93YbzDBZBiAWoTXQ4ZBLNQf5EWi2d6gMnEI3XIYFgui3FuqHcWyMx59nZCPAREPfR7YrvgQlXgbFofcxwLdwv6UuLBxpZChIZBvSy9nQYhuuWSxvyqQY06KEerIayMiXYiToaD8GNipVQZDZD"


class FacebookCollector:
    def __init__(self, access_token, sentiment_analyser=None, min_date=None, max_date=None):
        self.access_token = access_token
        self.sentiment_analyser = sentiment_analyser
        self.min_date = min_date or 0
        self.max_date = max_date or int(time.time())

    def run(self):
        self.content = []
        user_feed_url = self._construct_url()

        user_feed_request = requests.get(user_feed_url).json()
        user_feed_paginated = user_feed_request.get('feed')

        if not user_feed_paginated:
            raise ValueError(
                "Could not retrieve Facebook feed with the provided access token.\nFacebook response:\n\t{}".format(
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

        return json.loads(self.content)

    def _construct_url(self):

        url = USER_FEED_URL_BASE.format(
            self.access_token,
            self.max_date,
            self.min_date
        )

        print url
        return url


if __name__ == "__main__":
    fc = FacebookCollector(access_token=TEST_ACCESS_TOKEN)
    content = fc.run()
    print json.dumps(content)
