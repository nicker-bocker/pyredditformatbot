import pytest
import utils
from formatbot import *
from issues import *


text_def = '''
x = 1
def func(p, n):
    pass

'''

text_class = '''
x = 1
class MyClass:
    pass

'''

text_multi_inline = '''
`x = 1`
`def func(p, n):`
    `pass`
'''

text_for_loop = '''
Here is my issue 

for x, y, z in collection:
   print(x, y, z)
   
'''

text_bare_try = '''
Pls hLP my codes!!!
try:
x = "FrEe homEwork Hlp"
except:
pass
'''

text_proper = '''
for tricking regex:
    def func(p):
        pass
    class MyClass:
        pass
    for x in y:
        pass
    try:
        x = True
    except:
        pass
'''
def test_reddit_auth():
    reddit = utils.get_reddit()
    login_name = reddit.user.me().name
    assert utils.USERNAME.lower() == login_name.lower()

def test_raise_not_implemented():
    class TestClass(BaseIssue): pass
    with pytest.raises(NotImplementedError):
        x = TestClass()
        print(str(x))
    with pytest.raises(NotImplementedError):
        x = TestClass()
        print(x.is_issue(text_proper))

def test_issues_regex():
    issue_block = NoCodeBlockIssue()
    issue_inline = MultipleInlineIssue()
    assert issue_block.is_issue(text_bare_try)
    assert issue_block.is_issue(text_def)
    assert issue_block.is_issue(text_class)
    assert issue_block.is_issue(text_for_loop)
    assert issue_inline.is_issue(text_multi_inline)
    assert not issue_inline.is_issue(text_proper)
    assert not issue_block.is_issue(text_proper)

