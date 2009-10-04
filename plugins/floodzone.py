#!/usr/bin/env python

# --- skeleton for plugin.
#
# ---

import plugin
import string
import logging

# --- !! Class name SHOULD BE FileName_plugin
class floodzone_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(floodzone_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                #self.commands['?']=self.?
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onMainChatMsg']=self.onMainChatMsg
                
                # --- REGISTERING USERCOMMANDS
		#self.usercommands['?']='$UserCommand 1 2 '+hub._('MENU\\ITEM')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'COMMAND %[nick] %[line:'+hub._('message')+':]&#124;|'
		
	def onMainChatMsg(self, from_nick, message):
		#params 'nick' 'message'
                mess=''
#                logging.info('message:'+message)
#                if self.hub.nicks[from_nick].level in self.immune:
                        # user immuned
#                        return True
                k=1
                capcount=0
                t=''
                for i in message:
                        if i==t:
                                if k<4:
                                        mess+=i
                                        k+=1
                        else:
                                mess+=i
                                k=1
                                t=i
                        if (i!=i.lower()):
                                capcount+=1
#                        logging.info('%s' % capcount)
#                logging.info('%s  ;; %s ;; %s' % (float(capcount)/float(len(mess)), len(mess), mess.lower()))
                if (float(capcount)/float(len(mess))>0.6) and (len(mess)>6):
                        mess=mess.lower()
                self.hub.send_to_all("<"+from_nick+"> "+mess+"|")                                    
                self.hub.emit('ChatHistEvent', from_nick, mess)
		return False
