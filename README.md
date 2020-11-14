# BSI Sentiment Analysis Pipeline

CLI tool to download tweets and perform basic sentiment analysis on them.

## Usage

```console
foo@bar:~$ bsi_sentiment -h

usage: sentiment [-h] [-c CONFIG] [-q query] [-s SINCE] [-u UNTIL] [-n GEO] [-r RADIUS] [-l LANG] [--user username] [--result_type {recent,popular,mixed}] [--max_tweets MAX_TWEETS]
                 [--tweepy]
                 {analyze,configure,download} [dest]

BSI Tool for Sentiment Analysis. Tweets can be downloaded using either Snscrape(default) or Tweepy.

positional arguments:
  {analyze,configure,download}
                        Action to perform.
  dest                  Output file location. Analysis/configuration/download output file is stored here. Default is current directory.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file location. If action is 'analyze' or 'download', configuration file is read from here.
  -q query, --query query
                        A query text to be matched
  -s SINCE, --since SINCE
                        A lower bound date (UTC) to restrict search. Default is 7 days before today. Used only by Snscrape.
  -u UNTIL, --until UNTIL
                        An upper bound date (not included) to restrict search. Default is today. Tweepy has a 7 day hard limit, while Snscrape has no such limit.
  -n GEO, --geo GEO     Return only tweets by users from given geolocation. It must be a location name (e.g. 'Milan') if using Snscrape or a string of the form 'latitude,longitude' if
                        using Tweepy.
  -r RADIUS, --radius RADIUS
                        Must be used together with --geo. Return only tweets by users within a given radius from the selected location. It must be either in 'mi' or 'km' (e.g. '15km')
  -l LANG, --lang LANG  Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction. Used only by Tweepy.
  --user username       Restrict search to tweets from specified username.
  --result_type {recent,popular,mixed}
                        Type of tweets to retrieve. Can be either 'recent', 'popular' or 'mixed'. Default is 'mixed'. Used only by Tweepy.
  --max_tweets MAX_TWEETS
                        The maximum number of tweets to be retrieved. Default is 10. In the case of Tweepy, if greater API rate limit is reached, the program waits for 15 minutes before
                        trying again.
  --tweepy              Use Tweepy instead of the default Snscrape to download tweets.
```