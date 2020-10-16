import argparse
import configparser

# TODO: config.py script should create config.ini file according to the arguments passed by the user from the CLI
# e.g. python config_ini -d ./config/my_config.ini -q "tweet query" --until="2020-10-16"
# The config.ini file will contain all the arguments necessary to run script bsi_sentiment.py with something like
# e.g. python bsi_sentiment.py -f ./config/my_config.ini