import csv
import datetime
import json
import re
from pathlib import Path
from typing import Iterable, List, Union
import time

import GetOldTweets3 as got
import tweepy as tw

from textblob import TextBlob

class NLPTweet:
    """
    Base class that adds NLP methods to GetOldTweets3.models.Tweet and tweepy.models.Status.
    This class shouldn't normally be instantiated on its own, but rather by passing the list of tweets
    returned by got.manager.TweetManager.getTweets to NLPTweetList.

    Parameters
    ----------
    tweet (Union[GetOldTweets3.models.Tweet, tweepy.models.Status])

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
    DEFAULT_ATTRIBUTES = ['id', 'permalink', 'username', 'to', 'text', 'date', 'retweets', 'favorites', 'mentions', 'hashtags', 'geo', 'polarity', 'subjectivity']
    def __init__(self, tweet: Union[None, got.models.Tweet, tw.models.Status]=None):
        if isinstance(tweet, got.models.Tweet):
            self._from_got(tweet)
        elif isinstance(tweet, tw.models.Status):
            self._from_tweepy(tweet)

    def _from_got(self, tweet):
        self.__dict__ = tweet.__dict__.copy()

    def _from_tweepy(self, tweet):
            self.id = tweet.id_str
            self.permalink = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
            self.username = tweet.user.screen_name
            # if multiple reply_to, take first like https://github.com/Mottl/GetOldTweets3/blob/master/GetOldTweets3/manager/TweetManager.py
            self.to = tweet.in_reply_to_screen_name[0] if tweet.in_reply_to_screen_name is not None else None
            self.text = tweet.full_text
            self.date = datetime.datetime.strftime(tweet.created_at.astimezone(datetime.timezone.utc), '%Y-%m-%d')
            self.retweets = tweet.retweet_count
            self.favorites = tweet.favorite_count
            self.mentions = ' '.join([user['screen_name'] for user in tweet.entities['user_mentions']])
            self.hashtags = ' '.join(hashtag['text'] for hashtag in tweet.entities['hashtags'])
            self.geo = tweet.geo

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

    def get_sentiment(self):
        # TODO: add support to more arguments for textblob and nltk - this method MUST be expanded
        # Alternative: if we want to be fancy create SentimentModel class that trains/fine-tunes different 
        # model (naive bayes/LSTM/ULMFiT/BERT?) to be trained on long NLPTweetList (train set size depends on
        # model chosen)
        # Add other suggestions here
        processed_text = re.sub(r'(#)|(^RT[\s]+)|(https?:\S+)|(@[A-Za-z0-9_]+)', '', self.text) # remove hashtags | retweets | links | usernames
        processed_text = TextBlob(processed_text)
        self.polarity = processed_text.sentiment.polarity
        self.subjectivity = processed_text.sentiment.subjectivity


class NLPTweetList:
    """
    Add NLP methods to the list of tweets returned by GetOldTweets3.manager.TweetManager.getTweets.
    
    Parameters
    ----------
    tweets (Iterable[Union[GetOldTweets3.models.Tweet, tweepy.models.Status]])
    """
    def __init__(self, tweets: Iterable[Union[got.models.Tweet, tw.models.Status]]):
        if not isinstance(tweets, Iterable):
            raise TypeError(f"tweets must be an Iterable containing instances of either got.models.Tweet or tweepy.models.Status, got '{type(tweets).__name__}'")
        self.tweets = list(map(NLPTweet, tweets))
    
    def __getitem__(self, i):
        return self.tweets[i]

    def __len__(self):
        return len(self.tweets)

    def __iter__(self):
        for tweet in self.tweets:
            yield tweet

    def get_sentiment(self):
        for tweet in self:
            tweet.get_sentiment()

    @staticmethod
    def from_csv(path: Union[str, Path], delimiter=',', validate_columns=True):
        if not isinstance(path, (str, Path)):
            raise TypeError(f"path must be of type Union[str, Path], got '{type(path).__name__}'")
        elif isinstance(path, str):
            path = Path(path)
        if not path.parent.is_dir():
            raise FileNotFoundError(f"path '{str(path)}'is not valid")
        if not path.suffix == '.csv':
            raise FileNotFoundError(f"path must be pointing at a .csv file, got f'{str(path)}'")
        with path.open(newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            columns = next(reader)
            if validate_columns:
                for col in columns:
                    try:
                        assert col in NLPTweet.DEFAULT_ATTRIBUTES
                    except AssertionError:
                        raise KeyError(f"column '{col}' is not a valid NLPTweet attribute")
            tweets = list(map(lambda row: NLPTweet.from_dict(dict(zip(columns, [x if x != '' else None for x in row]))), reader))
        return tweets
    
    def to_csv(self, path: Union[str, Path], columns: List[str]=None, delimiter=','):
        if not isinstance(path, (str, Path)):
            raise TypeError(f"path must be of type Union[str, Path], got '{type(path).__name__}'")
        elif isinstance(path, str):
            path = Path(path)
        if not path.parent.is_dir():
            raise FileNotFoundError(f"path '{str(path)}'is not valid")
        if not path.suffix == '.csv':
            raise FileNotFoundError(f"path must be pointing at a .csv file, got f'{str(path)}'")
        if columns is None: 
            columns = list(self[0].__dict__.keys())
        
        with path.open('w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(columns)
            for tweet in self:
                writer.writerow([tweet[col] for col in columns])

def authenticate_tweepy():
    """
    Authenticates to Twitter API using keys stored at ./config/credentials.json

    Returns
    -------
    api (tweepy.API) = Authenticated instance of tweepy.API
    """
    credentials_path = Path('./config/credentials.json')
    with credentials_path.open() as f:
        credentials = json.load(f)
    auth = tw.OAuthHandler(credentials['api_key'], credentials['api_key_secret'])
    auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
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
            time.sleep(15 * 60) # wait 15 minutes
        except StopIteration:
            break

def search_tweets_tweepy(q,
                         until=None,
                         geocode=None,
                         lang=None,
                         result_type='mixed',
                         max_tweets=10):
    """
    Search tweets according to keyword arguments specified using Tweepy.

    Parameters
    ----------
    q (str): A query text to be matched.
    until (str. "yyyy-mm-dd"): An upper bound date (not included) to restrict search. Default is today. Tweepy limits search to 7 days before today (i.e. no tweets older than a week).
    geocode (str): Returns only tweets by users within a given radius of the given geolocation. Should be of the form "latitude,longitude,radius", where radius can be either in "mi" or "km".
    lang (str): Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction.
    result_type (bool): Type of tweets to retrieve. Can be either "recent", "popular" or "mixed". Default is "mixed".
    max_tweets (int): The maximum number of tweets to be retrieved. Default is 10. If Twitter API rate limit is reached, the program waits for 15 minutes before trying again.

    Returns
    -------
    tweets (NLPTweetList): list of tweets resulting from the search and amenable to analysis.
    """
    if until is None:
        until = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
    if datetime.datetime.strptime(until, '%Y-%m-%d') < (datetime.datetime.today() - datetime.timedelta(days=7)):
        raise ValueError('Tweepy limits search to 7 days before today (i.e. no tweets older than a week can be retrieved).')

    q += " exclude:retweets exclude:replies"
    search_args = {'q': q, 'until': until, 'result_type': result_type}
    if geocode is not None:
        search_args['geocode'] = geocode
    if lang is not None:
        search_args['lang'] = lang

    api = authenticate_tweepy()
    tweets = NLPTweetList(limit_handler(tw.Cursor(api.search, **search_args, tweet_mode='extended').items(max_tweets)))
    return tweets

# not working atm: https://github.com/Mottl/GetOldTweets3/issues/98
def search_tweets_got(q,
                      since=None,
                      until=None,
                      username=None,
                      near=None,
                      radius=None,
                      only_top=False,
                      max_tweets=-1):
    """
    Search tweets according to keyword arguments specified using GetOldTweets3. 

    Parameters
    ----------
    q (str): A query text to be matched.
    since (str. "yyyy-mm-dd"): A lower bound date (UTC) to restrict search. Default is 7 days before today.
    until (str. "yyyy-mm-dd"): An upper bound date (not included) to restrict search. Default is today.
    username (str or iterable): An optional specific username(s) from a twitter account (with or without "@"). Default is no username restriction.
    near (str): A reference location area from where tweets were generated. Default is no reference area.
    radius (str): A distance radius (e.g. 15km) from location specified by "near". Meaningful only if "near" is set.
    only_top (bool): If True only the Top Tweets will be retrieved. Default is False.
    max_tweets (int): The maximum number of tweets to be retrieved. If this number is unsetted or lower than 1 all possible tweets will be retrieved. Default is -1.

    Returns
    -------
    tweets (NLPTweetList): list of tweets resulting from the search and amenable to analysis.
    """
    if since is None:
        since = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=7), '%Y-%m-%d')
    
    if until is None:
        until = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')

    criteria = (got.manager.TweetCriteria().setQuerySearch(q)
                                           .setSince(since)
                                           .setUntil(until)
                                           .setTopTweets(only_top)
                                           .setMaxTweets(max_tweets))
    
    if username is not None:
        criteria = criteria.setUsername(username)
    if near is not None:
        criteria = criteria.setNear(near)
        if radius is not None:
            criteria = criteria.setWithin(radius)
    
    tweets = NLPTweetList(got.manager.TweetManager().getTweets(criteria))
    return tweets
