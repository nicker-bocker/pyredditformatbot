import praw
import configparser

def get_reddit():
    config = configparser.ConfigParser()
    config.read("formatbot.cfg")
    reddit_config = config['Reddit']
    IAM = reddit_config['username']
    r = praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        username=IAM,
        password=reddit_config['password'],
        user_agent='CodeFormatBot',
    )
    return r