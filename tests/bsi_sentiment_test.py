# TODO: add more tests
import pytest

from bsi_sentiment.twitter import *


class TestSerchTweetsSn:
    def test_correct_query(self):
        args = {
            "q": "us elections",
            "since": "2020-08-01",
            "until": "2020-11-30",
            "near": "New York",
            "radius": "100km",
            "lang": "en",
            "max_tweets": 10
        }
        tweets = search_tweets_sn(**args)
        assert len(tweets) == 10
        t = tweets[0]
        assert hasattr(t, "id")
        assert hasattr(t, "permalink")
        assert hasattr(t, "username")
        assert hasattr(t, "text")
        assert hasattr(t, "date")
