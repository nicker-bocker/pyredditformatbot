import configparser
import re
import time
from datetime import datetime, timedelta

import praw

SUBREDDIT = 'learnpython'
MAX_TIME_LAPSE = timedelta(minutes=30)
TEMPLATE = (
    "Hello u/{op}, I'm a bot that can assist you with code-formatting for reddit.\n"
    'I have detected the following potential issue(s) with your submission:\n\n'
    "{issues_str}\n\nIf I am correct then please follow [these instructions]"
    "(https://www.reddit.com/r/learnpython/wiki/faq#wiki_how_do_i_format_code.3F) "
    "to fix your code formatting. Thanks!"
)

class BaseIssue:
    pattern = description = None

    def is_issue(self, text):
        if self.pattern is None:
            raise NotImplementedError('Pattern not defined')
        search = self.pattern.search(text)
        return bool(search)


class MultipleInlineIssue(BaseIssue):
    description = "Multiple consecutive lines have been found to contain inline formatting."
    pattern = re.compile(r'(?:\s*?`.*?`\s*?[\n]+){2,}', re.MULTILINE)


class NoCodeBlockIssue(BaseIssue):
    description = "Python code found in submission text but not encapsulated in a code block."
    pattern = re.compile(r'''
        ^(?:                    #Any of the following is on the left-hand margin (not four spaces in)
        try                     #try block
        |class\s.*?             #class detection
        |def\s.*?\(.*?\)        #function detection
        |for\s.*?\sin\s.*?      #for loop detection
        ):
        ''', re.VERBOSE | re.MULTILINE)


VALIDATORS = [MultipleInlineIssue(), NoCodeBlockIssue(), ]


def get_reddit():
    config = configparser.ConfigParser()
    config.read("formatbot.cfg")
    reddit_config = config['Reddit']
    reddit = praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        username=reddit_config['username'],
        password=reddit_config['password'],
        user_agent='CodeFormatHelperBot',)
    return reddit


def get_comment(op, issues):
    issues_str = '\n'.join(f'{i}. {d}' for i, d in enumerate(issues, 1))
    return TEMPLATE.format(op=op, issues_str=issues_str)


def judge_submissions():
    reddit = get_reddit()
    subreddit = reddit.subreddit('learnpython')
    me = reddit.user.me().name.lower()
    for submission in subreddit.stream.submissions():
        try:
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
                if (time_current - time_created <= MAX_TIME_LAPSE):
                    submission.reply(get_comment(op, issues_found))
                    print('Replied to', op)
                    time.sleep(10 * 60)  # comment cool-down, need karma!
                else:
                    print('...but post is too old.')
        except Exception as exc:
            print(exc)


if __name__ == '__main__':
    judge_submissions()