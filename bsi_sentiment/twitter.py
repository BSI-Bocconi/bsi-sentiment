import csv
import datetime
import json
import re
import sys
import time
from itertools import islice
from pathlib import Path
from typing import Iterable, List, Union

from .utils import load_nltk

import snscrape.modules.twitter as sntwitter
import tweepy as tw

from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm


class NLPTweet:
    """
    Base class that adds NLP methods to tweepy.models.Status and sntwitter.Tweet.
    This class shouldn't normally be instantiated on its own, but rather by passing the list of tweets
    returned by search_tweets_tweepy or search_tweets_sn to NLPTweetList.

    Parameters
    ----------
    tweet (Union[tweepy.models.Status, sntwitter.Tweet])

    Attributes
    ----------
    id (str)
    permalink (str)
    username(str)
    to (str)
    text (str)
    date (datetime) in UTC
    retweets (int)
    favorites (int)
    mentions (str)
    hashtags (str)
    geo (str)
    sentiment -> update description once method implemented
    """
    def __init__(self, tweet: Union[None, tw.models.Status, sntwitter.Tweet] = None):
        if isinstance(tweet, tw.models.Status):
            self._from_tweepy(tweet)
        elif isinstance(tweet, sntwitter.Tweet):
            self._from_sn(tweet)

    def _from_tweepy(self, tweet):
        self.id = tweet.id_str
        self.permalink = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
        self.username = tweet.user.screen_name
        # if multiple reply_to, take first like https://github.com/Mottl/GetOldTweets3/blob/master/GetOldTweets3/manager/TweetManager.py
        self.to = tweet.in_reply_to_screen_name[0] if tweet.in_reply_to_screen_name is not None else None
        self.text = tweet.full_text
        self.date = datetime.datetime.strftime(
            tweet.created_at.astimezone(datetime.timezone.utc), '%Y-%m-%d')
        self.retweets = tweet.retweet_count
        self.favorites = tweet.favorite_count
        self.mentions = ' '.join([user['screen_name']
                                  for user in tweet.entities['user_mentions']])
        self.hashtags = ' '.join(hashtag['text']
                                 for hashtag in tweet.entities['hashtags'])
        self.geo = tweet.geo

    def _from_sn(self, tweet):
        self.id = tweet.id
        self.permalink = tweet.url
        self.username = tweet.username
        self.text = tweet.content
        self.date = datetime.datetime.strftime(
            tweet.date.astimezone(datetime.timezone.utc), '%Y-%m-%d')

    def __repr__(self):
        return str(self.__dict__)

    def __getitem__(self, k):
        return self.__dict__[k]

    def __copy__(self):
        copy = NLPTweet()
        copy.__dict__ = self.__dict__.copy()
        return copy

    @staticmethod
    def from_dict(d):
        tweet = NLPTweet()
        tweet.__dict__ = d.copy()
        return tweet

    def get_sentiment(self, method="vader"):
        """
        Extract sentiment expressed by self.text. Multiple sentiment analysis methods available. Default is 'vader'.

        Parameters
        ----------
        method (str): method to use for sentiment analysis. Possible choices are:
            - 'vader'(default): Give a sentiment intensity score to sentences, according to VADER sentiment analysis tool. Metrics stored are 'polarity', 'pos_w', 'neu_w', 'neg_w'.
            - 'textblob-pa': Uses PatternAnalyzer from textblob to compute 'polarity' (in range [-1.0, 1.0]) and 'subjectivity' (in range [0.0,1.0]).
            - 'textblob-nb': Uses NaiveBayesAnalyzer from textblob to classify the sentiment. Computes also 'p_pos' and 'p_neg', as probabilities.
        """       
        processed_text = re.sub(
            r'(#)|(^RT[\s]+)|(https?:\S+)|(@[A-Za-z0-9_]+)', '', self.text)
        # select method chosen
        if method == "textblob-pa":
            processed_text = TextBlob(processed_text)
            self.polarity = processed_text.sentiment.polarity
            self.subjectivity = processed_text.sentiment.subjectivity
        elif method == "textblob-nb":
            processed_text = TextBlob(processed_text, analyzer=NaiveBayesAnalyzer())
            self.classification = processed_text.sentiment.classification
            self.p_pos = processed_text.sentiment.p_pos
            self.p_neg = processed_text.sentiment.p_neg
        elif method == "vader":
            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(processed_text)
            self.polarity = scores['compound']
            self.pos_w = scores['pos']
            self.neu_w = scores['neu']
            self.neg_w = scores['neg']


class NLPTweetList:
    """
    Add NLP methods to the list of tweets returned by search_tweets_tweepy or search_tweets_sn.

    Parameters
    ----------
    tweets (Iterable[Union[tweepy.models.Status, sntwitter.Tweet]])
    """

    def __init__(self, tweets: Iterable[Union[tw.models.Status, sntwitter.Tweet]], quiet=False, tqdm_total=None):
        if not isinstance(tweets, Iterable):
            raise TypeError(
                f"tweets must be an Iterable containing instances of either tweepy.models.Status or sntwitter.Tweet, got '{type(tweets).__name__}'")
        self.tweets = list(map(NLPTweet, tqdm(tweets, desc="Downloading tweets", total=tqdm_total, disable=quiet)))
        

    def __getitem__(self, i):
        return self.tweets[i]

    def __len__(self):
        return len(self.tweets)

    def __iter__(self):
        for tweet in self.tweets:
            yield tweet

    def get_sentiment(self, method="vader", quiet=False):
        load_nltk(method, quiet=quiet)
        for tweet in tqdm(self,  desc="Analyzing tweets  ", disable=quiet):
            tweet.get_sentiment(method)

    @staticmethod
    def from_csv(path: Union[str, Path], delimiter=','):
        if not isinstance(path, (str, Path)):
            raise TypeError(
                f"path must be of type Union[str, Path], got '{type(path).__name__}'")
        elif isinstance(path, str):
            path = Path(path)
        if not path.parent.is_dir():
            raise FileNotFoundError(f"path '{str(path)}'is not valid")
        if not path.suffix == '.csv':
            raise FileNotFoundError(
                f"path must be pointing at a .csv file, got f'{str(path)}'")
        with path.open(newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            columns = next(reader)
            tweets = list(map(lambda row: NLPTweet.from_dict(
                dict(zip(columns, [x if x != '' else None for x in row]))), reader))
        return tweets

    def to_csv(self, path: Union[str, Path], columns: List[str] = None, delimiter=',', quiet=False):
        if not isinstance(path, (str, Path)):
            raise TypeError(
                f"path must be of type Union[str, Path], got '{type(path).__name__}'")
        elif isinstance(path, str):
            path = Path(path)
        if not path.parent.is_dir():
            raise FileNotFoundError(f"path '{str(path)}'is not valid")
        if not path.suffix == '.csv':
            raise FileNotFoundError(
                f"path must be pointing at a .csv file, got f'{str(path)}'")
        if columns is None:
            columns = list(self[0].__dict__.keys())

        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(columns)
            for tweet in tqdm(self, desc="Writing tweets    ",  disable=quiet):
                writer.writerow([tweet[col] for col in columns])


def authenticate_tweepy(credentials_path):
    """
    Authenticates to Twitter API using keys stored at ./config/credentials.json

    Parameters
    ----------
    credentials_path (str): Path to JSON file containing Tweepy credentials. See examples/credentials.json to see how the file should be formatted.

    Returns
    -------
    api (tweepy.API): Authenticated instance of tweepy.API
    """
    with open(credentials_path) as f:
        credentials = json.load(f)
    auth = tw.OAuthHandler(
        credentials['api_key'], credentials['api_key_secret'])
    auth.set_access_token(
        credentials['access_token'], credentials['access_token_secret'])
    api = tw.API(auth)
    return api


def limit_handler(cursor):
    """
    If Twitter API rate limit is reached, wait for 15 minutes and try again.
    """
    while True:
        try:
            yield cursor.next()
        except tw.RateLimitError:
            print("Reached Tweepy API rate limit. Trying again in 15 minutes. For more information, see https://developer.twitter.com/en/docs/twitter-api/v1/rate-limits.")
            time.sleep(15 * 60)  # wait 15 minutes
        except StopIteration:
            break


def search_tweets_tweepy(q,
                         until=None,
                         geocode=None,
                         lang=None,
                         result_type='mixed',
                         max_tweets=10,
                         credentials_path='./credentials.json',
                         quiet=False):
    """
    Search tweets according to keyword arguments specified using Tweepy.

    Parameters
    ----------
    q (str): A query text to be matched.
    until (str. "yyyy-mm-dd"): An upper bound date (not included) to restrict search. Default is today. Tweepy limits search to 7 days before today (i.e. no tweets older than a week).
    geocode (str): Returns only tweets by users within a given radius of the given geolocation. Should be of the form "latitude,longitude,radius", where radius can be either in "mi" or "km".
    lang (str): Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction.
    result_type (str): Type of tweets to retrieve. Can be either "recent", "popular" or "mixed". Default is "mixed".
    max_tweets (int): The maximum number of tweets to be retrieved. Default is 10. If Twitter API rate limit is reached, the program waits for 15 minutes before trying again.

    Returns
    -------
    tweets (NLPTweetList): list of tweets resulting from the search and amenable to analysis.
    """
    if until is None:
        until = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
    if datetime.datetime.strptime(until, '%Y-%m-%d') < (datetime.datetime.today() - datetime.timedelta(days=7)):
        raise ValueError(
            'Tweepy limits search to 7 days before today (i.e. no tweets older than a week can be retrieved).')

    q = f"{q} exclude:retweets exclude:replies"
    search_args = {'q': q, 'until': until, 'result_type': result_type}
    if geocode is not None:
        search_args['geocode'] = geocode
    if lang is not None:
        search_args['lang'] = lang

    api = authenticate_tweepy(credentials_path)
    tweets = NLPTweetList(limit_handler(
        tw.Cursor(api.search, **search_args, tweet_mode='extended').items(max_tweets)),
        tqdm_total=max_tweets,
        quiet=quiet)
    return tweets


def search_tweets_sn(q,
                     since=None,
                     until=None,
                     username=None,
                     near=None,
                     radius=None,
                     lang=None,
                     max_tweets=-1,
                     quiet=False):
    """
    Search tweets according to keyword arguments specified using snscrape.

    Parameters
    ----------
    q (str): A query text to be matched.
    since (str. "yyyy-mm-dd"): A lower bound date (UTC) to restrict search. Default is 7 days before today.
    until (str. "yyyy-mm-dd"): An upper bound date (not included) to restrict search. Default is today.
    username (str or iterable): An optional specific username(s) from a twitter account (with or without "@"). Default is no username restriction.
    near (str): A reference location area (e.g. Milan) from where tweets were generated. Default is no reference area.
    radius (str): A distance radius (e.g. 15km) from location specified by "near". Meaningful only if "near" is set.
    lang (str): Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction.
    max_tweets (int): The maximum number of tweets to be retrieved. If this number is unsetted or lower than 1 all possible tweets will be retrieved. Default is -1.

    Returns
    -------
    tweets (NLPTweetList): list of tweets resulting from the search and amenable to analysis.
    """
    if until is None:
        until = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
    if since is None:
        since = datetime.datetime.strftime(
            datetime.datetime.strptime(until, '%Y-%m-%d') - datetime.timedelta(days=7), '%Y-%m-%d')
    if max_tweets == -1:
        max_tweets = sys.maxsize

    criteria = f"{q} since:{since} until:{until} exclude:retweets exclude:replies"

    if username is not None:
        criteria += f" from:{username}"
    if near is not None:
        criteria += f" near:{near.replace(' ', '&')}"
    if radius is not None:
        criteria += f" within:{radius}"
    if lang is not None:
        criteria += f" lang:{lang}"

    tweets = NLPTweetList(
        islice(sntwitter.TwitterSearchScraper(criteria).get_items(), max_tweets), 
        tqdm_total=max_tweets,
        quiet=quiet
    )
    return tweets
