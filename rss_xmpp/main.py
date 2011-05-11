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

import logging
logging.basicConfig(level=logging.DEBUG, format="%(funcName)s: %(message)s")

from google.appengine.api import users, xmpp
from google.appengine.ext import db
from google.appengine.ext.webapp import WSGIApplication, RequestHandler, \
        template
from google.appengine.ext.webapp.util import run_wsgi_app, login_required

from models import *
from bot import xmpp_commands


class XMPPHandler(RequestHandler):

    def post(self):
        self.handle_message(xmpp.Message(self.request.POST))

    def handle_message(self, message):
        logging.debug("message from %s: %s" % (message.sender, message.body))
        # XXX: use shlex.split here
        args = message.body.split()
        cmd = args.pop(0).upper()
        logging.debug("command from %s: %s(%s)" % (message.sender, cmd, ", ".join(args)))
        if cmd not in xmpp_commands:
            logging.debug("%s: no such command" % cmd)
            message.reply(xmpp_commands['HELP'](message.sender))
        else:
            try:
                message.reply(xmpp_commands[cmd](message.sender, *args))
            except TypeError:
                logging.debug("%s: wrong args %s" % (cmd, args))
                message.reply(xmpp_commands['HELP'](message.sender, cmd))

class RequestHandler(RequestHandler):
    def render(self, page, context=None):
        if context is None: context = {}
        context['user'] = users.get_current_user()
        context['logout_url'] = users.create_logout_url(self.request.uri)
        self.response.out.write(template.render('templates/%s.html' % page, context))

class IndexHandler(RequestHandler):
    def get(self):
        self.render("index")

class LoginHandler(RequestHandler):

    def get(self, error=None):
        self.render("login", {'error': error})

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        key = self.request.get('key', None)
        if key is None:
            self.get()
            return
        q = AuthKey.all().filter('authkey =', key)
        if q.count() == 0:
            self.get("Wrong key!")
            return
        authkey = q.fetch(1)[0]
        logging.debug('user %s associated with jid %s' % (user.nickname, authkey.account.jid.address))
        account = authkey.account
        authkey.delete()
        account.user = user
        account.put()
        self.render("login_ok", {'account': account})

class ListHandler(RequestHandler):
    @login_required
    def get(self):
        q = Account.all().filter("user =", users.get_current_user())
        accounts = q.fetch(q.count())
        logging.debug(accounts)
        self.render("list", {'accounts': accounts})

class NotFoundHandler(RequestHandler):
    def get(self):
        self.response.set_status(404)
        self.render('404')
    def post(self):
        self.response.set_status(404)
        self.render('404')

def main():
    application = WSGIApplication([
                ('/', IndexHandler),
                ('/login', LoginHandler),
                ('/list', ListHandler),
                ('/_ah/xmpp/message/chat/', XMPPHandler),
                ('.*', NotFoundHandler),
            ], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()

