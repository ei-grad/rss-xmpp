#!/usr/bin/env python
#
# Copyright (c) 2011 Andrew Grigorev <andrew@ei-grad.ru>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import string
from random import choice

from google.appengine.ext import db

from models import *

def help_cmd(jid, cmd=None):
    """HELP [<command>]
    Show help message for some command.
    """
    return "List of supported commands:\n" + "\n".join([
            func.__doc__.strip() for func in xmpp_commands.values()
        ]) + '\n'

def ping_cmd(jid):
    """PING
    Answer PONG.
    """
    return "PONG\n"

def login_cmd(jid):
    """LOGIN
    Get a key to login via web interface.
    """
    key = "".join([ choice(string.ascii_letters) for i in range(64) ])
    AuthKey(account=Account.by_jid(jid), authkey=key).put()
    return key

def add_cmd(jid, url):
    """ADD <url>
    Adds a feed url.
    """

    account = Account.by_jid(jid)
    feed = Feed.by_url(url)

    if AccountFeed.all().filter('account =', account).filter('feed =', feed).count() == 0:
        AccountFeed(account=account, feed=feed).put()
        return "Feed %s added.\n" % url
    else:
        return "Feed %s already added.\n" % url

def del_cmd(jid, url):
    """DEL <url>
    Removes a feed from your list.
    """
    account = Account.by_jid(jid)
    feed = Feed.by_url(url)

    q = AccountFeed.all().filter('account =', account).filter('feed =', feed)
    count = q.count()

    if count > 0:
        if count != 1: logging.warning('duplicate AccountFeed found!')
        afeeds = q.fetch(count)
        for af in afeeds:
            af.delete()
        return "Feed %s removed.\n" % url
    else:
        return "You are not subscribed to feed %s.\n" % url


def feeds_cmd(jid):
    """FEEDS
    Get list of feeds.
    """
    account = Account.get_or_insert(jid, jid=db.IM('xmpp', jid))
    q = account.accountfeed_set
    count = q.count()
    if count == 0:
        return "You have no feeds.\n"
    return "List of your feeds:\n" + "\n".join([
            af.feed.url for af in q.fetch(count)
        ]) + '\n'


xmpp_commands = {
    'HELP': help_cmd,
    'PING': ping_cmd,
    'LOGIN': login_cmd,
    'ADD': add_cmd,
    'DEL': del_cmd,
    'FEEDS': feeds_cmd,
        }

