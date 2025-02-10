from settings import TWITTER_AUTH, TERMS, FOLLOWS
from streamer import SentinelStreamer
from termwatcher import TermWatcher

terms = TERMS
follows = FOLLOWS


if __name__ == "__main__":
    try:
        sb = TermWatcher(TWITTER_AUTH, terms=terms, follows=follows)
        sb.start_forever()
    except Exception as e:
        print(e)
