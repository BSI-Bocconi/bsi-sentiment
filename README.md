# BSI Sentiment Analysis Pipeline

![CI](https://github.com/bsi-bocconi/bsi-sentiment/workflows/CI/badge.svg) 
[![PyPI](https://img.shields.io/pypi/v/bsi-sentiment?color=blue&label=pypi%20version)](https://pypi.org/project/bsi-sentiment/#description)
[![PyPi Downloads](http://pepy.tech/badge/bsi-sentiment)](http://pepy.tech/project/bsi-sentiment)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-red.svg)](https://www.gnu.org/licenses/gpl-3.0)

BSI Sentiment is a Python library created at [BSI Bocconi](https://github.com/BSI-Bocconi) to download tweets and perform basic sentiment analysis on them.

## Installation 

BSI Sentiment can be installed using the `pip` package manager:

```console
foo@bar:~$ pip install bsi-sentiment --upgrade
```

## CLI Usage

```console
foo@bar:~$ sentiment -h

usage: sentiment [-h] [-c CONFIG] [-a ANALYZER] [-q QUERY] [-s SINCE] [-u UNTIL] [-g GEO] [-r RADIUS] [-l LANG] [--user USERNAME] [--result_type {recent,popular,mixed}] [--max_tweets MAX_TWEETS] [--tweepy] [--credentials CREDENTIALS]
                 [--quiet]
                 {analyze,configure,download} [DEST]

BSI Tool for Sentiment Analysis. Tweets can be downloaded using either Snscrape (default) or Tweepy.

positional arguments:
  {analyze,configure,download}
                        Action to perform.
  DEST                  Output file location. Analysis/configuration/download output file is stored here. Default is current directory.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file location. If action is 'analyze' or 'download', configuration file is read from here.
  -a ANALYZER, --analyzer ANALYZER
                        Analyzer method for sentiment analysis. Available options are {'vader','textblob-pa','textblob-nb'}. Default is 'vader'.
  -q QUERY, --query QUERY
                        A query text to be matched
  -s SINCE, --since SINCE
                        A lower bound date (UTC) to restrict search. Default is 7 days before --until. Used only by Snscrape.
  -u UNTIL, --until UNTIL
                        An upper bound date (not included) to restrict search. Default is today. Tweepy has a 7 day hard limit, while Snscrape has no such limit.
  -g GEO, --geo GEO     Return only tweets by users from given geolocation. It must be a location name (e.g. 'Milan') if using Snscrape or a string of the form 'latitude,longitude' if using Tweepy.
  -r RADIUS, --radius RADIUS
                        Must be used together with --geo. Return only tweets by users within a given radius from the selected location. It must be either in 'mi' or 'km' (e.g. '15km')
  -l LANG, --lang LANG  Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction. Used only by Tweepy.
  --user USERNAME       Restrict search to tweets from specified username.
  --result_type {recent,popular,mixed}
                        Type of tweets to retrieve. Can be either 'recent', 'popular' or 'mixed'. Default is 'mixed'. Used only by Tweepy.
  --max_tweets MAX_TWEETS
                        The maximum number of tweets to be retrieved. Default is 10. In the case of Tweepy, if greater API rate limit is reached, the program waits for 15 minutes before trying again.
  --tweepy              Use Tweepy instead of the default Snscrape to download tweets.
  --credentials CREDENTIALS
                        Path to JSON file containing Tweepy credentials. See examples/credentials.json to see how the file should be formatted.
  --quiet               No stdout output when downloading or analyzing tweets. Default is verbose.
```

## Examples

### As a CLI Tool

```console
foo@bar:~$ sentiment analyze ./results.csv --analyzer="vader" -q "us elections" --since="2020-08-01" --until="2020-11-30" --geo="New York" --radius="100km" -l "en" --max_tweets=100
```

### As a Python Library

```python
from bsi_sentiment.twitter import search_tweets_sn

tweets = search_tweets_sn(
  q="us elections",
  since="2020-08-01",
  until="2020-11-30",
  near="New York",
  radius="100km",
  lang="en",
  max_tweets=100
)

tweets.get_sentiment(method="vader")
tweets.to_csv("./results.csv")
```

## Contributors

The BSI members that contributed to this project are:
* [Stefano Cortinovis](https://github.com/scortino) (PL)
* [Pietro Dominietto](https://github.com/PietroDomi)
* [Elio Scarci](https://github.com/eliox98)
* [Kasra Zamanian](https://github.com/kasrazn97)
