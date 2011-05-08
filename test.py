import os

from dev_appserver import fix_sys_path
fix_sys_path()
from google.appengine.ext.testbed import Testbed
tb = Testbed()
tb.activate()
os.environ['APPLICATION_ID'] = 'rss-xmpp'
tb.init_xmpp_stub()
tb.init_datastore_v3_stub()
tb.init_urlfetch_stub()

from rss_xmpp.main import *
from google.appengine.api import xmpp
from rss_xmpp import feedcrawler

import unittest

url = 'http://feeds.feedburner.com/github'

class XMPPTestMessage(xmpp.Message):
    def reply(self, body, message_type="chat", raw_xml=False, send_message=xmpp.send_message):
        super(XMPPTestMessage, self).reply(body, message_type, raw_xml, send_message)
        print('\nSent message:\n' + '='*80 + '\n' + body + '='*80 + '\n')

class TestRSSXMPP(unittest.TestCase):

    def setUp(self):

        self.from_addr = 'test@example.com'
        self.to_addr = 'rss-xmpp@appspot.com'
        self.xmpp_handler = XMPPHandler()
        self.sample_rss = """
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
<channel>
  <title>Sample Feed</title>
  <description>For documentation &lt;em&gt;only&lt;/em&gt;</description>
  <link>http://example.org/</link>
  <pubDate>Sat, 07 Sep 2002 0:00:01 GMT</pubDate>
  <!-- other elements omitted from this example -->
  <item>
    <title>First entry title</title>
    <link>http://example.org/entry/3</link>
    <description>Watch out for &lt;span style="background-image:
url(javascript:window.location='http://example.org/')"&gt;nasty
tricks&lt;/span&gt;</description>
    <pubDate>Sat, 07 Sep 2002 0:00:01 GMT</pubDate>
    <guid>http://example.org/entry/3</guid>
    <!-- other elements omitted from this example -->
  </item>
</channel>
</rss>
"""

    def get_message(self, msg):
        return XMPPTestMessage({'from': self.from_addr, 'to': self.to_addr, 'body': msg})

    def handle_message(self, msg):
        return self.xmpp_handler.handle_message(self.get_message(msg))

    def test_handle_message(self):
        self.handle_message('help')
        self.handle_message('abrakadabra')

    def test_xmpp_commands(self):
        self.assertEqual(xmpp_commands['PING'](self.from_addr), 'PONG\n')
        self.assertEqual(xmpp_commands['ADD'](self.from_addr, url), 'Feed %s added.\n' % url)
        self.assertEqual(xmpp_commands['ADD'](self.from_addr, url), 'Feed %s already added.\n' % url)
        self.assertEqual(xmpp_commands['FEEDS'](self.from_addr), 'List of your feeds:\n%s\n' % url)
        self.assertEqual(xmpp_commands['DEL'](self.from_addr, url), 'Feed %s removed.\n' % url)
        self.assertEqual(xmpp_commands['DEL'](self.from_addr, url), 'You are not subscribed to feed %s.\n' % url)
        self.assertEqual(xmpp_commands['FEEDS'](self.from_addr), 'You have no feeds.\n')

    def test_handle_feed(self):

        class Result(object):
            status_code = 200
            content = self.sample_rss

        xmpp_commands['ADD'](self.from_addr, url)
        feedcrawler.handle_feed(Feed.all().fetch(1)[0], Result())
        xmpp_commands['DEL'](self.from_addr, url)

    def test_feedeinghandler(self):
        xmpp_commands['ADD'](self.from_addr, url)
        f = feedcrawler.FeedingHandler()
        f.get()
        xmpp_commands['DEL'](self.from_addr, url)

#    def test_shuffle(self):
#        # make sure the shuffled sequence does not lose any elements
#        random.shuffle(self.seq)
#        self.seq.sort()
#        self.assertEqual(self.seq, range(10))
#
#        # should raise an exception for an immutable sequence
#        self.assertRaises(TypeError, random.shuffle, (1,2,3))
#
#    def test_choice(self):
#        element = random.choice(self.seq)
#        self.assertTrue(element in self.seq)
#
#    def test_sample(self):
#        with self.assertRaises(ValueError):
#            random.sample(self.seq, 20)
#        for element in random.sample(self.seq, 5):
#            self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest.main()

