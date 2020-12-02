import configparser
import json
import re
from datetime import datetime as dt
from datetime import timedelta as td

from nltk import data, download

DATE_FORMAT = "%Y-%m-%d"
FLOAT_REGEX = "[+-]?([0-9]*[.])?[0-9]+"
ISO_REGEX = "^[a-z]{2}$"
RADIUS_REGEX = "^[0-9]+(km|mi)$"

# TODO: add docstrings

def validate_common(args):
    if args.until is not None:
        try:
            dt.strptime(args.until, DATE_FORMAT)
        except ValueError:
            raise ValueError(
                f"until must be formatted as yyyy-mm-dd, got {args.until}")
    if args.radius is not None:
        if args.geo is None:
            raise ValueError("--near be used together with --geo")
        if re.match(RADIUS_REGEX, args.radius) is None:
            raise ValueError(
                "Radius must be a positive integer followed by either 'mi' or 'km' (e.g. '15km')")
    if args.max_tweets <= 0:
        raise ValueError(
            f"max_tweets must be a positive integer, got {args.max_tweets}")
    validated_args = dict()
    validated_args["q"] = args.q  # can be any string
    validated_args["until"] = args.until
    validated_args["max_tweets"] = args.max_tweets
    return validated_args


def validate_snscrape(args, validated_args):
    if args.since is not None:
        try:
            dt.strptime(args.since, DATE_FORMAT)
        except ValueError:
            raise ValueError(
                f"since must be formatted as yyyy-mm-dd, got {args.since}")
        if dt.strptime(args.since, DATE_FORMAT) >= dt.today():
            raise ValueError(
                f"since can be at most {dt.strftime(dt.today() - td.timedelta(days=1), '%Y-%m-%d')}, got {args.since}")
        if dt.strptime(args.since, DATE_FORMAT) >= dt.strptime(args.until, DATE_FORMAT):
            raise ValueError(f"since must strictly precede until")
    validated_args["since"] = args.since
    validated_args["near"] = args.geo
    return validated_args


def validate_tweepy(args, validated_args):
    if args.geo is not None and re.match(f"^{FLOAT_REGEX},{FLOAT_REGEX}$", args.geo) is None:
        raise ValueError(
            f"geo must have the form 'latitude,longitude' for tweepy, got {args.geo}")
    elif args.geo is not None and args.radius is None:
        raise ValueError(
            f"If using Tweepy with geolocation, both --geo and --radius must be specified")
    if args.lang is not None and re.match(ISO_REGEX, args.lang) is None:
        raise ValueError(f"lang must be an ISO 639-1 code, got {args.lang}")
    validated_args["geocode"] = ','.join([args.geo, args.radius])
    validated_args["lang"] = args.lang
    validated_args["result_type"] = args.result_type
    return validated_args


def validate_args(args):
    validated_args = validate_common(args)
    if args.tweepy:
        return validate_tweepy(args, validated_args)
    return validate_snscrape(args, validated_args)


def load_nltk(analyzer):
    if analyzer == 'textblob-nb':
        try:
            data.find('corpora/movie_reviews')
        except LookupError:
            download('movie_reviews')
        try:
            data.find('tokenizers/punkt')
        except LookupError:
            download('punkt') 
    elif analyzer == 'vader':
        try:
            data.find("sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt")
        except LookupError:
            download('vader_lexicon')


def read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    validated_args = config._sections['bsi-sentiment']
    validated_args['max_tweets'] = config['bsi-sentiment'].getint('max_tweets')
    tweepy = config['bsi-sentiment'].getboolean('tweepy')
    del validated_args['tweepy'] 
    return validated_args, tweepy

def write_config(args, validated_args):
    config = configparser.ConfigParser()
    config['bsi-sentiment'] = {argname: str(argval) for argname, argval in validated_args.items() if argval is not None}
    config['bsi-sentiment']['tweepy'] = str(args.tweepy)
    dest = args.dest if args.dest is not None else './config.ini'
    with open(dest, 'w') as f:
        config.write(f)
