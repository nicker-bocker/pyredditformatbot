import re
from utils import botlogger

class BaseIssue:
    _pattern = None
    _description = None

    def __str__(self):
        if self._description is None:
            mssg = f'No error description assigned to {type(self).__name__}._description'
            botlogger.error(mssg)
            raise NotImplementedError(mssg)
        return self._description

    def is_issue(self, submission_text):
        try:
            return bool(self._pattern.search(submission_text))
        except AttributeError:
            mssg = f'No error compiled regex object assigned to {type(self).__name__}._pattern'
            botlogger.error(mssg)
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
