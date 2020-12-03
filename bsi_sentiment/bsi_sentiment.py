from .parser import parser
from .twitter import search_tweets_tweepy, search_tweets_sn
from .utils import validate_args, read_config, write_config


def main():
    args = parser.parse_args()
    validated_args = validate_args(args)

    if args.command == "configure":
        write_config(args, validated_args)
    else:
        if args.config is not None:
            validated_args, tweepy = read_config(args.config)
            search = search_tweets_tweepy if tweepy else search_tweets_sn
        else:
            search = search_tweets_tweepy if args.tweepy else search_tweets_sn
        tweets = search(**validated_args)
        if len(tweets) == 0:
            raise Exception("The search returned no tweets. Please double check your query.")
        if args.command == 'analyze':
            tweets.get_sentiment(method=args.analyzer, quiet=args.quiet)
        if args.dest is None:
            args.dest = './result.csv'
        tweets.to_csv(args.dest, quiet=args.quiet)


if __name__ == '__main__':
    main()
