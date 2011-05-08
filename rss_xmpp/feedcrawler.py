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

import shlex
import logging
logging.basicConfig(level=logging.DEBUG, format="%(funcName)s: %(message)s")

from datetime import datetime

from google.appengine.api import users, xmpp, urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import WSGIApplication, RequestHandler, \
        template
from google.appengine.ext.webapp.util import run_wsgi_app, login_required

from models import *
import feedparser


def tt2dt(tt):
    "timetuple->datetime"
    return datetime(*tt[:6])

def handle_item(feed, item):
    msg = "\n".join([ item[kw] for kw in ['title', 'link', 'description' ] ])
    logging.debug("Feed: %s\nMessage: %s" % (feed.url, msg))
    q = feed.accountfeed_set
    afeeds = q.fetch(q.count())
    logging.debug('%d accountfeeds found' % len(afeeds))
    for af in afeeds:
        logging.debug("Sending to: %s" % af.account.jid.address)
        xmpp.send_message(af.account.jid.address, msg)

def handle_feed(feed, result):
    logging.debug('got %s - %d' % (feed.url, result.status_code))
    if result.status_code != 200:
        return
    d = feedparser.parse(result.content)
    logging.debug('last item in db: %s' % feed.last_date)
    logging.debug('%d entries' % len(d.entries))
    ignored = 0
    last_date = feed.last_date
    for item in d.entries:
        item_date = tt2dt(item.updated_parsed)
        if item_date <= last_date:
            ignored += 1
            continue
        logging.debug('new item %s %s' % (item.id, item_date))
        if item_date > feed.last_date:
            feed.last_date = item_date
        handle_item(feed, item)
    logging.debug('%d entries ignored' % ignored)
    feed.put()


def get_callback(feed, rpc):
    def q():
        handle_feed(feed, rpc.get_result())
    return q

class FeedingHandler(RequestHandler):
    def get(self):
        logging.debug('feedcrawler started')
        rpcs = []
        feeds = Feed.all().fetch(Feed.all().count())
        logging.debug('%d feeds found' % len(feeds))
        for feed in feeds:
            if feed.accountfeed_set.count() == 0:
                logging.debug('No accountfeed found for %s feed. Ignoring.' % feed.url)
                continue
            # TODO: implement dynamic update interval
            rpc = urlfetch.create_rpc()
            rpc.callback = get_callback(feed, rpc)
            urlfetch.make_fetch_call(rpc, feed.url)
            rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()


def main():
    application = WSGIApplication([
                ('/cron/feeding', FeedingHandler),
            ], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()

