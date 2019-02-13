import configparser
import re
from typing import Pattern

import praw

SUBREDDIT = 'learnpython'

template_auto = (
    "Hello u/{op}, I'm a bot that can assist you with code-formatting for reddit. "
    'I have detected the following potential issue(s) with your submission:\n\n'
    "{issues_str}\n\n"
    "If I am correct then please follow "
    "[these instructions](https://www.reddit.com/r/learnpython/wiki/faq#wiki_how_do_i_format_code.3F) "
    "to fix your code formatting. Thanks!"
)


def get_reddit():
    """
    Get a praw.Reddit instance from config
    :return: praw.Reddit instance
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
    description = "Python code found in submission but not encapsulated in a code block."


issues = [
    IssueMultiInline(),
    IssueCodeBlock(),
]


def main():
    reddit = get_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)
    submission: praw.reddit.models.Submission
    me = reddit.user.me().name.lower()
    for submission in subreddit.stream.submissions():
        text = submission.selftext
        op = submission.author.name
        issues_found = [x.description for x in issues if x.is_issue(text)]
        if not issues_found:
            print(f"no issues with {op}'s post")
            continue
        for comment in submission.comments:
            if comment.author.name.lower() == me:
                print(f"I've already commented on {op}'s post.")
                break
        else:
            issues_str = '\n'.join(f'{i}. {des}' for i, des in enumerate(issues_found, 1))
            my_comment = template_auto.format(op=op, issues_str=issues_str)
            submission.reply(my_comment)
            print('Replied to', op)


if __name__ == '__main__':
    main()
