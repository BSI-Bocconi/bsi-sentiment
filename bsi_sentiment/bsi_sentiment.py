from .parser import parser
from .twitter import search_tweets_tweepy, search_tweets_sn
from .utils import validate_args, load_nltk, read_config, write_config


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
            # Load (or download, if not already done) required NLTK resources
            load_nltk(args.analyzer)

            # Sentiment analysis
            tweets.get_sentiment(method=args.analyzer)
        if args.dest is None:
            args.dest = './result.csv'
        tweets.to_csv(args.dest)


if __name__ == '__main__':
    main()
