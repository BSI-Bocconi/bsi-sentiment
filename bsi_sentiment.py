import argparse
import configparser

from sentiment.twitter import search_tweets_tweepy

# TODO: pass arguments from command line using argparse or from config.ini file 
# (when -f flag is passed from command line) using configparser.
# e.g. python bsi_sentiment.py -q "twitter quey" --geo="lat,long,rad" --until="2020-10-16"
# Sorry guys, I would have done it now, but I'm getting tired lol
QUERY = 'midterm break'
UNTIL = '2020-10-16'
LANG = 'en'
MAX_TWEETS = 10
CSV_PATH = './test.csv'

# just a little example
def test():
    tweets = search_tweets_tweepy(q=QUERY, until=UNTIL, lang=LANG, max_tweets=MAX_TWEETS)
    tweets.process_text() # TODO: tokenize, normalize, clean,...
    tweets.get_sentiment() # TODO: pretrained or to-be-trained? 
    tweets.to_csv(CSV_PATH)

if __name__ == '__main__':
    test()