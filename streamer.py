from datetime import datetime
from time import sleep

import pymongo
from pymongo import MongoClient
from pymongo.errors import AutoReconnect
from requests.exceptions import ChunkedEncodingError
from twython import TwythonStreamer

from settings import MONGOURI, MONGODB, MONGOCOLLECTION, MONGOERRORCOLLECTION


class SentinelStreamer(TwythonStreamer):
    def __init__(self, twitter_auth):
        super(SentinelStreamer, self).__init__(twitter_auth['app_key'], twitter_auth['app_secret'],
                                               twitter_auth['oauth_token'], twitter_auth['oauth_token_secret'])

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

    '''
    Called when a tweet is successfully received.
    '''
    def do_insert(self, data, collection):
        try:
            collection.insert_one(data)
        except AutoReconnect as e:
            collection.insert_one(data)

    def set_term_list(self, terms):
        self.terms = terms

    def set_follow_list(self, follow):
        self.follow = follow

    def on_success(self, data):
        self.log("Got Tweet")
        self.do_insert(data, self.mongocollection)

    def on_error(self, status_code, data):
        print(str(status_code) + ' : ' + str(data))
        to_insert = {
            'time': datetime.now(),
            'status_code': status_code,
            'data':data
        }

        self.do_insert(to_insert, self.mongoerrorcollection)

        if status_code == 420:
            #enhance your calm
            print("Twitter wants us to slow down - Waiting 1 minute")
            sleep(60)


    def on_stop(self, status_code, data):
        print("Stopping")
        self.disconnect()

    def on_timeout(self):
        print('timeout')
        to_insert = {
            'time': datetime.now(),
            'status_code': 'timeout',
            'data': 'timeout'
        }

        self.do_insert(to_insert, self.mongoerrorcollection)