#!/usr/bin/env python

# --- Chathist plugin.
#
#    Send last N lines from chat to joined user
#
# ---

import plugin
import yaml
import time

class chathist_plugin(plugin.plugin):
		def __init__(self,hub):
				super(chathist_plugin,self).__init__(hub)
				if 'chathist' not in self.hub.settings or self.hub.settings['chathist']==[]:
					self.hub.settings['chathist']={'lines': 20}
				if 'chathist.db' not in self.hub.settings:
					self.hub.settings['chathist.db'] = []
				self.chlog=self.hub.settings['chathist.db']
				self.settings=self.hub.settings['chathist']
				self.slots['onConnected']=self.onConnected
				self.slots['ChatHistEvent']=self.ChatHistEvent

		def onConnected(self,user):
			self.hub.send_to_nick( user.nick, self.hub._( ' ---- Last history ---- \n%s' ) % '\n'.join( self.chlog ) )
			return True

		def ChatHistEvent(self, from_nick, message): 
			self.chlog.append('[%s] <%s> %s' % ( time.strftime( '%Y-%m-%d %H:%M:%S' ), from_nick, message ) )
			if len( self.chlog ) > self.settings['lines']:
				self.chlog.pop(0)
			return True    
