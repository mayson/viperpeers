#!/usr/bin/env python
# vim:fileencoding=utf-8

# Find the best reactor
reactorchoices = ["epollreactor", "kqreactor", "cfreactor", "pollreactor", "selectreactor", "posixbase", "default"]
for choice in reactorchoices:
	try:
		exec("from twisted.internet import %s as bestreactor" % choice)
		break
	except:
		pass
bestreactor.install()
#from twisted.application import internet, service
from twisted.internet import reactor
from twisted.protocols import basic, policies

import yaml

import socket
import select
import re
import logging
import sys
import signal
import os
import traceback
import codecs
import time
import resource

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
#logging.getLogger().addHandler()

resource.setrlimit(resource.RLIMIT_NOFILE, [32768,65536])

trace=None
if 'format_exc' in dir(traceback):
        from traceback import format_exc as trace
else:
        from traceback import print_exc as trace

reload(sys)


def lock2key (lock):
		key = {}
		for i in xrange(1, len(lock)):
				key[i] = ord(lock[i]) ^ ord(lock[i-1])
		key[0] = ord(lock[0]) ^ ord(lock[len(lock)-1]) ^ ord(lock[len(lock)-2]) ^ 5
		for i in xrange(0, len(lock)):
				key[i] = ((key[i]<<4) & 240) | ((key[i]>>4) & 15)
		out = ''
		for i in xrange(0, len(lock)):
				out += unichr(key[i])
		out = out.replace(u'\0', u'/%DCN000%/').replace(u'\5', u'/%DCN005%/').replace(u'\44', u'/%DCN036%/')
		out = out.replace(u'\140', u'/%DCN096%/').replace(u'\174', u'/%DCN124%/').replace(u'\176', u'/%DCN126%/')
		return out


def number_to_human_size(size, precision=1):
	"""
	Returns a formatted-for-humans file size.

	``precision``
	The level of precision, defaults to 1

	Examples::

	>>> number_to_human_size(123)
	'123 Bytes'
	>>> number_to_human_size(1234)
	'1.2 KB'
	>>> number_to_human_size(12345)
	'12.1 KB'
	>>> number_to_human_size(1234567)
	'1.2 MB'
	>>> number_to_human_size(1234567890)
	'1.1 GB'
	>>> number_to_human_size(1234567890123)
	'1.1 TB'
	>>> number_to_human_size(1234567, 2)
	'1.18 MB'
	"""
	if size == 1:
		return "1 Byte"
	elif size < 1024:
		return "%d Bytes" % size
	elif size < (1024**2):
		return ("%%.%if KB" % precision) % (size / 1024.00)
	elif size < (1024**3):
		return ("%%.%if MB" % precision) % (size / 1024.00**2)
	elif size < (1024**4):
		 return ("%%.%if GB" % precision) % (size / 1024.00**3)
	elif size < (1024**5):
		return ("%%.%if TB" % precision) % (size / 1024.00**4)


	return ""
	





class DCUser:

	recp={}
	recp['tag']=re.compile('[<](.*)[>]$')
	recp['slots']=re.compile('S:(\d*)')
	recp['hubs']=re.compile('H:([0-9/]*)')
	


	def __init__(self,myinfo="",descr=None,addr=None):
		
		self.nick = ''
		self.connection = ''
		self.flag = ''
		self.mail = ''
		self.share = 0
		self.descr = None
		self.MyINFO = None
		self.level = 0
		self.tag = ''
		self.slots = 0
		self.hubs = 0
		self.sum_hubs = 0	
		if len( myinfo )>0:
			self.upInfo( myinfo )
		self.descr = descr
		self.addr = addr



				

	def upInfo(self,myinfo):
		self.MyINFO = myinfo
		ar = myinfo.split("$")
		ar2 = ar[2].split(" ",2)
		self.nick = ar2[1]
		self.description = ar2[2]
		self.connection = ar[4][0:-1]
		self.flag = ar[4][-1]
		self.mail = ar[5]
		self.share = int( ar[6] )

		# Parsing TAG
		tag = self.recp['tag'].search( self.description )
		if self.tag != None:
			self.tag=tag.group( 1 )
			slots = self.recp['slots'].search( self.tag )
			if slots != None:
				self.slots = int( slots.group( 1 ) )

			hubs = self.recp['hubs'].search( self.tag )
			if hubs != None:
				self.hubs = hubs.group( 1 )
				try:
					self.sum_hubs=self.get_sum_hubs()
				except:
					logging.warning( 'WRONG TAG: %s' % tag )



	def get_ip( self ):
		return self.addr.split(':')[0]

	def get_sum_hubs( self ):
		s=0
		for i in self.hubs.split('/'):
			s=s+int( i )
		return s


class DCHub( policies.ServerFactory ):
	# CONSTANTS
	LOCK='EXTENDEDPROTOCOL_VIPERHUB Pk=versionHidden'
	SUPPORTS='OpPlus NoGetINFO NoHello UserIP UserIP2'
	 
	 
	def _(self,string):  # Translate function
		return self.lang.get(string,string)
	
	def tUCR( self, req ):
		'''translate and make usercmmand request %[line:req:] '''
		return '%%[line:%s:]' % self._( req )


	def UC( self, menu, params ):
		'''make UserCommands'''
		return '$UserCommand 1 2 %s %s %s%s&#124;|' % ( menu, '$<%[mynick]>', self.core_settings['cmdsymbol'], ' '.join( params ) )


	def Gen_UC( self ):
		self.usercommands={}
		# -- CORE USERCOMMANDS --

		self.usercommands['Quit'] = self.UC( self._('Core\\Quit'), ['Quit'] )
		self.usercommands['Save'] = self.UC( self._('Settings\\Save settings'), ['Save'] )
		self.usercommands['SetTopic'] = self.UC( self._('Settings\\Set hub topic'), ['SetTopic', self.tUCR('New Topic')] )
		self.usercommands['Help'] = self.UC( self._('Help'), ['Help'] )
		self.usercommands['RegenMenu'] = self.UC( self._( 'Core\\Regenerate menu' ), ['RegenMenu'] )
		self.usercommands['ReloadSettings'] = self.UC( self._( 'Core\\Reload settings (DANGEROUS)' ), ['ReloadSettings'] )

		# -- settings get/set
		self.usercommands['Get'] = self.UC( self._('Settings\\List settings files'), ['Get'] )

		self.usercommands['Set'] = self.UC( self._('Settings\\Set variable'), ['Set', self.tUCR( 'File' ), self.tUCR( 'Variable' ), self.tUCR( 'New Value' )] )
		 

		# -- Limits control

		self.usercommands['Set'] += self.UC( self._('Settings\\Limits\\Set max users'), ['Set core max_users', self.tUCR( 'New max users' )] )
		self.usercommands['Set'] += self.UC( self._('Settings\\Limits\\Set min share'), ['Set core min_share', self.tUCR( 'New min share (in bytes)' )] )
		self.usercommands['Set'] += self.UC( self._('Settings\\Limits\\Set max hubs'), ['Set core max_hubs', self.tUCR( 'New max hubs' )] )
		self.usercommands['Set'] += self.UC( self._('Settings\\Limits\\Set min slots'), ['Set core min_slots', self.tUCR( 'New min slots' )] )




		# -- User control
		self.usercommands['AddReg'] = ''
		self.usercommands['SetLevel'] = ''


		for i in self.settings['privlist'].keys():
			self.usercommands['AddReg'] += self.UC( self._( 'Users\\Selected\\Register selected nick as\\%s' ) % i, ['AddReg %[nick]', i, self.tUCR( 'Password' )] )


		self.usercommands['AddReg'] += self.UC( self._( 'Users\\Register nick...' ), ['AddReg', self.tUCR( 'nick' ), self.tUCR( 'level' ), self.tUCR( 'Password' )] )

		self.usercommands['ListReg'] = self.UC( self._( 'Users\\List registred nicks' ), ['ListReg'] )

		self.usercommands['DelReg'] = self.UC( self._( 'Users\\Selected\\Unreg selected nick' ), ['DelReg %[nick]'] )
		self.usercommands['DelReg'] += self.UC( self._( 'Users\\Unreg nick...' ), ['DelReg', self.tUCR('Nick')] )

		for i in self.settings['privlist'].keys():
			self.usercommands['SetLevel'] += self.UC( self._( 'Users\\Selected\\Set level for selected nick\\%s' ) % i, ['SetLevel %[nick]', i] )


		self.usercommands['PasswdTo'] = self.UC( self._( 'Users\\Selected\\Set password for selected nick...' ), ['PasswdTo %[nick]', self.tUCR('new password')] )

		self.usercommands['Kick'] = self.UC( self._( 'Kick selected nick...' ), ['Kick %[nick]', self.tUCR( 'reason (may be empty)' )] )

		self.usercommands['UI'] = self.UC( self._( 'Users\\Selected\\User Info' ), ['UI %[nick]'] )




		# -- Plugin control
		
		#self.usercommands['ListPlugins'] = self.UC( self._( 'Plugins\\List aviable plugins' ), ['ListPlugins'] )
		#self.usercommands['ActivePlugins'] = self.UC( self._( 'Plugins\\List active plugins' ), ['ListPlugins'] )

		menu = self._( 'Plugins\\Load/Reload Plugin\\' )
		menuU = self._( 'Plugins\\Unload Plugin\\' )
		loaded = self._( '(loaded)' )

		aplugs = self.get_aviable_plugins()

		self.usercommands['ReloadPlugin'] = ''
		self.usercommands['LoadPlugin'] = ''
		self.usercommands['UnloadPlugin'] = ''
		
		for i in aplugs:
			if i in self.plugs:
				self.usercommands['ReloadPlugin'] += self.UC( menu + i + '  ' + loaded, ['ReloadPlugin', i] )
			else:
				self.usercommands['LoadPlugin'] += self.UC( menu + i, ['LoadPlugin', i] )

		for i in self.plugs.keys():
			self.usercommands['UnloadPlugin'] += self.UC( menuU + i, ['UnloadPlugin', i] )




		#self.usercommands['ListPlugins']='$UserCommand 1 2 '+self._('Plugins\\List aviable plugins')+'$<%[mynick]> '+self.core_settings['cmdsymbol']+'ListPlugins&#124;|'
		#self.usercommands['ActivePlugins']='$UserCommand 1 2 '+self._('Plugins\\List active plugins')+'$<%[mynick]> '+self.core_settings['cmdsymbol']+'ActivePlugins&#124;|'
		#self.usercommands['LoadPlugin']='$UserCommand 1 2 '+self._('Plugins\\Load plugin..')+'$<%[mynick]> '+self.core_settings['cmdsymbol']+'LoadPlugin %[line:'+self._('plugin')+':]&#124;|'
		#self.usercommands['UnloadPlugin']='$UserCommand 1 2 '+self._('Plugins\\Unload plugin...')+'$<%[mynick]> '+self.core_settings['cmdsymbol']+'UnloadPlugin %[line:'+self._('plugin')+':]&#124;|'
		#self.usercommands['ReloadPlugin']='$UserCommand 1 2 '+self._('Plugins\\Reload plugin...')+'$<%[mynick]> '+self.core_settings['cmdsymbol']+'ReloadPlugin %[line:'+self._('plugin')+':]&#124;|'
	   
		# -- Self control
		self.usercommands['Passwd'] = self.UC( self._('Me\\Set MY password...'), [ 'Passwd', self.tUCR( 'new password' ) ] )

		for i in self.plugs.values():
			i.update_menu()
			self.usercommands.update( i.usercommands )




		#logging.debug ('UC: %s' % repr(self.usercommands) )
		
		return




	def __init__( self ):

		# COMMANDS
		self.commands={}
		# SIGNAL-SLOT EVENT SUBSYSTEM
		self.slots={}
	   

		# COMPILE REGEXPS
		self.recp={}
		#self.recp['Key']=re.compile('(?<=\$Key )[^|]*(?=[|])')
		#self.recp['ValidateNick']=re.compile('(?<=\$ValidateNick )[^|]*(?=[|])')
		#self.recp['Supports']=re.compile('(?<=\$Supports )[^|]*(?=[|])')
		#self.recp['MyPass']=re.compile('(?<=\$MyPass )[^|]*(?=[|])')
		#self.recp['MyINFO']=re.compile('\$MyINFO [^|]*(?=[|])')

		#self.recp['NoGetINFO']=re.compile('NoGetINFO')
		#self.recp['NoHello']=re.compile('NoHello')

		self.recp['.yaml']=re.compile('\.yaml$')
		self.recp['before.yaml']=re.compile('.*(?=\.yaml)')
		self.recp['.py']=re.compile('\.py$')
		self.recp['before.py']=re.compile('.*(?=\.py)')
		self.recp['tag']=re.compile('[<](.*)[>]$')
	   

		# SET PATHS
		self.path_to_settings="./settings/"
		self.path_to_plugins="./plugins/"


		# ----- SETTINGS -----
		self.settings={}

		# LOADING SETTINGS
		self.load_settings()


		# SHORTCUTS
		self.core_settings=self.settings.get('core',{})
		self.reglist=self.settings.get('reglist',{})
		self.privlist=self.settings.get('privlist',{})

		# DEFAULTS
		defcore_settings={}
		defcore_settings['port']=[411]
		defcore_settings['hubname']='ViperPeers'
		defcore_settings['topic']=''
		defcore_settings['cmdsymbol']='!'
		defcore_settings['OpLevels']=['owner']
		defcore_settings['Protected']=['owner', 'op']
		defcore_settings['Lang']='ru.cp1251'
		defcore_settings['autoload']=[
			'ban', 'chatlist', 'chatroom', 'forbid', 'goodplug',
			'iplog', 'massmsg', 'motd', 'mute', 'say', 'regme'
		]
		defcore_settings['logfile']=''
		defcore_settings['loglevel']=10
		defcore_settings['autosave']=120
		defcore_settings['userip']=['owner', 'op']

		# ---- LIMITS ----

		defcore_settings['max_users'] = 10000
		defcore_settings['min_share'] = 0
		defcore_settings['max_hubs'] = 1000
		defcore_settings['min_slots'] = 0
		defcore_settings['pass_limits'] = ['owner', 'op', 'chatroom']



		defcore_settings['hubinfo']={'address':'127.0.0.1','description':'ViperPeers powered hub (vipehive fork)','type':'ViperPeers Hub', 'hubowner':'owner'}

		defreglist={'admin':{'level':'owner', 'passwd':'megapass'}}


		defprivlist={'owner':['*']}

		
	


		# If loaded core_settings miss some stuff - load defaults
		if len(self.core_settings)==0:
				self.settings['core']=self.core_settings={}

		for i in defcore_settings.keys():
			if not i in self.core_settings:
				self.core_settings[i]=defcore_settings[i]


		#------UPDATE SETTINGS FROM OLD VERSION:-------

		# UPDATE PORT SETTINGS FOR VERSIONS <= svn r168
		if not isinstance( self.core_settings['port'], list ):
			self.core_settings['port'] = [ self.core_settings['port'] ]

		if len(self.reglist)==0:
				self.settings['reglist']=self.reglist=defreglist
	   
		if len(self.privlist)==0:
				self.settings['privlist']=self.privlist=defprivlist

		# MORE SHORTCUTS
		self.oplevels=self.core_settings['OpLevels']
		self.protected=self.core_settings['Protected']
		self.KEY=lock2key(self.LOCK)

		# ---- TRANSPORTS ----
		self.transports=[]

		# User hashes
		self.nicks={}
		self.addrs={}

		# Support for very, VERY old clients
		self.hello=[]
		self.getinfo=[]
	   
		self.clthreads=[]

	   
		# Reinitialize Logging
		self.reload_logging()
	    

		# REGISTERING CORE COMMANDS
		self.commands['Quit']=self.Quit #Usercommands +
		self.commands['AddReg']=self.AddReg #Usercommands +
		self.commands['DelReg']=self.DelReg  #Usercommands +
		self.commands['ListReg']=self.ListReg #Usercommands +
		self.commands['Get']=self.Get #Usercommands +
		self.commands['Set']=self.Set #Usercommands +
		self.commands['SetLevel']=self.SetLevel #Usercommands +
		self.commands['Help']=self.Help #Usercommands +
		self.commands['ListPlugins']=self.ListPlugins #Usercommands +
		self.commands['LoadPlugin']=self.LoadPlugin #Usercommands +
		self.commands['UnloadPlugin']=self.UnloadPlugin #Usercommands +
		self.commands['ActivePlugins']=self.ActivePlugins #Usercommands +
		self.commands['Save']=self.Save #Usercommands +
		self.commands['ReloadPlugin']=self.ReloadPlugin
		self.commands['RP']=self.ReloadPlugin #Usercommands +
		self.commands['Passwd']=self.Passwd
		self.commands['PasswdTo']=self.PasswdTo #Usercommands +
		self.commands['Kick']=self.Kick #Usercommands +
		self.commands['UI']=self.UI #Usercoommands +
		self.commands['SetTopic']=self.SetTopic #Usercommands +
		self.commands['RegenMenu'] = self.RegenMenu #Usercommands +
		self.commands['ReloadSettings'] = self.ReloadSettings #Usercommands +


		# TRANSLATION SYSTEM
		self.lang={}              # Current language array
		self.help={}              # Help for current language

		# -- LOADING LANGUAGE

		lang=self.core_settings['Lang'].split('.')[0]
		self.charset=cpage=self.core_settings['Lang'].split('.')[1]


		try:
			lpath='./languages/'+lang+'/'
			lfiles=os.listdir(lpath)
			for i in lfiles:
				# LOAD MESSAGES FOR CURRENT LANGUAGE
				if self.recp['.yaml'].search(i)!=None:
					try:
						arr=yaml.load(codecs.open(lpath+i,'r','utf-8').read())
					   
						#for key,value in arr.iteritems():
						#       arr[key]=value.encode(cpage)

						self.lang.update(arr)
					except:
						logging.error('file %s in wrong format: %s' % ((lpath+i), trace()))
			if 'help' in lfiles:                                
			   # LOAD HELP FOR CURRENT LANGUAGE
			   hpath=lpath+'help/'
			   hfiles=os.listdir(hpath)
			   for i in hfiles:
					if self.recp['.yaml'].search(i)!=None:
						try:
							arr=yaml.load(codecs.open(hpath+i,'r','utf-8').read())
						   
							#for key,value in arr.iteritems():
							#        arr[key]=value.encode(cpage)

							self.help.update(arr)
						except:
							logging.error('file %s in wrong format: %s' % ((lpath+i), trace()))
		except:
			logging.error('language directory not found %s' % (trace()))

	   
		logging.info('Language loaded: %s strings' % str(len(self.lang)))
		logging.info('Help loaded: %s strings' % str(len(self.help)))


		# PLUGINS
		self.plugs={}

		self.Gen_UC()

		# Queue for queue_worker
		self.queue = []
		self.queue_lock = False
		self.delay = 0.5
		self.ping_time = 150.
		reactor.callLater(self.delay, self.queue_worker, self.ping_time)

		# AUTOLOAD PLUGINS
		for i in self.settings['core']['autoload']:
			reactor.callLater(self.delay, self.LoadPlugin, None, [i])

		# SETTING AUTOSAVER
		reactor.callLater(self.settings['core']['autosave'], self.settings_autosaver)

		logging.info ('Hub ready to start on port %s...' % self.core_settings['port'])

		self.skipme=[]


	def reload_logging(self):
		logging.debug('Set logging to %s, level %s' % (self.settings['core']['logfile'], str(self.settings['core']['loglevel'])))
		reload(sys.modules['logging'])
		if self.settings['core']['logfile']:
			logging.basicConfig(filename=self.settings['core']['logfile'],)
		logging.getLogger().setLevel(self.settings['core']['loglevel'])

	def emit(self,signal,*args):
		#logging.debug('emitting %s' % signal)
		#logging.debug('emit map %s' % repr(self.slots))
		for slot in self.slots.get(signal,[]):
			logging.debug( 'Emitting: %s, for  %s slot' % ( signal, repr( slot )) )
			try:
				if not slot(*args):
					logging.debug( 'Emit %s: FALSE' % signal )
					return False
			except:
				logging.error('PLUGIN ERROR: %s' % trace())
		logging.debug( 'Emit %s: True' % signal )
		return True

	def settings_autosaver(self):
		logging.debug('settings autosave')
		self.save_settings()
		reactor.callLater(self.settings['core']['autosave'], self.settings_autosaver)

	def drop_user_by_addr(self,addr):
		if addr in self.addrs:
			transport=self.addrs[addr].descr
			nick=self.addrs[addr].nick
			self.drop_user(addr,nick,transport)

	def drop_user(self, addr, nick, transport):
		logging.debug('dropping %s %s' % (addr, nick))
		try:
			if transport in self.transports:
				self.transports.remove(transport)
			self.addrs.pop(addr,'')
			self.nicks.pop(nick,'')
			if transport in self.hello:
				self.hello.remove(transport)
			transport.loseConnection()
		except:
				logging.debug('something wrong while dropping client %s' % trace())
		self.send_to_all('$Quit %s|' % nick)
		self.emit('onUserLeft',addr,nick)

	def drop_user_by_nick(self,nick):
		if nick in self.nicks:
			transport=self.nicks[nick].descr
			addr=self.nicks[nick].addr
			self.drop_user(addr,nick,transport)

	def drop_user_by_transport(self, transport):
		A=None
		N=None

		for nick, user in self.nicks.items():
			if user.descr == transport:
				N=nick
				break

		for addr, user in self.addrs.items():
			if user.descr == transport:
				A=addr
				break

		self.drop_user(A, N, transport)

	def send_to_all(self, msg):
		if not self.queue_lock:
			self.queue_lock = True
			self.queue.append(msg)
			self.queue_lock = False
		else:
			reactor.callLater(self.delay, self.send_to_all, msg)

	def queue_worker(self, ping_timer):
		if ping_timer > 0:
			ping_timer -= self.delay
		result = ''
		if not self.queue_lock:
			self.queue_lock = True
			msgs = self.queue
			self.queue = []
			self.queue_lock = False
			if len(msgs)>0:
				for msg in msgs:
					logging.debug('sending to all %s' % msg)
					if not (len(msg)>0 and msg[-1]=="|"):
						msg += "|"
					result += msg
		if not result and ping_timer <= 0:
			# We should probably "ping" all connections if no messages to send 
			ping_timer += self.ping_time
			logging.debug('pinging')
			result = '|'
		if result:
			logging.debug('senging "%s" to all' % result)
			for transport in self.transports:
				try:
					transport.write(result.encode(self.charset))
				except:
					logging.debug('transport layer error %s' % trace())
					reactor.callLater(0, self.drop_user_by_transport, transport)
		reactor.callLater(self.delay, self.queue_worker, ping_timer)

	def send_pm_to_nick(self,fnick,nick,msg):
		self.send_to_nick(nick,'$To: %s From: %s $<%s> %s|' % (nick, fnick, fnick, msg))

	def send_to_nick(self,nick,msg):
		if nick in self.nicks:
			if not (len(msg)>0 and msg[-1]=="|"):
					msg=msg+"|"
			try:
				logging.debug('sending "%s" to %s' % (msg, nick))
				self.nicks[nick].descr.write(msg.encode(self.charset))
			except:
				#logging.debug('Error while sending "%s" to %s. Dropping. %s' % (msg,nick,trace()))
				logging.debug('socket error %s. dropping lost user!' % trace() )
				self.drop_user_by_nick(nick)
		else:
			logging.debug('send to unknown nick: %s' % nick)

	def send_to_addr(self,addr,msg):
		if addr in self.addrs:
			if not (len(msg)>0 and msg[-1]=="|"):
				msg=msg+"|"
			try:
				logging.debug('sending "%s" to %s' % (msg, addr))
				self.addrs[addr].descr.write(msg.encode(self.charset))
			except:
				logging.debug('socket error %s' % trace())
		else:
			logging.warning('uknown addres: %s' % addr)


	def get_nick_list( self ):
		nicklist="$NickList "
		oplist="$OpList "
		for user in self.nicks.values():
			nicklist+=user.nick+"$$"
			if user.level in self.oplevels:
				oplist+=user.nick+"$$"
		
		return "%s|%s|" % (nicklist[:-2], oplist[:-2])
	def get_op_list(self):
		#repeat some code for faster access
		oplist="$OpList "
		for user in self.nicks.values():
			if user.level in self.oplevels:
				oplist+=user.nick+"$$"
		return oplist+'|'

	def get_userip_list( self ):
		uip='$UserIP '
		for user in self.nicks.values():
			uip+='%s %s$$' % (user.nick, user.get_ip())
		return uip+'|'
	def get_userip_acc_list(self):
		uip=[]
		for user in self.nicks.values():
			if user.level in self.core_settings['userip']:
				uip.append(user.nick)
		return uip

	def save_settings(self):
		logging.debug('saving settigs')
		try:
			for mod, sett in self.settings.items():
				try:
					logging.info('saving settings for %s' % mod)
					f=open(self.path_to_settings+'/'+mod+'.yaml','wb')
					f.write(yaml.safe_dump(sett,default_flow_style=False,allow_unicode=True))
				except:
					logging.error('failed to load settings for module %s. cause:' % mod)
					logging.error('%s' %  trace())
					return False

		except:
			logging.error('!!! SETTINGS NOT SAVED !!!')
			return False
		return True

	def load_settings(self):
		logging.debug('reading settigs')
		try:
			for i in os.listdir(self.path_to_settings):
				if self.recp['.yaml'].search(i)!=None:
					mod=self.recp['before.yaml'].search(i).group(0)
					logging.debug('loading settings for %s' % mod)
					try:
						f=codecs.open(self.path_to_settings+'/'+ i,'r','utf-8')
						text=f.read()
						dct=yaml.load(text)
						if dct!=None:
								self.settings[mod]=dct
					except:
						logging.error('failed to load settings for module %s. cause:' % mod)
						logging.error('%s' %  trace())
		except:
			logging.error('error while loading settings: %s', trace())

	def check_rights(self, user, command):
		rights=self.privlist.get(user.level,[])
		if ('*' in rights) or (command in rights):
			return True
		else:
			return False

	def send_usercommands_to_nick(self, nick):
		for i in range(1,4):
			self.send_to_nick(nick, '$UserCommand 255 %s |' % i)
		for name, cmd in self.usercommands.items():
			if self.check_rights(self.nicks[nick],name):
				self.send_to_nick(nick, cmd)

	def send_usercommands_to_all(self):
		for nick in self.nicks.keys():
			self.send_usercommands_to_nick(nick)

	# COMMANDS
		
		#  -- Hub Control

	def Quit(self,addr,params=[]):
		self.work=False
		exit
		return True
		
	def Set(self,addr,params=[]): # Setting param for core or plugin
		# Params should be: 'core/plugin name' 'parameter' 'value'
		# Cause 'value' can contain spaces - join params[2:]
		if len(params)<2:
			return self._('Params error')
		try:
			value=yaml.load(" ".join(params[2:]))
			self.settings[params[0]][params[1]]=value
			if params[1].startswith('log'):
				self.reload_logging()
			return self._('Settings for %s - %s setted for %s') % (params[0], params[1], value)
		except:
			return self._('Error: %s') % trace()
	
	def Get(self,addr, params=[]): #Getting params or list
		# Params can be 'core/plugin name' 'parameter' or 'core/plugin name'
		if len(params)==0:
			return self._(' -- Available settings --:\n%s' ) % (unicode(yaml.safe_dump(self.settings.keys(),allow_unicode=True),'utf-8'))

		elif len(params)==1:
			if params[0] in self.settings:
				return self._(' -- Settings for %s --\n%s' ) % (params[0], unicode(yaml.safe_dump(self.settings.get(params[0],''),allow_unicode=True),'utf-8'))
			elif len(params)==2:
				if params[0] in self.settings and params[1] in self.settings[params[0]]:
					return self._(' -- Settings for %s - %s --\n%s' ) % ( params[0], params[1], unicode(yaml.safe_dump(self.settings[params[0]][params[1]],allow_unicode=True),'utf-8'))
				else:
					return self._('Params error')
			else:
				return self._('Params error')

	def Save(self, params=[]):
		try:
			self.save_settings()
			return True
		except:
			return False

		
	def RegenMenu( self, params = [] ):
		try:
			self.Gen_UC()
			self.send_usercommands_to_all()
			return True
		except:
			return False

	def ReloadSettings( self, params = [] ):
		try:
			self.load_settings()
		except:
			return False
		return True

	# --- User Control
	def AddReg(self,addr,params=[]):
		# Params should be: 'nick' 'level' 'passwd'
		if len(params)==3:
			# Check if 'nick' already registred
			if params[0] not in self.reglist:
				self.reglist[params[0]]={'level': params[1],'passwd':params[2]}
				return self._('User Registred:\n nick: %s\n level: %s\n passwd:%s') % (params[0],params[1],params[2])
			else:
				return self._('User already registred')
		else:
			return self._('Params error.')

	def DelReg(self,addr,params=[]):
		# Params should be 'nick'
		if len(params)==1:
			# Check if 'nick' registred
			if params[0] in self.reglist:
				if params[0] not in self.protected:
					del self.reglist[params[0]]
					return self._('User deleted')
				else:
					return self._('User protected!')

			else:
				return self._('User not registred')
		else:
			return self._('Params error')

	def ListReg(self,addr):
		s=self._('--- REGISTRED USERES --- \n')
		for nick, param in self.reglist.items():
			s=s+('nick: %s level: %s' % (nick, param['level'],))+'\n'
		return s
		#return self._('--- REGISTRED USERES --- \n') + "\n".join('nick: %s level: %s' % (nick, param['level'],) for nick, param in self.reglist.iteritems())

	def SetLevel(self,addr,params=[]):
		# Params should be: 'nick' 'level'
		if len(params)==2:
			if params[0] in self.reglist:
				self.reglist[params[0]]['level']=yaml.load(params[1])
				return self._('Success')
			else:
				return self._('No such user')
		else:
			return self._('Params error.')

	def Kick (self, addr, params=[]):
		# Params should be: 'nick'
		if len(params)>=1:
			if params[0] in self.nicks:
				if self.nicks[params[0]].level in self.protected:
					return self._('User protected!')
				msg = '<%s> is kicking %s because: ' % (self.addrs[addr].nick, params[0])
				if len(params)>1:
					fnick = self.core_settings['hubname'].replace(' ','_')
					reason = ' '.join(params[1:])
					self.send_pm_to_nick(fnick, params[0], reason)
					msg += reason
				else:
					msg += '-'
				self.drop_user_by_nick(params[0])
				self.send_to_all(msg)
				return self._('Success')
			else:
				return self._('No such user')
		else:
			return self._('Usage: !Kick <Username> [<reason>]')

	# -- Help System

	def Help(self,addr,params=""):
		# Params can be empty or 'command'
		if len(params)==1:
			if self.check_rights(self.addrs[addr], params[0]):
				return self.help[params[0]]
			else:
				return self._('Premission denied')
				
		elif len(params)==0:
			ans=self._(' -- Aviable commands for you--\n')
			for cmd in self.commands.keys():
				if self.check_rights(self.addrs[addr],cmd):
					ans+='%s\n' % self.help.get(cmd,cmd)
			return ans
		else:
			return self._('Params error')

	# -- Plugin control

	def get_aviable_plugins( self ):
		ans = []
		try:
			for i in os.listdir(self.path_to_plugins):
				if self.recp['.py'].search(i)!=None and i!="__init__.py" and i!="plugin.py":
					mod=self.recp['before.py'].search(i).group(0)
					ans.append( mod )
			return ans
		except:
			logging.error('error while listing plugins: %s', trace())
		return ans

	def ListPlugins(self,addr):
		logging.debug('listing plugins')
		ans = self._(' -- Aviable plugins --\n%s') % '\n'.join( self.get_aviable_plugins() )
		return ans

	def LoadPlugin(self,addr,params=[]):
		# Params should be: 'plugin'
		if len(params)==1:
			logging.debug('loading plugin %s' % params[0])
			if params[0] not in self.plugs:
				try:
					if not '.' in sys.path:
						sys.path.append('.')
					if 'plugins.'+params[0] not in sys.modules:
						plugins=__import__('plugins.'+params[0])
						plugin=getattr(plugins,params[0])
					else:
						plugin=reload(sys.modules['plugins.'+params[0]])
					logging.getLogger().setLevel(self.settings['core']['loglevel'])
					logging.debug('loaded plugin file success')
					cls=getattr(plugin,params[0]+'_plugin')
					obj=cls(self)
					self.plugs[params[0]]=obj
					self.commands.update(obj.commands)
					#self.usercommands.update(obj.usercommands)
					logging.debug( 'Plugin %s slots: %s' % (params[0], repr( obj.slots ) ) )
					for key,value in obj.slots.iteritems():
						logging.debug( 'Activating Slot: %s, on plugin %s' % ( key, params[0] ) )


						if key in self.slots:
							self.slots[key].append(value)
							
						else:
							self.slots[key]=[value]
					logging.debug( 'MessageMap: %s' % repr( self.slots ))

					self.Gen_UC()
					self.send_usercommands_to_all()
					return self._('Success')
				except:
					e=trace()
					logging.debug( 'Plugin load error: %s' % (e,) )
					return self._( 'Plugin load error: %s' % (e,) )
			else:
				return self._('Plugin already loaded')
		else:
			return self._('Params error')

	def UnloadPlugin(self,addr,params=[]):
			# Params should be: 'plugin'
			logging.debug('unloading plugin')
			if len(params)==1:
				try:
					if params[0] in self.plugs:
						plug=self.plugs.pop(params[0])
						plug.unload()
						for key in plug.commands.keys():
							self.commands.pop(key,None)
						for key in plug.usercommands.keys():
							self.usercommands.pop(key,None)
						for key, value in plug.slots.iteritems():
							if key in self.slots:
								if value in self.slots[key]:
									self.slots[key].remove(value)
						self.Gen_UC()
						self.send_usercommands_to_all()
						return self._('Success')
					else:
						return self._('Plugin not loaded')
				except:
					return self._('Plugin unload error: %s' % trace())
			else:
				return self._('Params error')

	def ReloadPlugin(self, addr, params=[]):
		# Params 'plugin'
		return 'Unload: %s, Load %s' % (self.UnloadPlugin(addr, params), self.LoadPlugin(addr, params))
			
	def ActivePlugins(self,addr,params=[]):
		return self._(' -- ACTIVE PLUGINS -- \n')+"\n".join(self.plugs.keys())

	def Passwd(self,addr,params=[]):
		# Params 'nick'
		if len(params)>0:
			newpass=" ".join(params)
			nick=self.addrs[addr].nick
			if nick in self.reglist:
				self.reglist[nick]['passwd']=newpass
				return self._('Your password updated')
			else:
				return self._('You are not registred')
		else:
			return self._('Params error')

	def PasswdTo(self,addr,params=[]):
		# Params: 'nick' 'newpass'
		if len(params)>1:
			nick=params[0]
			newpass=" ".join(params[1:])
			if nick in self.reglist:
				if self.nicks[nick].level in self.protected:
						return self._('User protected!')
				self.reglist[nick]['passwd']=newpass
				return self._('User password updated')
			else:
					return self._('User not registred')

		else:
				return self._('Params error')
	
	def UI(self,addr,params=[]):
		# params: 'nick'

		if len(params)==1:
			user=self.nicks.get(params[0],None)
			if user!=None:
				return self._(' -- USER %s INFO --\n addres: %s\n level: %s\n is op?: %s\n is protected?: %s') % (user.nick, user.addr, user.level, repr(user.level in self.oplevels), repr(user.level in self.protected))
			else:
				return self._('No such user')
		else:
				return self._('Params error')

	def SetTopic(self,addr,params=[]):
		#params: ['topic']
		if len(params)>=1:
			topic=' '.join(params)
			self.core_settings['topic']=topic
			self.send_to_all('$HubTopic %s|' % topic)
			return self._('Success')
		else:
			return self._('Params error')

	# -- EXTENDED FUNCTIONS USED FOR SIMPLIFY SOME WRK

	def masksyms(self, str):
		''' return string with ASCII 0, 5, 36, 96, 124, 126 masked with: &# ;. e.g. chr(5) -> &#5; '''
		cds=[0, 5, 36, 96, 124, 126]
		for i in cds:
			str=str.replace(chr(i),'&#%s;' % i)

		return str

	def unmasksyms(self, str):
		''' return string with ASCII 0, 5, 36, 96, 124, 126 unmasked from: &# ; mask. e.g. &#5; -> chr(5) '''
		cds=[0, 5, 36, 96, 124, 126]
		for i in cds:
			str=str.replace('&#%s;' % i, chr(i))

		return str


class DCProtocol(basic.LineOnlyReceiver, policies.TimeoutMixin):
	def _(self,string):  # Translate function
		return self.factory._(string)

	def __init__(self):
		self.delimiter = '|'
		self.MAX_LENGTH = 2**16 # default is 16384

	def write(self, msg):
		self.transport.write(msg)
		logging.debug('sending "%s" to %s' % (msg, self._addr))

	def connectionMade(self):
		self._state = 'connect'
		self._supports = []
		self._hubinfo = self.factory.core_settings['hubinfo']
		self._host, self._port = self.transport.socket.getpeername()
		self._addr = '%s:%s' % (self._host, self._port)
		self._nick = ''
		self.setTimeout(None)
		if len( self.factory.nicks ) >= self.factory.core_settings['max_users']:
			self.transport.loseConnection()
			logging.warning( 'MAX USERS REACHED!!!' )
			return
		logging.debug ('connecting: %s' % self._addr)
		if self.factory.emit('onConnecting', self._addr):
			self.write('$Lock %s|' % self.factory.LOCK )
		else:
			logging.debug('Connection is not allowed by plugins')
			self.transport.loseConnection

	def lineReceived(self, line):
		line = unicode(line, self.factory.charset)
		logging.debug ('received: %s from %s' % (line, self._addr))
		if self._state in [ 'connect', 'validate', 'negotiate' ] and line.startswith('$'):
			self.resetTimeout()
			f = getattr(self, 'parse_' + self._state + '_cmd')
			f(line)
		elif self._state == 'logedin':
			self.resetTimeout()
			if self.factory.emit('onReceivedSomething', self._addr) and len(line) > 0:
				if line.startswith('$'):
					self.parse_protocol_cmd(line)
				else:
					self.parse_chat_msg(line)
		else:
			logging.debug ( 'Unexpected command sequence received from %s' % self._addr )
			self.transport.loseConnection()

	def lineLengthExceeded(self, line):
		logging.warning ( 'Too big or wrong message received from %s: %s' % (self._addr, s) )

	def connectionLost(self, reason):
		if self._nick:
			self.factory.drop_user(self._addr, self._nick, self.transport)
		logging.debug('User Lost: %s' % reason) 

	def parse_protocol_cmd(self, cmd):
		acmd=cmd.split(' ')
		if acmd[0]=='$GetINFO':
			if len(acmd)==3:
				if self.factory.addrs[self._addr].nick==acmd[2] and self.factory.nicks.has_key(acmd[1]):
					if self.factory.emit('onGetINFO',acmd[1],acmd[2]):
						logging.debug('send myinfo %s' % self.factory.nicks[acmd[1]].MyINFO)
						self.factory.send_to_nick(acmd[2],self.factory.nicks[acmd[1]].MyINFO)
		elif acmd[0]=='$MyINFO':
			if len(acmd)>=3:
				if self.factory.addrs[self._addr].nick==acmd[2]:
					try:
						self.factory.nicks[acmd[2]].upInfo(cmd)
						if self.factory.emit('onMyINFO',cmd):
							self.factory.send_to_all(cmd)
					except:
						logging.warning( 'Wrong MyINFO by: %s with addr %s: %s' % ( acmd[2], self._addr, trace() ) )
						self.factory.drop_user_by_addr(self._addr)
		elif acmd[0]=='$To:':
			if len(acmd)>5:
				if acmd[3]==self.factory.addrs[self._addr].nick==acmd[4][2:-1]:
					if acmd[1] in self.factory.nicks:
						tocmd=cmd.split(' ',5)
						if self.factory.emit('onPrivMsg',acmd[3],acmd[1],tocmd[5]):
							self.factory.send_to_nick(acmd[1],cmd+"|")
		elif acmd[0]=='$ConnectToMe':
			if len(acmd)==3:
				if acmd[2].split(':')[0]==self._addr.split(':')[0]:
					if self.factory.emit('onConnectToMe',self._addr,acmd[1]):
						self.factory.send_to_nick(acmd[1],cmd+"|")
		elif acmd[0]=='$RevConnectToMe':
			if len(acmd)==3:
				if acmd[1] in self.factory.nicks:
					if self.factory.addrs[self._addr].nick==acmd[1]:
						if self.factory.emit('onRevConnectToMe',acmd[1],acmd[2]):
							self.factory.send_to_nick(acmd[2],cmd+"|")
		elif acmd[0]=='$Search':
			if len(acmd)>=3:
				srcport=acmd[1].split(':')
				if len(srcport)==2:
					if srcport[0]=='Hub':
						#Passive Search
						if srcport[1]==self.factory.addrs[self._addr].nick:
							bcmd=cmd.split(' ',2)
							if self.factory.emit('onSearchHub',bcmd[1],bcmd[2]):
								self.factory.send_to_all(cmd)

					else:
						#Active Search
						if srcport[0]==self.factory.addrs[self._addr].addr.split(':')[0]:
							bcmd=cmd.split(' ',2)
							if self.factory.emit('onSearch',bcmd[1],bcmd[2]):
								self.factory.send_to_all(cmd)
		elif acmd[0]=='$SR':
			fcmd=cmd.split(chr(5))
			if len(fcmd)==4 and len(acmd)>=3:
				sender=acmd[1]
				receiver=fcmd[3]
				if self.factory.addrs[self._addr].nick==sender:
					if self.factory.emit('onSearchResult', sender, receiver, cmd):
						self.factory.send_to_nick(receiver, chr(5).join(fcmd[:3])+'|')
		elif acmd[0]=='$GetNickList':
			self.factory.send_to_addr( self._addr, self.factory.get_nick_list() )
		elif acmd[0]=='$HubINFO' or acmd[0]=='$BotINFO':
			hubinfo='$HubINFO '
			hubinfo+='%s$' % self.factory.core_settings['hubname']
			hubinfo+='%s:%s$' % ( self._hubinfo.get('address',''), self.factory.core_settings['port'][0] )
			hubinfo+='%s$' % self._hubinfo.get('description','')
			hubinfo+='%s$' % self.factory.core_settings.get('max_users','10000')
			hubinfo+='%s$' % self.factory.core_settings.get('min_share','0') 
			hubinfo+='%s$' % self.factory.core_settings.get('min_slots','0')
			hubinfo+='%s$' % self.factory.core_settings.get('max_hubs','1000')
			hubinfo+='%s$' % self._hubinfo.get('type','')
			hubinfo+='%s$' % self._hubinfo.get('owner','')
			self.factory.send_to_addr( self._addr, hubinfo )
		else:
			logging.debug('Unknown protocol command: %s from: %s' % (cmd, self._addr))
		return

	def parse_cmd(self, cmd):
		logging.debug('command received %s' % cmd)
		acmd=cmd.split(' ')
		ncmd=acmd[0]
		for j in self.factory.commands:
			if acmd[0].lower() == j.lower():
				ncmd=j
		if self.factory.check_rights(self.factory.addrs[self._addr],acmd[0]):
			if ncmd in self.factory.commands:
				try:
					if (len(acmd[1:]))>0:
						result=self.factory.commands[ncmd](self._addr,acmd[1:])
					else:
						result=self.factory.commands[ncmd](self._addr)
					if result != '':
						self.factory.send_to_addr(self._addr, self._('<HUB> %s|') % result)
				except SystemExit:
					raise SystemExit

				except:
					self.factory.send_to_addr(self._addr, self._('<HUB> Error while proccessing command %s|') % trace())
			else:
				self.factory.send_to_addr(self._addr, self._('<HUB> No such command'))
		else:
			self.factory.send_to_addr(self._addr, self._('<HUB> Premission denied'))
		return

	def parse_chat_msg(self, msg):
		acmd=msg.split(' ',1)
		if len(acmd)==2:
			if acmd[0][1:-1]==self.factory.addrs[self._addr].nick:
				if acmd[1][0]==self.factory.core_settings['cmdsymbol']:
					self.parse_cmd(acmd[1][1:])
				else:
					if self.factory.emit('onMainChatMsg',acmd[0][1:-1],acmd[1]):
						self.factory.emit('ChatHistEvent',acmd[0][1:-1],acmd[1])
						self.factory.send_to_all(msg)
			else:
				logging.warning('user tried to use wrong nick in MC. Real nick: %s. Message: %s' % (self.factory.addrs[self._addr].nick, msg))
				self.drop_user_by_addr(self._addr)
		return

	def parse_connect_cmd(self, cmd):
		acmd = cmd.split(' ', 1)
		if acmd[0] == '$Supports':
			self._supports = acmd[1].split(' ')
			logging.debug('Supports: %s' % acmd[1])
		elif acmd[0] == '$ValidateNick':
			self.write('<HUB> This hub is powered by ViperPeers specific software.|$HubName %s|' % (
				self.factory.core_settings['hubname'].encode(self.factory.charset) ) )
			self._nick = acmd[1]
			if self._nick:
				logging.debug('validating: %s' % self._nick)
				if self._nick in self.factory.reglist:
					self._state = 'validate'
					self.write('$GetPass|')
					return
				elif self._nick not in self.factory.nicks:
					self.send_negotiate_cmd()
					return
				else:
					logging.debug('this nick is already online.');
			else:
				logging.debug('not validated nick. dropping.')
			self.write('$ValidateDenide|')
			self.transport.loseConnection()

	def parse_validate_cmd(self, cmd):
		"""
		if user registred, and passwd is correct 
		we should connect it even if it's already connected (drop & connect)
		"""
		acmd = cmd.split(' ', 1)
		if acmd[0] == '$MyPass':
			logging.debug('MyPass %s' % acmd[1])
			if acmd[1] != self.factory.reglist[self._nick]['passwd']:
				logging.info('wrong pass')
				self.write(('<HUB> %s|$BadPass|' % (self._('Password incorrect. Provided: %s') % str(acmd[1]),)).encode(self.factory.charset))
				logging.debug('not validated nick. dropping.')
				self.transport.loseConnection()
				return
			else:
				if self._nick in self.factory.nicks:
					logging.debug('reconnecting identified user')
					try:
						self.factory.nicks[self._nick].descr.write('<HUB> You are connecting from different machine. Bye.|')
					except:
						pass
					self.factory.drop_user_by_nick(self._nick)
				self.send_negotiate_cmd()
				return
		#else:
		#	logging.debug('received wrong cmd: %s' % cmd)

	def send_negotiate_cmd(self):
		self._state = 'negotiate'
		logging.debug ('validated %s' % self._nick)
		for transport in self.factory.hello:
			reactor.callLater(0, transport.write, '$Hello %s|' % self._nick.encode(self.factory.charset))
		self.write('$Hello %s|$Supports %s |' % (self._nick.encode(self.factory.charset), self.factory.SUPPORTS))
		#self.write('$Hello %s|' % self._nick.encode(self.factory.charset))

	def parse_negotiate_cmd(self, cmd):
		acmd = cmd.split(' ', 1)
		if acmd[0] == '$MyINFO':
			try:
				user=DCUser(cmd, self.transport, self._addr)
			except:
				logging.warning( 'wrong myinfo from: %s addr: %s info: %s %s' % ( self._nick, self._addr, cmd, trace() ) )
			else:
				if self._nick in self.factory.reglist:
					user.level=self.factory.reglist[self._nick]['level']
				else:
					user.level='unreg'
				self.factory.nicks[self._nick] = user
				self.factory.addrs[self._addr] = user
				try:
					# --- APPLY LIMITS ---

					if user.share < self.factory.core_settings['min_share'] and user.level not in self.factory.core_settings['pass_limits']:
						self.write( (self._( '<HUB> Too low share. Min share is %s.|' ) % number_to_human_size( self.factory.core_settings['min_share'] ) ).encode( self.factory.charset ) )
						logging.debug('not validated. dropping')
						self.factory.drop_user(self._addr, self._nick, self.transport)
						return

					if user.sum_hubs > self.factory.core_settings['max_hubs'] and user.level not in self.factory.core_settings['pass_limits']:
						self.write( (self._( '<HUB> Too many hubs open. Max hubs is %s.|' ) % self.factory.core_settings['max_hubs']).encode( self.factory.charset ) )
						logging.debug('not validated. dropping')
						self.factory.drop_user(self._addr, self._nick, self.transport)
						return

					if user.slots < self.factory.core_settings['min_slots'] and user.level not in self.factory.core_settings['pass_limits']:
						self.write( (self._( '<HUB> Too few slots open. Min slots is %s.|' ) % self.factory.core_settings['min_slots']).encode( self.factory.charset ) )
						logging.debug('not validated. dropping')
						self.factory.drop_user(self._addr, self._nick, self.transport)
						return

					logging.debug('slots: %s, hubs: %s' % (user.slots, user.hubs) )

					if self.factory.emit('onConnected',user):
						logging.debug('Validated. Appending.')

						self.factory.transports.append(self.transport)

						if user.level in self.factory.oplevels:
							self.write('$LogedIn|')
							self.factory.send_to_all(self.factory.get_op_list())

						if not 'NoHello' in self._supports:
							self.factory.hello.append(self.transport)

						if not 'NoGetINFO' in self._supports:
							self.write(self.factory.get_nick_list().encode( self.factory.charset ))
						else:
							for i in self.factory.nicks.values():
								self.write(i.MyINFO.encode(self.factory.charset))
								self.write(self.factory.get_op_list().encode(self.factory.charset))
						self.factory.send_to_all(cmd)

						uips=self.factory.get_userip_acc_list()

						if ('UserIP' in self._supports) or ('UserIP2' in self._supports):
							self.factory.send_to_nick(self._nick, '$UserIP %s %s$$' %(self._nick, user.get_ip()))
							if user.level in self.factory.core_settings['userip']:
								self.factory.send_to_nick(self._nick, self.factory.get_userip_list())

						for unick in uips:
							self.factory.send_to_nick(unick, '$UserIP %s %s$$' %(self._nick, user.get_ip()))

						self.factory.send_usercommands_to_nick(self._nick)
						self.factory.send_to_nick(self._nick, '$HubTopic %s' % self.factory.core_settings['topic'])

					else:
						logging.debug('not validated. dropping')
						self.factory.drop_user(self._addr, self._nick, self.transport)
						return
				except:
					logging.debug('error while connect: %s' % trace())
					self.factory.drop_user(self._addr, self._nick, self.transport)
					return
			self._state = 'logedin'
			self.setTimeout(None)

	def timeoutConnection(self):
		"""
		Called when the connection times out.
		"""
		logging.debug('timeout: %s' % self._addr)
		self.write('<HUB> Login timeout!|')
		self.transport.loseConnection()

	def on_exit(self):
		self.work=False
		self.save_settings()
		sys.exit()




#RUNNING HUB
#application = service.Application('DirectConnect Hub')
hub = DCHub()
hub.protocol = DCProtocol
for i in hub.core_settings['port']:
	try:
		#internet.TCPServer(i, hub).setServiceParent(application)
		reactor.listenTCP(i, hub)
		logging.debug('Started on port %d' % i)
	except:
		logging.error('---- A PROBLEM WHILE BINDING TO PORT: %s \n %s----' % (i, trace(),) )
reactor.run()
