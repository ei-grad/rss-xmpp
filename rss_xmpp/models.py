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

from datetime import datetime

from google.appengine.ext import db


class Account(db.Model):
    user = db.UserProperty()
    jid = db.IMProperty()

    @classmethod
    def by_jid(cls, jid):
        return cls.get_or_insert(jid, jid=db.IM('xmpp', jid))

    def delete(self):
        for prop in dir(self):
            if prop.endswith('_set'):
                db.delete(getattr(self, prop))
        super(Account, self).delete()

class AuthKey(db.Model):
    account = db.ReferenceProperty(Account)
    authkey = db.StringProperty(required=True)

class Feed(db.Model):
    url = db.LinkProperty(required=True)
    last_date = db.DateTimeProperty(default=datetime.fromtimestamp(0))
    updated = db.DateTimeProperty(default=datetime.fromtimestamp(0))
    update_interval = db.IntegerProperty(required=True, default=5)
    min_interval = db.IntegerProperty(required=True, default=1)
    max_interval = db.IntegerProperty(required=True, default=30)

    @classmethod
    def by_url(cls, url):
        return cls.get_or_insert(url, url=url)

class AccountFeed(db.Model):
    feed = db.ReferenceProperty(Feed)
    account = db.ReferenceProperty(Account)
    keywords = db.StringProperty()

