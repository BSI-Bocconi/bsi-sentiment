import csv
import datetime
import json
from pathlib import Path
from typing import Iterable, List, Union

import GetOldTweets3 as got
import tweepy as tw

class NLPTweet:
    """
    Base class that adds NLP methods to GetOldTweets3.models.Tweet and tweepy.models.Status.
    This class shouldn't be instantiated on its own, but rather by passing the list of tweets
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
    def __init__(self, tweet: Union[got.models.Tweet, tw.models.Status]):
        if isinstance(tweet, got.models.Tweet):
            self.__dict__ = tweet.__dict__.copy()
        elif isinstance(tweet, tw.models.Status):
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
        else:
            raise TypeError(f"tweet must be an instance of either GetOldTweets3.models.Tweet or tweepy.models.Status, got '{type(tweet).__name__}'")
        self.sentiment = None

    def __repr__(self):
        return str(self.__dict__)

    def __getitem__(self, k):
        return self.__dict__[k]

    def __copy__(self):
        copy = NLPTweet(got.models.Tweet())
        copy.id = self.id
        copy.permalink = self.permalink
        copy.username = self.username
        copy.to = self.to
        copy.text = self.text
        copy.date = self.date
        copy.retweets = self.retweets
        copy.favorites = self.favorites
        copy.mentions = self.mentions
        copy.hashtags = self.hashtags
        copy.geo = self.geo
        copy.sentiment = self.sentiment
        return copy

    def processed_text(self):
        # TODO: tokenize, normalize, clean -> nltk/textblob?
        # Maybe bool args for tokenize, normalize and clean? 
        # Add other suggestions here
        return None

    def get_sentiment(self):
        # TODO: sentiment analysis on processed text -> nltk/textblob if we want to use pretrained model?
        # If we go with these, super easy, but we'll have to assess results
        # Alternative: if we want to be fancy create SentimentModel class that trains/fine-tunes different 
        # model (naive bayes/LSTM/ULMFiT/BERT?) to be trained on long NLPTweetList (train set size depends on
        # model chosen)
        # Add other suggestions here
        self.sentiment = self.processed_text()
    
    @staticmethod
    def from_dict(d, validate_keys=True):
        tweet = NLPTweet(got.models.Tweet())
        for k, v in d.items():
            if validate_keys:
                try:
                    assert k in NLPTweet.DEFAULT_ATTRIBUTES
                except AssertionError:
                    raise KeyError(f"column '{col}' is not a valid NLPTweet attribute")
            tweet.__dict__[k] = v
        return tweet

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
    def from_csv(path: Union[str, Path], delimiter=','):
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
            for col in columns:
                try:
                    assert col in NLPTweet.DEFAULT_ATTRIBUTES
                except AssertionError:
                    raise KeyError(f"column '{col}' is not a valid NLPTweet attribute")
            tweets = list(map(lambda row: NLPTweet.from_dict(dict(zip(columns, row)), validate_keys=False), reader))
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
    max_tweets (int): The maximum number of tweets to be retrieved. Note that Tweepy limits tweet searches to 300 tweets every 3 hours. Default is 10.

    Returns
    -------
    tweets (NLPTweetList): list of tweets resulting from the search and amenable to analysis.
    """
    if until is None:
        until = datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d')
    if datetime.datetime.strptime(until, '%Y-%m-%d') < (datetime.datetime.today() - datetime.timedelta(days=7)):
        raise ValueError('Tweepy limits search to 7 days before today (i.e. no tweets older than a week can be retrieved).')

    search_args = {'q': q, 'until': until, 'result_type': result_type}
    if geocode is not None:
        search_args['geocode'] = geocode
    if lang is not None:
        search_args['lang'] = lang

    api = authenticate_tweepy()
    tweets = NLPTweetList(tw.Cursor(api.search, **search_args, tweet_mode='extended').items(max_tweets))
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
