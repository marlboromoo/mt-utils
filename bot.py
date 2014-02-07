#!/usr/bin/env python
# encoding: utf-8

import urllib
import urllib2
import cookielib
import json
import getpass
#from docopt import docopt

class Bot(object):
    """Signin bot for I'm MT (traditional chinese)

       http://amt.vqw.com/event/mtqd/
       http://www.efuntw.com/ipad/store.html

    """

    EVENT_URL = 'http://amt.vqw.com/event/mtqd/'
    EFUN_URL ='http://www.efuntw.com/ipad/'
    LOGIN_URL ='https://login.efun.com/'
    GAME_URL = 'http://game.efun.com/'
    ACTIVITY_URL = 'http://activity.efun.com/'

    PLATFORMS = ['mt', 'mtios']

    def __init__(self):
        self.opener = None
        self.debug = None

        #. account
        self.user_name = None
        self.user_id = None

        #. server
        self.server_name = None
        self.server_code = None
        self.game_code = None
        self.servers = {}
        for i in self.PLATFORMS:
            self.servers[i] = {}

        #. role
        self.role_id = None
        self.role_name = None
        self.level = None
        self.month_num = None
        self.month_time = None

    @property
    def event_login_url(self):
        """Login URL for http://amt.vqw.com/event/mtqd/"""
        return "%s/pcLogin_checkLogin.shtml" % (self.LOGIN_URL)

    @property
    def efun_login_url(self):
        """Login URL for http://www.efuntw.com/ipad/"""
        return "%s/pcLogin_login.shtml" % (self.LOGIN_URL)

    @property
    def game_server_url(self):
        """Servers URL for http://amt.vqw.com/event/mtqd/"""
        return "%s/gameServer_findAllServerByGameCodePC.shtml" % (self.GAME_URL)

    @property
    def role_url(self):
        """Role URL for http://amt.vqw.com/event/mtqd/"""
        return "%s/gameRole_findRole.shtml" % (self.GAME_URL)

    @property
    def lottery_signin_url(self):
        """Singin URL for http://amt.vqw.com/event/mtqd/"""
        return "%s/lottery_registerMT.shtml" % (self.ACTIVITY_URL)

    @property
    def lottery_reference_url(self):
        """Reference URL for http://amt.vqw.com/event/mtqd/"""
        role_name = self.role_name if self.role_name else 'foo'
        data = {
            'userId' : self.user_id,
            'userName' : self.user_name,
            'serverCode' : self.server_code,
            'roldId' : self.role_id,
            'roleName' : urllib.quote(role_name.encode('utf8'))
        }
        if self.month_num == '1':
            data['monthNum'] = self.month_num
            data['monthTime'] = self.month_time
        data = urllib.urlencode(data)
        return "%s/index.html?%s" % (self.EVENT_URL, data)

    def get_csrf_token(self, opener, cookiejar, login_url):
        """
        get csrf token from cookie
        ref: http://stackoverflow.com/questions/3623925/how-do-i-post-to-a-django-1-2-form-using-urllib
        """
        opener.open(login_url)
        try:
            token = [x.value for x in cookiejar if x.name == 'csrftoken'][0]
        except Exception:
            token = None
        return token

    def get_login_info(self):
        """Get username/password from client input.
        :returns: (username, passowrd)
        """
        username = raw_input("Username: ")
        password = getpass.getpass("Password:")
        return (username, password)

    def jsonp2json(self, jsonp):
        """Convert JSONP string to JSON string
        :jsonp: JSONP string
        :returns: JSON string
        """
        json_ = jsonp[ jsonp.index("(")+1 : jsonp.rindex(")") ]
        json_ = json.loads(json_)
        return json_

    def _make_opener(self, ref_url):
        """Create a http client with cookie support.

        :ref_url: Refecence URL
        :returns: urlib2 opener

        """
        cookiejar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        if ref_url:
            opener.addheaders.append(('Referer', ref_url))
        return opener, cookiejar

    def _open_url(self, url, data, ref_url=None):
        """Get content of URL.

        :url: URL
        :data: Paramaters
        :returns: Content(string)

        """
        opener, cookiejar = self._make_opener(ref_url)
        token = self.get_csrf_token(opener, cookiejar, url)
        if token:
            data['csrfmiddlewaretoken'] = token
        return opener.open(url, data).read()

    def event_login(self, username, password):
        """Login http://amt.vqw.com/event/mtqd/

        :username: username
        :password: password

        """
        data = urllib.urlencode({
            'loginName' : username,
            'loginPwd' : password
        })
        json_ = bot.jsonp2json(self._open_url(self.event_login_url, data))
        try:
            if json_[0]['result'] == '1000':
                self.user_id  = json_[0]['userId']
                self.user_name = json_[0]['username']
        except Exception, e:
            print "Login fail - %s" % (e)
        if self.debug:
            print self.user_id, self.user_name

    def _get_servers(self, code):
        data = urllib.urlencode({
            'gameCode' : code
        })
        json_ = bot.jsonp2json(self._open_url(self.game_server_url, data))
        try:
            for i in json_[0]['ServerList']:
                self.servers[code][i.get('ServerCode')] = i.get('ServerName')
        except Exception, e:
            print "Fail to get servers - %s" % (e)

    def get_servers(self):
        """Get server infos """
        for i in self.PLATFORMS:
            self._get_servers(i)
        if self.debug:
            print self.servers

    def _select_server(self, code=None, name=None):
        """Select server by code/name.

        :code: Server code
        :name: Server name

        """
        for p in self.servers:
            for k,v in self.servers.get(p).items():
                if k == code or v == name:
                    self.server_code = k
                    self.server_name = v
                    self.game_code = p
                    break
        if self.debug:
            print self.server_code, self.server_name, self.game_code

    def select_server_by_code(self, code):
        """Select server by code."""
        return self._select_server(code=code)

    def select_server_by_name(self, name):
        """Select server by name."""
        return self._select_server(name=name)

    def get_role(self):
        """Get role infos."""
        data = urllib.urlencode({
            'gameCode' : self.game_code,
            'uid' : self.user_id,
            'serverCode' : self.server_code,
            'crossdomain' : True,
        })
        json_ = bot.jsonp2json(self._open_url(self.role_url, data))
        try:
            json_ = json_[0]['list'][0]
            self.role_name = json_.get('name')
            self.role_id = json_.get('roleid')
            self.level = json_.get('level')
            self.month_num = json_.get('MonthNum')
            self.month_time = json_.get('MonthTime')
        except Exception, e:
            print "Fail to get role - %s" % (e)
        if self.debug:
            print self.role_name, self.role_id, self.level, self.month_num, self.month_time

    def lottery_signin(self):
        """Lottery sign-in."""
        data = urllib.urlencode({
            'userid' : self.user_id,
            'userName' : self.user_name,
            'roleId' : self.role_id,
            'serverCode' : self.server_code,
            'crossdomain' : True,
        })
        json_ = bot.jsonp2json(self._open_url(
            self.lottery_signin_url, data, self.lottery_reference_url))
        if self.debug:
            print json_
        print "%s(%s) %s!!" % (self.user_name, self.role_name, json_[0]['message'])

    def efun_login(self, username, password):
        """Login http://www.efuntw.com/ipad/

        :username: username
        :password: password

        """
        data = urllib.urlencode({
            'loginName' : username,
            'loginPwd' : password,
            'gameCode' : 'platForm',
        })
        json_ = bot.jsonp2json(self._open_url(self.efun_login_url, data))
        try:
            if json_[0]['code'] == '1000':
                print "%s %s" % (username, json_[0]['message'])
        except Exception, e:
            print "Login fail - %s" % (e)
        if self.debug:
            print json_

if __name__ == '__main__':
    bot = Bot()
    username, password = bot.get_login_info()

    bot.get_servers()
    bot.select_server_by_code('5401')
    #bot.select_server_by_name(u'雷霆之崖')

    #. sign the main account
    bot.efun_login(username, password)
    bot.event_login(username, password)
    bot.get_role()
    bot.lottery_signin()

    #. sign the other accounts
    for i in range(1,6):
        bot.efun_login("%s%s" % (username, i), password)
        bot.event_login("%s%s" % (username, i), password)
        bot.get_role()
        bot.lottery_signin()


