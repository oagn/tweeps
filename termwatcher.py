import time
import logging
import os
import glob
from threading import Thread

import simplejson
import watchdog
from requests.exceptions import ChunkedEncodingError
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

from settings import PATH
from streamer import SentinelStreamer


class TermWatcher(object):
    def __init__(self, twitter_auth, terms, follows):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.forever = True

        self.auth = twitter_auth
        self.stream = SentinelStreamer(twitter_auth=twitter_auth)
        print("Terms: " + ', '.join(terms))
        self.terms = terms
        self.follows = follows

        newest = self.get_newest()
        if newest is not None:
            print("Updating terms!")
            terms = set()
            with open(newest, 'r') as termfile:
                filecontents = simplejson.load(termfile)

                terms = filecontents['terms']
                follows = filecontents['follows']

                print("New Terms: " + ', '.join(terms))
                print("New Follows: " + ', '.join(terms))

            if len(terms) > 0:
                self.terms = terms
            if len(follows) > 0:
                self.follows = follows

        self.stream.set_term_list(terms)
        self.stream.set_follow_list(follows)

        self.event_handler = watchdog.events.PatternMatchingEventHandler(
            patterns=["*.terms"],
            ignore_patterns=[],
            ignore_directories=True)

        self.event_handler.on_any_event = self.file_updated
        self.observer = Observer()
        self.observer.schedule(self.event_handler, PATH, recursive=True)

    def start_forever(self):
        #do_stream is started in a thread
        def do_stream(tw):
            try:
                if len(tw.follows) > 0:
                    tw.stream.statuses.filter(track=tw.terms, follow=tw.follows)
                else:
                    tw.stream.statuses.filter(track=tw.terms)
            except ChunkedEncodingError as e:
                print("ChunkedEncodingError")
                do_stream(tw)

        #start the file watcher
        self.observer.start()

        while self.forever:
            #Create the thread - need to create a new one each time - can't reuse
            self.tweet_thread = Thread(target=do_stream, args=(self,), daemon=True)

            print("Starting Collection!")
            self.tweet_thread.start()

            while self.tweet_thread.is_alive():
                #wait 1 second to join, then timeout and do it again
                self.tweet_thread.join(1)

    def restart(self):
        print("Restarting Collection!")
        self.stream.disconnect()

    def get_newest(self):
        try:
            if not os.path.exists(PATH):
                os.makedirs(PATH)
            g = glob.iglob(PATH + '/*.[Tt][Ee][Rr][Mm][Ss]')
            return max(g, key=os.path.getctime)
        except:
            return None

    def file_updated(self, event):
        if event.event_type == "created" or event.event_type == "modified":
            newest = self.get_newest()
            if newest is not None:
                print("Updating terms!")
                terms = []
                follows = []
                with open(newest, 'r') as termfile:
                    filecontents = simplejson.load(termfile)

                    terms = filecontents['terms']
                    follows = filecontents['follows']

                restart = False

                if len(terms) > 0:
                    restart = True
                    print("New Terms: " + ', '.join(terms))
                    self.terms = terms
                    self.stream.set_term_list(terms)

                if len(follows) > 0:
                    restart = True
                    print("New Follows: " + ', '.join(terms))
                    self.follows = follows
                    self.stream.set_follow_list(follows)

                if restart:
                    self.restart()

    def stop(self):
        print("Stopping")
        self.forever = False
        self.observer.stop()
        self.stream.disconnect()
        self.tweet_thread.join()
        self.observer.join()
        print("Stopped")
