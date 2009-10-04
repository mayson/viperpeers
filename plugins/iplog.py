#!/usr/bin/env python

# --- skeleton for plugin.
#
# ---

import plugin
import time

# --- !! Class name SHOULD BE FileName_plugin
class iplog_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(iplog_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                if 'iplog' not in self.hub.settings:
			self.hub.settings['iplog']={'max_store':1000}

		if 'iplog.db' not in self.hub.settings:
			self.hub.settings['iplog.db']=[]

        	self.db=self.hub.settings['iplog.db']
		self.max= self.hub.settings['iplog']['max_store']

                # --- REGISTERING COMMANDS ---
                self.commands['iplog']=self.iplog
		self.commands['nicklog']=self.nicklog
		self.commands['nickiplog']=self.nickiplog
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onConnected']=self.onConnected
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['nicklog']='$UserCommand 1 2 '+hub._('Log\\Log selected user nick')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'nicklog %[nick]&#124;|'
		self.usercommands['nickiplog']='$UserCommand 1 2 '+hub._('Log\\Log selected user ip')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'nickiplog %[nick]&#124;|'
		self.usercommands['nicklog']+='$UserCommand 1 2 '+hub._('Log\\Log nick...')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'nicklog %[line:'+hub._('nick')+':]&#124;|'
		self.usercommands['iplog']='$UserCommand 1 2 '+hub._('Log\\Log ip...')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'iplog %[line:'+hub._('ip')+':]&#124;|'
	
	def onConnected( self, user ):
		if len(self.db)>self.max:
			self.db.pop(0)
		self.db.append( [user.nick, user.get_ip(), time.strftime('%Y-%m-%d %H:%M:%S')] )
		return True

	def iplog( self, addr, params=[] ):
		if len(params)>0:
			ip=params[0]
			res='IPLOG: %s\n' % ip
			for i in self.db:
				if i[1]==ip:
					res+=' %s - %s - %s \n' % (i[0], i[1], i[2])
			return res
		
		return self.hub._('Params error.')

	def nickiplog( self, addr, params=[] ):
		if len(params)>0:
			user=self.hub.nicks.get(params[0], None)
			if user==None:
				return self.hub._('No such user.')
			return self.iplog( addr, [user.get_ip()] )

		return self.hub._('Params error.')

	def nicklog( self, addr, params=[] ):
		if len(params)>0:
			nick=params[0]
			res='NICKLOG: %s\n' % nick
			for i in self.db:
				if i[0]==nick:
					res+=' %s - %s - %s \n' % (i[0], i[1], i[2])
			return res
		
		return self.hub._('Params error.')



	#def COMMAND(self,addr,params=[]):
	#	#params 'nick' 'message'
	#
	#	return RESULT_STRING
