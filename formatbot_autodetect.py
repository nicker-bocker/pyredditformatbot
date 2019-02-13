import configparser
import re
import time
from datetime import datetime
from datetime import timedelta
from typing import Pattern

import praw
from praw.exceptions import APIException

SUBREDDIT = 'learnpython'
MAX_TIME_LAPSE = timedelta(minutes=30)
TEMPLATE = (
    "Hello u/{op}, I'm a bot that can assist you with code-formatting for reddit.\n"
    'I have detected the following potential issue(s) with your submission:\n\n'
    "{issues_str}\n\n"
    "If I am correct then please follow "
    "[these instructions](https://www.reddit.com/r/learnpython/wiki/faq#wiki_how_do_i_format_code.3F) "
    "to fix your code formatting. Thanks!"
)


class Issue:
    pattern: Pattern = None
    description: str = None

    def is_issue(self, text):
        if self.pattern is None:
            raise NotImplementedError('Pattern not defined')
        search = self.pattern.search(text)
        return bool(search)


class IssueMultiInline(Issue):
    # two or more consecutive lines with inline code (wrong format button)
    pattern = re.compile(r'(?:\s*?`.*?`\s*?[\n]+){2,}', re.MULTILINE)
    description = "Multiple consecutive lines have been found to contain inline formatting."


class IssueCodeBlock(Issue):
    pattern = re.compile(r'''
        ^(?:                    #is on the left-hand margin (not four-spaces in)
        class\s.*?              #class detection
        |def\s.*?\(.*?\)        #function detection
        |for\s.*?in.*?          #for loop detection
        ):
        ''', re.VERBOSE | re.MULTILINE)
    description = "Python code found in submission text but not encapsulated in a code block."


VALIDATORS = [
    IssueMultiInline(),
    IssueCodeBlock(),
]


def get_reddit():
    """
    Get a praw.Reddit instance from config
    """
    config = configparser.ConfigParser()
    config.read("formatbot.cfg")
    reddit_config = config['Reddit']
    reddit = praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        username=reddit_config['username'],
        password=reddit_config['password'],
        user_agent='CodeFormatBot',
    )
    return reddit


def get_comment(op, issues):
    issues_str = '\n'.join(f'{i}. {description}'
                           for i, description in enumerate(issues, 1))
    return TEMPLATE.format(op=op, issues_str=issues_str)


def judge_submissions(reddit):
    subreddit = reddit.subreddit(SUBREDDIT)
    me = reddit.user.me().name.lower()
    for submission in subreddit.stream.submissions():
        op = submission.author.name
        body_text = submission.selftext
        issues_found = [v.description for v in VALIDATORS if v.is_issue(body_text)]
        if not issues_found:
            print(f"no issues with {op}'s post")
            continue
        for comment in submission.comments:
            if comment.author.name.lower() == me:
                print(f"I've already commented on {op}'s post.")
                break
        else:
            print('I GOT BEEF WITH', op)
            time_created = datetime.fromtimestamp(submission.created_utc)
            time_current = datetime.now()
            is_recent = (time_current - time_created <= MAX_TIME_LAPSE)
            if is_recent:
                try:
                    submission.reply(get_comment(op, issues_found))
                    print('Replied to', op)
                    time.sleep(10 * 60)  # comment cool-down, need karma!
                except APIException as exc:
                    print(exc)
            else:
                print('...but post is old.')


def main():
    reddit = get_reddit()
    judge_submissions(reddit)


if __name__ == '__main__':
    main()
