#!/usr/bin/env python

# --- chatroom plugin.
#
#    Chatroom Support for ViperHive
#    
#    STATUS: NOT WORKING
#
# ---

import plugin
import pydcppbot
import threading
import re
import logging
import string
import random


class chatroom( pydcppbot.dcppbot ):

	recp=re.compile('\$<([^ ]*)> (.*)')

	def __init__( self, hub, name='#ChatRoom' ):
		
		logging.debug( 'CREATING CHATROOM' )

		self.hub=hub
		self.nicks=[]
		
		passwd=unicode(self.genpass(10))

		hub.reglist[name]={'level':'chatroom','passwd': passwd}

		super( chatroom, self ).__init__( 'localhost', hub.core_settings['port'][0], name, passwd )
		
		self.charset = self.hub.charset

	def genpass( self, size=10 ):
		s=[]
		for i in range( size ):
			s.append( random.choice( string.letters + string.digits ) )
		return ''.join(s)

	def parser ( self, msg ):
		logging.debug( 'CHATROOM: parsing message %s' % msg )
		
		try:
			amsg=self.recp.search(msg)
			if amsg==None:
				return
			logging.debug( 'CHATROOM: Message captured: %s' % msg )
			nick=amsg.group(1)
			message=amsg.group(2)
			
			logging.debug( 'CHATROOM: from: %s msg: %s' % ( nick, message ) )

			if nick not in self.nicks:
				return

			logging.debug( 'CHATROOM: nick %s accepted, sending message' % nick )

			fmsg='<%s> %s|' % ( nick, message )
			for i in self.nicks:
				if i==nick:
					continue
				self.hub.send_pm_to_nick( self.NICK, i, fmsg )
		except:
			logging.error('CHATROOM ERROR %s' % pydcppbot.trace())

		logging.debug( 'CHATROOM: message parsed' )
		return




# --- !! Class name SHOULD BE FileName_plugin
class chatroom_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super( chatroom_plugin, self ).__init__( hub )
                
		self.roomthreads = {}
		self.rooms = {}
		

                # --- SETTINGS FOR PLUGIN ---
                if 'chatroom' not in self.hub.settings:
			self.hub.settings['chatroom'] = {'#OpChat': { 'allow': ['owner','op'], 'autojoin': ['owner', 'op']} }
		self.settings=self.hub.settings['chatroom']


        
                # --- REGISTERING COMMANDS ---
                self.commands['join'] = self.join
		self.commands['left'] = self.left
		self.commands['listroom'] = self.listroom

		self.loadrooms()
		#self.commands['listroom'] = self.listroom
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onUserLeft']=self.onUserLeft
		self.slots['onConnected']=self.onConnected
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['join']='$UserCommand 1 2 '+hub._('Chatrooms\\Join selected room')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'join %[nick]&#124;|'
		self.usercommands['left']='$UserCommand 1 2 '+hub._('Chatrooms\\Left selected room')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'left %[nick]&#124;|'
		self.usercommands['listroom']='$UserCommand 1 2 '+hub._('Chatrooms\\Who is in room?')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'listroom %[nick]&#124;|'

	
	def unload( self ):
		logging.debug('DESTROYING CHATROOMS')
		for room in self.rooms.itervalues():
			room.work=False
		
	def loadrooms( self ):
		for i, r in self.settings.items():
			room=chatroom( self.hub, i )
			self.rooms[i]=room 
			for nick, user in self.hub.nicks.iteritems():
				if user.level in r['autojoin']:
					room.nicks.append(nick)
			
			roomthread=threading.Thread( None, room.run, 'chatroom', () )
			self.roomthreads[i]=roomthread
			roomthread.setDaemon(True)
			roomthread.start()


	def onConnected( self, user ):
		for rname, rparams in self.settings.items():
			if user.level in rparams['autojoin']:
				self.rooms[rname].nicks.append( user.nick )
		return True

	def onUserLeft( self, addr, nick ):
		for room in self.rooms.values():
			if nick in room.nicks:
				room.nicks.remove( nick )
		return True


	def join( self, addr, params=[]):
		# params ['room']
		if len( params ) <= 0:
			return self.hub._('Params error.')

		room = params[0]
		if room not in self.rooms:
			return self.hub._('Params error.')

		nick = self.hub.addrs[addr].nick
		level = self.hub.addrs[addr].level
		room=self.rooms[room]
		if nick in room.nicks:
			return self.hub._('Already in room.')

		if level in self.settings[params[0]]['allow']:		
			room.nicks.append( nick )
		else:
			return self.hub._( 'Premission denied.' )

		return self.hub._('Success')

	def left( self, addr, params=[]):
		# params ['room']
		if len( params ) <= 0:
			return self.hub._('Params error.')

		room = params[0]
		if room not in self.rooms:
			return self.hub._('Params error.')

		nick = self.hub.addrs[addr].nick
		room=self.rooms[room]
		if nick not in room.nicks:
			return self.hub._('Params error.')
		room.nicks.remove( nick )
		return  self.hub._('Success')

	def listroom( self, addr, params=[] ):
		#params ['room']

		if len( params ) <= 0:
			return self.hub._( 'Params error.' )

		room = params[0]
		if room not in self.rooms:
			return self.hub._( 'Params error.' )
		room = self.rooms[room]
		ans = self.hub._( 'Users in room %s: %s' ) % ( params[0], ', '.join(room.nicks) )

		return ans


	#def listroom( self, addr, params=[]):
	#	pass
	




	#def COMMAND(self,addr,params=[]):
	#	#params 'nick' 'message'
	#
	#	return RESULT_STRING
