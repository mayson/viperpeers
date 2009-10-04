#!/usr/bin/env python

# --- skeleton for plugin.
#
# ---

import plugin

# --- !! Class name SHOULD BE FileName_plugin
class massmsg_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(massmsg_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                self.commands['MassMsg']=self.MassMsg
		
                # --- REGISTERING SLOTS (On Event reaction)
		#self.slots['on?']=self.on?
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['MassMsg']='$UserCommand 1 2 '+hub._('Send to all...')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'MassMsg %[line:'+hub._('message')+':]&#124;|'
		
	def MassMsg(self,addr,params=[]):
		#params 'nick' 'message'
		if len(params)>0:
			fnick=self.hub.core_settings['hubname'].replace(' ','_')
			for nick in self.hub.nicks.keys():
				self.hub.send_pm_to_nick(fnick, nick, ' '.join(params))
		else:
			return self.hub._('Params error')
		return ''
