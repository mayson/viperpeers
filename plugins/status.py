#!/usr/bin/env python

# --- skeleton for plugin.
#
# ---

import plugin
import threading

# --- !! Class name SHOULD BE FileName_plugin
class status_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(status_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
        
                # --- REGISTERING COMMANDS ---
                self.commands['Status']=self.Status
		
                # --- REGISTERING SLOTS (On Event reaction)
		#self.slots['on?']=self.on?
                
                # --- REGISTERING USERCOMMANDS
		#self.usercommands['?']='$UserCommand 1 2 '+hub._('MENU\\ITEM')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'COMMAND %[nick] %[line:'+hub._('message')+':]&#124;|'
		
	def Status(self,addr,params=[]):
		#params 'nick' 'message'
		status='\n'
		status+='Active threads: %s\n' % str(threading.activeCount())
		k=[]
		for i, t in enumerate(threading.enumerate()):
			if t.isAlive():
				k.append('%s %s' %( str(i), t.getName()))
		#status+='\n'.join(k)
		status+='Alive threads: \n%s\n' % '\n'.join(k)
		status+='Active workers: %s\n' % str(len(self.hub.clthreads))
		status+='WORKER_MAX: %s\n' % self.hub.WORKER_MAX
		for i, t in enumerate(self.hub.clthreads):
			status+='Worker %s status: %s. Serving %s clients.\n' % (i, t.isAlive(),len(self.hub.descriptors[i]))
		return status
