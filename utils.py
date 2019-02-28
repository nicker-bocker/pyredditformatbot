import configparser
from datetime import timedelta

import praw
from loguru import logger as botlogger

botlogger.add("formatbot.log", backtrace=True)
config = configparser.ConfigParser()
config.read("formatbot.cfg")

USERNAME = config['Reddit']['username']

SUBREDDIT = config['Bot']['subreddit']

MAX_POST_AGE_DELTA = timedelta(minutes=int(config['Bot']['max_post_age']))

TEMPLATE = (
    "Hello u/{op}, I'm a bot that can assist you with code-formatting for reddit.\n"
    'I have detected the following potential issue(s) with your submission:\n\n'
    "{issues_str}\n\nIf I am correct then please follow [these instructions]"
    "(https://www.reddit.com/r/learnpython/wiki/faq#wiki_how_do_i_format_code.3F) "
    "to fix your code formatting. Thanks!"
)


@botlogger.catch
def get_reddit():
    reddit_config = config['Reddit']
    reddit = praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        username=reddit_config['username'],
        password=reddit_config['password'],
        user_agent=reddit_config['user_agent'],
    )
    return reddit


@botlogger.catch
def get_comment(op, issues):
    issues_str = '\n'.join(f'{i}. {d}' for i, d in enumerate(issues, 1))
    return TEMPLATE.format(op=op, issues_str=issues_str)
