import configparser
import re
import time
from datetime import datetime
from datetime import timedelta

import praw
from loguru import logger

logger.add("formatbot.log", backtrace=True)

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
    _pattern = None
    _description = None

    def __str__(self):
        if self._description is None:
            mssg = f'No error description assigned to {type(self).__name__}._description'
            logger.error(mssg)
            raise NotImplementedError(mssg)
        return self._description

    def is_issue(self, submission_text):
        try:
            return bool(self._pattern.search(submission_text))
        except AttributeError:
            mssg = f'No error compiled regex object assigned to {type(self).__name__}._pattern'
            logger.error(mssg)
            raise NotImplementedError(mssg)


class MultipleInlineIssue(BaseIssue):
    _description = "Multiple consecutive lines have been found to contain inline formatting."
    _pattern = re.compile(r'(?:\s*?`.*?`\s*?[\n]+){2,}', re.MULTILINE)


class NoCodeBlockIssue(BaseIssue):
    _description = "Python code found in submission text but not encapsulated in a code block."
    _pattern = re.compile(r'''
        ^(?:                        # any of the following is on the left-hand margin (not four spaces in)
            try                     # try block
            |class\s.*?             # class detection
            |def\s.*?\(.*?\)        # function detection
            |for\s.*?\sin\s.*?      # for loop detection
        ):                          # END NON-CAPTURE GROUP -- literal colon
        ''', re.VERBOSE | re.MULTILINE)


VALIDATORS = [MultipleInlineIssue(), NoCodeBlockIssue(), ]


@logger.catch
def get_reddit():
    config = configparser.ConfigParser()
    config.read("formatbot.cfg")
    reddit_config = config['Reddit']
    reddit = praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        username=reddit_config['username'],
        password=reddit_config['password'],
        user_agent='CodeFormatHelperBot', )
    return reddit


@logger.catch
def get_comment(op, issues):
    issues_str = '\n'.join(f'{i}. {d}' for i, d in enumerate(issues, 1))
    return TEMPLATE.format(op=op, issues_str=issues_str)


@logger.catch
def judge_submissions():
    reddit = get_reddit()
    subreddit = reddit.subreddit('learnpython')
    me = reddit.user.me().name.lower()
    for submission in subreddit.stream.submissions():
        try:
            op = submission.author.name
            submission_text = submission.selftext
            issues_found = [str(v) for v in VALIDATORS if v.is_issue(submission_text)]
            if not issues_found:
                logger.info(f"No issues found in {op}'s post")
                continue
            logger.info(f"Issues found in {op}'s submission")
            for issue in issues_found:
                logger.info(issue)

            for comment in submission.comments:
                if comment.author.name.lower() == me:
                    logger.info(f"I've already commented on {op}'s post. Moving on.")
                    break
            else:
                time_created = datetime.fromtimestamp(submission.created_utc)
                if datetime.now() - time_created <= MAX_TIME_LAPSE:
                    submission.reply(get_comment(op, issues_found))
                    logger.info(f"Comment left on {op}'s post")
                    time.sleep(10 * 60)  # comment cool-down, need karma!
                    logger.info("Done sleeping for now.")
                else:
                    logger.info('No comment left due to age of post.')
        except Exception as exc:
            print(exc)


if __name__ == '__main__':
    logger.info('Bot started')
    judge_submissions()
