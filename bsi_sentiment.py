import argparse
import configparser

from sentiment.twitter import search_tweets_tweepy, search_tweets_sn

# TODO: this is just a first version of the CLI tool....

parser = argparse.ArgumentParser(description="BSI Tool for Sentiment Analysis. Tweets can be downloaded using either Snscrape(default) or Tweepy.")
parser.add_argument("command", type=str, choices=["analyze", "configure", "download"], help="Action to perform.")
parser.add_argument("dest", type=str, nargs="?", help="Output file location. Analysis/configuration/download output file is stored here. Default is current directory.")
parser.add_argument("-c", "--config", type=str, help="Config file location. If action is 'analyze' or 'download', configuration file is read from here.")
parser.add_argument("-q", "--query", type=str, metavar="query", dest="q", help="A query text to be matched")
parser.add_argument("-s", "--since", type=str, help="A lower bound date (UTC) to restrict search. Default is 7 days before today. Used only by Snscrape.")
parser.add_argument("-u", "--until", type=str, help="An upper bound date (not included) to restrict search. Default is today. Tweepy has a 7 day hard limit, while Snscrape has no such limit.")
parser.add_argument("-n", "--geo", type=str, help="Return only tweets by users from given geolocation. It must be a location name (e.g. 'Milan') if using Snscrape or a string of the form 'latitude,longitude' if using Tweepy.")
parser.add_argument("-r", "--radius", type=str, help="Must be used together with --geo. Return only tweets by users within a given radius from the selected location. It must be either in 'mi' or 'km' (e.g. '15km')")
parser.add_argument("-l", "--lang", type=str, help="Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction. Used only by Tweepy.")
parser.add_argument("--user", type=str, metavar="username", dest="username", help="Restrict search  to tweets from specified username.")
parser.add_argument("--result_type", type=str, default="mixed", help="Type of tweets to retrieve. Can be either 'recent', 'popular' or 'mixed'. Default is 'mixed'. Used only by Tweepy.")
parser.add_argument("--max_tweets", type=int, default=10, help="The maximum number of tweets to be retrieved. Default is 10. In the case of Tweepy, if greater API rate limit is reached, the program waits for 15 minutes before trying again.")
parser.add_argument("--tweepy", action="store_true", default=False, dest="tweepy", help="Use Tweepy instead of the default Snscrape to download tweets.")
args = parser.parse_args()

search = search_tweets_tweepy if args.tweepy else search_tweets_sn

# TODO: validate arguments + add --download_method 'got' when issue with library is fixed - Stefano
if args.command == "configure":
    config = configparser.ConfigParser()
    config['bsi_sentiment'] = {argname: str(args.__dict__[argname]) for argname in ['q', 'until', 'geocode', 'lang', 'result_type', 'max_tweets'] if args.__dict__[argname] is not None}
    if args.dest is None:
        args.dest = './config.ini'
    with open(args.dest, 'w') as f:
        config.write(f)
else:
    if args.config is not None:
        config = configparser.ConfigParser()
        config.read(args.config)
        tweets = search(**config['bsi_sentiment'])
    else:
        tweets = search(**args.__dict__)
    if len(tweets) == 0:
        raise Exception("The search returned no tweets. Please double check your query.")
    if args.command == 'analyze':
        tweets.get_sentiment() # TODO: more advanced sentiment analysis (at the moment only textblob) - Kasra + Pietro
    if args.dest is None:
        args.dest = './result.csv'
    tweets.to_csv(args.dest) # TODO: add options to select columns - Stefano
 
