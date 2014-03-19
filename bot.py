#!/usr/bin/env python
# encoding: utf-8

import urllib
import urllib2
import cookielib
import json
import getpass
#from docopt import docopt
import logging

logger = logging.getLogger(__name__)

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
    REWARDS = range(1, 8)
    SLOT_MACHINE_REWARDS = {
        "yjzsmzs2" : u"魅子Online神秘鑽石禮包",
        "fnmzs" : u"三國急攻防鑽石禮包",
        "ahzs" : u"重裝武士鑽石禮包",
        "lsjzs" : u"邪王傳鑽石禮包",
        "mtzs" : u"我叫MT鑽石禮包",
	"qjzs" : u"秦姬鑽石禮包",
        "gwlmzs" : u"怪物聯盟鑽石禮包",
        "bmhkzs" : u"彈彈島鑽石禮包",
        "yjzsmhj2" : u"魅子Online神秘黃金禮包",
        "fnmhj" : u"三國急攻防黃金禮包",
	"ahhj" : u"重裝武士黃金禮包",
        "mkhxhj" : u"摩卡幻想黃金禮包",
        "sdxlzs" : u"神雕俠侶鑽石禮包",
        "sdxlhj" : u"神雕俠侶黃金禮包",
        "mkhxzs" : u"魔卡幻想鑽石禮包",
	"lsjhj" : u"亂世決黃金禮包",
        "mthj2" : u"我叫MT黃金禮包",
        "qjhj" : u"秦姬黃金禮包",
        "gwlmhj" : u"怪物聯盟黃金禮包",
        "bmhkhj" : u"彈彈島黃金禮包",
	"anweijiang" : u"沒有中獎哦！請明天再來吧！"
    }

    def __init__(self, log='/tmp/mt-bot.log', debug=False):
        self.opener = None

        #. logger
        format = "%(asctime)s %(levelname)s: %(message)s"
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(filename=log, level=level, format=format)

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
    def slot_machine_pull_url(self):
        """Slot machine trigger URL for http://www.efuntw.com/ipad/"""
        return "%s/lottery_tigerEngineLottery.shtml" % (self.ACTIVITY_URL)

    @property
    def slot_machine_record_url(self):
        """Slot machine record URL for http://www.efuntw.com/ipad/"""
        return "%s/lottery_findTigerEngineLotteryRecord.shtml" % (self.ACTIVITY_URL)

    @property
    def slot_machine_reference_url(self):
        """Slot machine reference URL for http://www.efuntw.com/ipad/"""
        return "http://www.efuntw.com/ipad/ernie_info.html"

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
    def lottery_award_url(self):
        """Singin URL for http://amt.vqw.com/event/mtqd/"""
        return "%s/lottery_drawAwardMT.shtml" % (self.ACTIVITY_URL)

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

    def _stdlog(self, msg):
        """Log & print the message."""
        print msg
        logger.info(msg)

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
        if len(jsonp) > 0:
            json_ = jsonp[ jsonp.index("(")+1 : jsonp.rindex(")") ]
            json_ = json.loads(json_)
        else:
            json_ = None
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
            msg =  "Login fail - %s" % (e)
            self._stdlog(msg)
        logger.debug(self.user_id, self.user_name)

    def _get_servers(self, code):
        data = urllib.urlencode({
            'gameCode' : code
        })
        json_ = bot.jsonp2json(self._open_url(self.game_server_url, data))
        try:
            for i in json_[0]['ServerList']:
                self.servers[code][i.get('ServerCode')] = i.get('ServerName')
        except Exception, e:
            msg =  "Fail to get servers - %s" % (e)
            self._stdlog(msg)

    def get_servers(self):
        """Get server infos """
        for i in self.PLATFORMS:
            self._get_servers(i)
        logger.debug(self.servers)

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
        logger.debug(self.server_code, self.server_name, self.game_code)

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
            msg =  "Fail to get role - %s" % (e)
            self._stdlog(msg)
        logger.debug(self.role_name, self.role_id, self.level, self.month_num, self.month_time)

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
        logger.debug(json_)
        msg =  "%s(%s) %s!!" % (self.user_name, self.role_name, json_[0]['message'])
        self._stdlog(msg)

    def get_reward(self, type_):
        """Get lottery reward."""
        data = urllib.urlencode({
            'userid' : self.user_id,
            'userName' : self.user_name,
            'roleId' : self.role_id,
            'type' : type_,
            'serverCode' : self.server_code,
            'gameCodeFlag' : self.game_code,
            'crossdomain' : True,
        })
        json_ = bot.jsonp2json(self._open_url(
            self.lottery_award_url, data, self.lottery_reference_url))
        logger.debug(json_)
        if json_:
            msg =  "Reward %s - %s" % (type_, json_[0]['message'])
            self._stdlog(msg)

    def get_rewards(self):
        """Get all lottery rewards."""
        for i in self.REWARDS:
            self.get_reward(i)

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
                self.user_name = username
                self.user_id = json_[0]['userid']
                msg =  "%s %s" % (username, json_[0]['message'])
                self._stdlog(msg)
        except Exception, e:
            msg = "Login fail - %s" % (e)
            self._stdlog(msg)
        logger.debug(json_)

    def slot_machine(self):
        """@todo: Docstring for efun_slot_machine.

        :returns: @todo

        """
        data = urllib.urlencode({
            'userid' : self.user_id,
            'userName' : self.user_name,
            'crossdomain' : 'true',
        })
        #. start the machine
        json_ = bot.jsonp2json(self._open_url(
            self.slot_machine_pull_url, data, self.slot_machine_reference_url))
        try:
            msg = "Slot machine start: %s" % json_[0]['message']
            self._stdlog(msg)
        except Exception, e:
            msg =  "Fail to start the slot machine: %s" % (e)
            self._stdlog(msg)
        logger.debug(json_)
        #. get reward
        json_ = bot.jsonp2json(self._open_url(
            self.slot_machine_record_url,
            data,
            self.slot_machine_reference_url))
        try:
            sn = 'serial'
            reward = self.SLOT_MACHINE_REWARDS[json_[0]['reward']]
            if json_[0].has_key(sn):
                msg = "Slot machine reward: %s(%s)" % (json_[0][sn], reward)
                self._stdlog(msg)
            else:
                msg = "Slot machine reward: %s" % (reward)
                self._stdlog(msg)
        except Exception, e:
            msg = json_[0].get('message')
            msg = msg if msg else e
            msg = "Fail to get the slot machine reward: %s" % (msg)
            self._stdlog(msg)
        logger.debug(json_)

if __name__ == '__main__':
    bot = Bot()
    username, password = bot.get_login_info()

    #bot.debug = True
    bot.get_servers()
    bot.select_server_by_code('5401')
    #bot.select_server_by_name(u'雷霆之崖')

    #. sign the main account
    bot.efun_login(username, password)
    bot.slot_machine()
    bot.event_login(username, password)
    bot.get_role()
    bot.lottery_signin()
    bot.get_rewards()

    #. sign the other accounts
    for i in range(1,6):
        bot.efun_login("%s%s" % (username, i), password)
        bot.slot_machine()
        bot.event_login("%s%s" % (username, i), password)
        bot.get_role()
        bot.lottery_signin()
        bot.get_rewards()


