#!/usr/bin/env python

# --- logger plugin.
# log PM and MC to file
# ---

import plugin
import logging
import time
class logger_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(logger_plugin,self).__init__(hub)

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                #self.commands['?']=self.?
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onMainChatMsg']=self.onMainChatMsg
		self.slots['onPrivMsg']=self.onPrivMsg
                
                # --- REGISTERING USERCOMMANDS
		#self.usercommands['?']='$UserCommand 1 2 '+hub._('MENU\\ITEM')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'COMMAND %[nick] %[line:'+hub._('message')+':]&#124;|'
		

	def onMainChatMsg(self, from_nick, message):
		open('./mc-%s.log' % time.strftime( '%d-%m-%y' ),'a').write(('%s - %s: %s\n' % (time.strftime('%x %X'), from_nick, message)).encode('utf-8'))
		return True
	def onPrivMsg(self, from_nick, to_nick, message):
		open( './pm-%s.log' % time.strftime( '%d-%m-%y' ) , 'a' ).write(('%s - %s -> %s: %s\n' % (time.strftime('%x %X'), from_nick, to_nick,  message)).encode('utf-8'))
		return True
