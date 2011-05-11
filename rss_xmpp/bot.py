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

import locale
LANG, ENCODING = locale.getdefaultlocale()
locale.setlocale(locale.LC_ALL, (LANG, ENCODING))
import string
from random import choice
import logging

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

def add_cmd(jid, url, *keywords):
    """ADD <url> [keywords]
    Adds a feed url.
    """

    account = Account.by_jid(jid)
    feed = Feed.by_url(url)
    keywords = ",".join(keywords)

    if AccountFeed.all().filter('account =', account).filter('feed =', feed).filter('keywords =', keywords).count() == 0:
        AccountFeed(account=account, feed=feed, keywords=keywords).put()
        if keywords:
            return "Feed %s added with keywords '%s'.\n" % (url, keywords)
        else:
            return "Feed %s added.\n" % url
    else:
        if keywords:
            return "Feed %s has already been added with keywords '%s'.\n" % (url, keywords)
        else:
            return "Feed %s has already been added.\n" % url

def del_cmd(jid, url, *keywords):
    """DEL <url> [keywords]
    Removes a feed from your list.
    """

    account = Account.by_jid(jid)
    feed = Feed.by_url(url)
    keywords = ",".join(keywords)

    q = AccountFeed.all().filter('account =', account).filter('feed =', feed).filter('keywords =', keywords)
    count = q.count()

    if count > 0:
        if count != 1:
            logging.warning('Duplicate AccountFeed found!')
        afeeds = q.fetch(count)
        for af in afeeds:
            af.delete()
        if keywords:
            return "Feed %s with keywords '%s' removed.\n" % (url, keywords)
        else:
            return "Feed %s removed.\n" % url
    else:
        if keywords:
            return "You are not subscribed to feed %s with keywords '%s'.\n" % (url, keywords)
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
            '%s %s' % (af.feed.url, af.keywords)
                if af.keywords else af.feed.url
                    for af in q.fetch(count)
        ]) + '\n'

def destroy_cmd(jid):
    """DESTROY
    Remove all data associated with your account.
    """
    msg = (
            "You are about to destroy your account. Remind you about your "
            "feeds list. It will be lost.\n%s\n"
            "Your account has been destroyed.\n\n"
            "Thank you for using this service. Goodbye.\n"
           ) % feeds_cmd(jid)
    Account.by_jid(jid).delete()
    return msg

xmpp_commands = {
    'HELP': help_cmd,
    'PING': ping_cmd,
    'LOGIN': login_cmd,
    'ADD': add_cmd,
    'DEL': del_cmd,
    'DESTROY': destroy_cmd,
    'FEEDS': feeds_cmd,
        }

