#!/usr/bin/env python

# --- skeleton for plugin.
#
# ---

import plugin
import yaml
import logging
import traceback
import os
import sys
import signal
import re

trace=None
if 'format_exc' in dir(traceback):
        from traceback import format_exc as trace
else:
        from traceback import print_exc as trace

# --- !! Class name SHOULD BE FileName_plugin
class goodplug_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(goodplug_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                #self.commands['?']=self.?
                self.commands['AddPlugin']=self.AddPlugin
                self.commands['DelPlugin']=self.DelPlugin
                # --- REGISTERING SLOTS (On Event reaction)
		#self.slots['on?']=self.on?
                
                # --- REGISTERING USERCOMMANDS
		#self.usercommands['?']='$UserCommand 1 2 '+hub._('MENU\\ITEM')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'COMMAND %[nick] %[line:'+hub._('message')+':]&#124;|'
		#self.usercommands['AddPlugin']='$UserCommand 1 2 '+hub._('Plugins\\Add plugin\\')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'AddPlugin %[line:'+hub._('plugin')+':]&#124;|'
		#self.usercommands['DelPlugin']='$UserCommand 1 2 '+hub._('Plugins\\Del plugin\\')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'DelPlugin %[line:'+hub._('plugin')+':]&#124;|'
                
		
	#def COMMAND(self,addr,params=[]):
	#	#params 'nick' 'message'
	#
	#	return RESULT_STRING
	def update_menu( self ):
		self.usercommands['AddPlugin']=''
		self.usercommands['DelPlugin']=''

		for i in self.hub.get_aviable_plugins():
			if i not in self.hub.core_settings['autoload']:
				self.usercommands['AddPlugin'] += self.hub.UC( self.hub._( 'Plugins\\Add plugin to autolad\\%s' )% i, ['AddPlugin', i] )

		for i in self.hub.core_settings['autoload']:
			self.usercommands['DelPlugin'] += self.hub.UC( self.hub._( 'Plugins\\Remove plugin from autolad\\%s' ) % i, ['DelPlugin', i] )



	def AddPlugin(self,addr,params=[]):
		ans=[]
		try:
			for i in os.listdir(self.hub.path_to_plugins):
				if self.hub.recp['.py'].search(i)!=None and i!="__init__.py" and i!="plugin.py":
					mod=self.hub.recp['before.py'].search(i).group(0)
					ans.append(mod)
			if params[0] in ans:
				self.hub.core_settings['autoload'].append(params[0])
				self.hub.Gen_UC()
				self.hub.send_usercommands_to_all()
		

				return self.hub._('Success')
			else:
				return self.hub._('No plugin')
		except:
			logging.error('error while listing plugins: %s', trace())
		
		
	def DelPlugin(self,addr,params=[]):
		if params[0] in self.hub.core_settings['autoload']:
			t=[]
			for j in self.hub.core_settings['autoload']:
				if params[0] != j:
					t.append(j)
			self.hub.core_settings['autoload']=t
			self.hub.Gen_UC()
			self.hub.send_usercommands_to_all()
		

			return self.hub._('Success')
		else:
			return self.hub._('No plugin')
