import time
from datetime import datetime

import issues
import utils
from utils import botlogger

import logging

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('prawcore')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

@botlogger.catch
def main():
    botlogger.info('Bot started')
    reddit = utils.get_reddit()
    subreddit = reddit.subreddit(utils.SUBREDDIT)
    me = reddit.user.me().name.lower()
    for submission in subreddit.stream.submissions():
        try:
            op = submission.author.name
            submission_text = submission.selftext
            issues_found = [str(v) for v in issues.VALIDATORS if v.is_issue(submission_text)]
            if not issues_found:
                botlogger.info(f"No issues found in {op}'s post")
                continue
            botlogger.info(f"Issues found in {op}'s submission")
            for issue in issues_found:
                botlogger.info(issue)

            for comment in submission.comments:
                if comment.author.name.lower() == me:
                    botlogger.info(f"I've already commented on {op}'s post. Moving on.")
                    break
            else:
                time_created = datetime.fromtimestamp(submission.created_utc)
                if datetime.now() - time_created <= utils.MAX_POST_AGE_DELTA:
                    submission.reply(utils.get_comment(op, issues_found))
                    botlogger.info(f"Comment left on {op}'s post")
                    time.sleep(10)  # comment cool-down, need karma!
                    botlogger.info("Done sleeping for now.")
                else:
                    botlogger.info('No comment left due to age of post.')
        except Exception as exc:
            print(exc)


if __name__ == '__main__':
    main()
