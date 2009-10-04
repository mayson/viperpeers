#!/usr/bin/env python

# --- regme plugin.
#
#  Allow user self registration process
# 
# ---

import plugin

# --- !! Class name SHOULD BE FileName_plugin
class regme_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(regme_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                self.commands['regme']=self.regme
                self.commands['reghelp']=self.reghelp
		
                # --- REGISTERING SLOTS (On Event reaction)
		#self.slots['on?']=self.on?
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['regme']='$UserCommand 1 2 '+hub._('Register My Nick ...')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'regme %[line:'+hub._('password')+':]&#124;|'
		
	def regme(self,addr,params=[]):
		#params 'passwd'
                if len (params)<1:
                        return self.hub._('Params error') +'\n'+ self.hub._('Usage: %sregme password') % (hub.core_settings['cmdsymbol'], )

                nick=self.hub.addrs[addr].nick
                if nick in self.hub.reglist:
                        return self.hub._('User already registred')

                password=params[0]

                self.hub.reglist[nick]={'passwd': password, 'level': 'reg'}
                self.hub.nicks[nick].level='reg'
                self.hub.send_usercommands_to_nick(nick)
		
                return self.hub._('Registered nick: %s with password: %s') % (nick, password)
	def reghelp(self,addr,params=[]):
                return self.hub._('To register please use the %sregme. The syntax is: %sregme <password>') % (self.hub.core_settings['cmdsymbol'],self.hub.core_settings['cmdsymbol'])
