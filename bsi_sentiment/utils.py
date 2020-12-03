import configparser
import re
from datetime import datetime as dt
from datetime import timedelta as td

from nltk import data, download

DATE_FORMAT = "%Y-%m-%d"
FLOAT_REGEX = "[+-]?([0-9]*[.])?[0-9]+"
ISO_REGEX = "^[a-z]{2}$"
RADIUS_REGEX = "^[0-9]+(km|mi)$"


def validate_common(args):
    """
    Validate CLI arguments common to both Tweepy and Snscrape.

    Parameters
    ----------
    args (argparse.Namespace): arguments passed by the user through the command line.

    Returns
    -------
    validated_args (dict): validated arguments.
    """
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
    validated_args["quiet"] = args.quiet
    return validated_args


def validate_snscrape(args, validated_args):
    """
    Validate CLI arguments specific to Snscrape.

    Parameters
    ----------
    args (argparse.Namespace): arguments passed by the user through the command line.
    validated_args (dict): dict containing the arguments already validated by validate_common().

    Returns
    -------
    validated_args (dict): validated arguments.
    """
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
            raise ValueError("since must strictly precede until")
    validated_args["since"] = args.since
    validated_args["near"] = args.geo
    return validated_args


def validate_tweepy(args, validated_args):
    """
    Validate CLI arguments specific to Snscrape.

    Parameters
    ----------
    args (argparse.Namespace): arguments passed by the user through the command line.
    validated_args (dict): dict containing the arguments already validated by validate_common().

    Returns
    -------
    validated_args (dict): validated arguments.
    """
    if args.geo is not None and re.match(f"^{FLOAT_REGEX},{FLOAT_REGEX}$", args.geo) is None:
        raise ValueError(
            f"geo must have the form 'latitude,longitude' for tweepy, got {args.geo}")
    elif (args.geo is not None and args.radius is None) or (args.geo is None and args.radius is not None):
        raise ValueError(
            "If using Tweepy with geolocation, both --geo and --radius must be specified")
    elif args.geo is not None and args.radius is not None:
        validated_args["geocode"] = ','.join([args.geo, args.radius])
    if args.lang is not None and re.match(ISO_REGEX, args.lang) is None:
        raise ValueError(f"lang must be an ISO 639-1 code, got {args.lang}")
    validated_args["lang"] = args.lang
    validated_args["result_type"] = args.result_type
    validated_args["credentials_path"] = args.credentials
    return validated_args


def validate_args(args):
    """
    Validate CLI arguments.

    Parameters
    ----------
    args (argparse.Namespace): arguments passed by the user through the command line.

    Returns
    -------
    validated_args (dict): validated arguments.
    """
    validated_args = validate_common(args)
    if args.tweepy:
        return validate_tweepy(args, validated_args)
    return validate_snscrape(args, validated_args)


def load_nltk(analyzer, quiet=False):
    """
    Check if resources necessary to use 'analyzer' are already present locally. Else, download them.

    Parameters
    ----------
    analyzer (str): method to use for sentiment analysis.
    """
    if analyzer == 'textblob-nb':
        try:
            data.find('corpora/movie_reviews')
        except LookupError:
            download('movie_reviews', quiet=quiet)
        try:
            data.find('tokenizers/punkt')
        except LookupError:
            download('punkt', quiet=quiet)
    elif analyzer == 'vader':
        try:
            data.find("sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt")
        except LookupError:
            download('vader_lexicon', quiet=quiet)


def read_config(config_path):
    """
    Read configuration file containing parameters of twitter search query and analysis.

    Parameters:
    config_path (Union[str, pathlib.Path]): path of configuration file.

    Returns:
    validated_args (dict): validated arguments for twitter search and tweet analysis.
    tweepy (bool): whether to use Tweepy instead of Snscrape to download tweets.
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    validated_args = config._sections['bsi-sentiment']
    validated_args['max_tweets'] = config['bsi-sentiment'].getint('max_tweets')
    tweepy = config['bsi-sentiment'].getboolean('tweepy')
    del validated_args['tweepy']
    return validated_args, tweepy


def write_config(args, validated_args):
    """
    Write configuration file containing parameters of twitter search query and analysis to args.dest.

    Parameters
    ----------
    args (argparse.Namespace): arguments passed by the user through the command line.
    validated_args (dict): validated arguments for twitter search and tweet analysis.
    """
    config = configparser.ConfigParser()
    config['bsi-sentiment'] = {argname: str(argval) for argname, argval in validated_args.items() if argval is not None}
    config['bsi-sentiment']['tweepy'] = str(args.tweepy)
    dest = args.dest if args.dest is not None else './config.ini'
    with open(dest, 'w') as f:
        config.write(f)
