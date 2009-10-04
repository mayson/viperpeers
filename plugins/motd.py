#!/usr/bin/env python

# --- motd plugin.
# Message Of The Day
#
# Send MOTD to user on login or by 'motd'command 
#
# ---

import plugin

class motd_plugin(plugin.plugin):
        
	def __init__(self, hub):
		super(motd_plugin,self).__init__(hub)
                self.commands['motd']=self.motd
                self.commands['SetMotd']=self.SetMotd

                self.slots['onConnected']=self.onConnected

                if 'motd' not in hub.settings:
                        hub.settings['motd']={'message':'PLEASE SET MOTD MESSAGE (!Set motd message <new message>)'}

                self.usercommands['SetMotd']='$UserCommand 1 2 '+hub._('MOTD\\Set MOTD...')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'SetMotd %[line:'+hub._('NEW_MOTD?')+':]&#124;|'
                self.usercommands['motd']='$UserCommand 1 2 '+hub._('MOTD\\MOTD')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'motd&#124;|'

        def onConnected(self,user):
                self.motd(user.addr)
                return True
		
	def motd(self,addr, params=[]):
                if 'motd' in self.hub.settings:
                        self.hub.send_to_addr(addr,self.hub.settings['motd']['message'])
                return ""
        def SetMotd(self,addr, params=[]):
                # params: 'message'

                if len(params)<=0:
                        return self.hub._('Params error')

                self.hub.settings['motd']['message']=' '.join(params)
                
                return self.hub._('Success')


