import time

import pymongo
from pymongo import MongoClient
from pymongo.errors import AutoReconnect

from twython import Twython
from twython import TwythonError
import re
import json
from datetime import datetime
import time

from settings import MONGOURI, MONGODB, MONGOCOLLECTION, MONGOERRORCOLLECTION, TWITTER_AUTH, TERMS


class TwitterTermToMongo():
    def __init__(self):
        self.mongoclient = MongoClient(MONGOURI)
        self.mongodb = self.mongoclient[MONGODB]
        self.mongocollection = self.mongodb[MONGOCOLLECTION]
        self.mongoerrorcollection = self.mongodb[MONGOERRORCOLLECTION]
        self.mongocollection.create_index([("id_str", pymongo.ASCENDING)])
        self.mongocollection.create_index([("id", pymongo.ASCENDING)])

    '''
    Quick logging method, replace later with proper logging api/library
    '''
    def log(self, line):
        print('%s: %s' % (datetime.now(), line))

    def iterative_search(self, _max, _since, _search_value):
        max_tweet_id = 0
        min_tweet_id = 0
        tweet_count = 0
        search_count = 0

        while True:
            try:
                twitter = Twython(app_key=TWITTER_AUTH['app_key'],
                                  app_secret=TWITTER_AUTH['app_secret'],
                                  oauth_token=TWITTER_AUTH['oauth_token'],
                                  oauth_token_secret=TWITTER_AUTH['oauth_token_secret'])

                search_results = twitter.search(q=_search_value, count="100", max_id=str(_max), since_id=str(_since),
                                                result_type="recent", include_entities="true")

                search_count += 1

                for tweet in search_results["statuses"]:

                    self.do_insert(tweet, self.mongocollection)
                    # self.log(tweet['id'])

                    tweet_count += 1

                    if tweet['id'] > max_tweet_id:
                        max_tweet_id = tweet['id']

                    if min_tweet_id == 0 or tweet['id'] < min_tweet_id:
                        min_tweet_id = tweet['id']

                    if tweet_count % 500 == 0:
                        ts = time.time()
                        st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        self.log((st, "-on", _search_value, ":", tweet_count))

                next_search = search_results["search_metadata"]
                if 'next_results' in next_search:
                    next_search = next_search["next_results"]
                    next_search = re.search('max_id=([0-9]*)', next_search)
                    _max = next_search.group(1)
                else:
                    break

            except TwythonError as e:
                ts = time.time()
                st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                self.log((st, "-", e, "Error searching", _search_value, ":", e.msg))

                time.sleep(15 * 61)
                break
        return _max

    def run_search(self, max_id, since_id):
        for query in TERMS:
            self.log(("searching on ", query))
            while max_id > since_id:
                last_max = max_id
                max_id = self.iterative_search(max_id, since_id, query)
                self.log(max_id)

                if max_id == last_max:
                    break

    def do_insert(self, data, collection):
        try:
            collection.insert_one(data)
        except AutoReconnect as e:
            collection.insert_one(data)

# the Tweet ID that you last collected just before the gap
since_id = "1305532851425665024"

# the Tweet ID that you first collected after the gap
max_id = "1305533174164983812"

searcher = TwitterTermToMongo()

searcher.run_search(max_id, since_id)
