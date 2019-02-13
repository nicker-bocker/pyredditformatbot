import re
from typing import Pattern

import praw

import templates
import utils

SUBREDDIT = 'testingground4bots'


class Issue:
    pattern: Pattern = None
    description: str = None

    def is_issue(self, text):
        if self.pattern is None:
            raise NotImplementedError('Pattern not defined')
        search = self.pattern.search(text)
        return bool(search)


class IssueMultiInline(Issue):
    # two or more consecutive lines with inline code
    pattern = re.compile(r'(?:\s*?`.*?`\s*?[\n]+){2,}', re.MULTILINE)
    description = "Multiple consecutive lines have been found to contain inline formatting."


class IssueCodeBlock(Issue):
    # def found on left margin
    pattern = re.compile(r'''
        ^(?:                    #is on the left-hand margin (not four-spaces in)
        class\s.*?              #class detection
        |def\s.*?\(.*?\)        #function detection
        |for\s.*?in.*?          #for loop detection
        ):
        ''', re.VERBOSE|re.MULTILINE)
    description = "Python code found in submission but not encapsulated in a code block."


issues = [
    IssueMultiInline(),
    IssueCodeBlock(),
]


def main():
    reddit = utils.get_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)
    submission: praw.reddit.models.Submission
    me = reddit.user.me().name.lower()
    for submission in subreddit.new():
        text = submission.selftext
        op = submission.author.name
        issues_found = [x.description for x in issues if x.is_issue(text)]
        if not issues_found:
            continue
        for comment in submission.comments:
            if comment.author.name.lower() == me:
                break
        else:
            issues_str = '\n'.join(f'{i}. {des}' for i, des in enumerate(issues_found, 1))
            my_comment = templates.auto.format(op=op, issues_str=issues_str)
            submission.reply(my_comment)
            print('Replied to', op)


if __name__ == '__main__':
    main()
