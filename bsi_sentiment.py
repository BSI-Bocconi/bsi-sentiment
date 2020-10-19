import argparse
import configparser

from sentiment.twitter import search_tweets_tweepy

# TODO: this is just a first version of the CLI tool....

parser = argparse.ArgumentParser(description="BSI Tool for Sentiment Analysis")
parser.add_argument("command", type=str, choices=["analyze", "configure", "download"], help="Action to perform")
parser.add_argument("dest", type=str, nargs="?", help="Output file location. Analysis/configuration/download output file is stored here. Default is current directory.")
parser.add_argument("-c", "--config", type=str, help="Config file location. If action is 'analyze' or 'download', configuration file is read from here.")
parser.add_argument("-q", "--query", type=str, help="A query text to be matched", metavar="query", dest="q")
parser.add_argument("-u", "--until", type=str, help="An upper bound date (not included) to restrict search. Default is today. Tweepy has a 7 day hard limit")
parser.add_argument("-g", "--geocode", type=str, help="Returns only tweets by users within a given radius of the given geolocation. Should be of the form 'latitude,longitude,radius', where radius can be either in 'mi' or 'km'.")
parser.add_argument("-l", "--lang", type=str, help="Restrict language of the tweets retrieved. Must be an ISO 639-1 code (e.g. en, it, etc.). Default is no language restriction.")
parser.add_argument("--result_type", type=str, default="mixed", help="Type of tweets to retrieve. Can be either 'recent', 'popular' or 'mixed'. Default is 'mixed'.")
parser.add_argument("--max_tweets", type=int, default=10, help="The maximum number of tweets to be retrieved. Note that Tweepy limits tweet searches to 300 tweets every 3 hours. Default is 10.")
args = parser.parse_args()

# TODO: validate arguments + add --download_method 'got' when issue with library is fixed
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
        tweets = search_tweets_tweepy(**config['bsi_sentiment'])
    else:
        tweets = search_tweets_tweepy(q=args.q, until=args.until, geocode=args.geocode, lang=args.lang, result_type=args.result_type, max_tweets=args.max_tweets)
    if args.command == 'analyze':
        tweets.get_sentiment() # TODO: more advanced sentiment analysis (at the moment only textblob)
    if args.dest is None:
        args.dest = './result.csv'
    tweets.to_csv(args.dest) # TODO: add options to select columns
 
