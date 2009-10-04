#!/usr/bin/env python

# --- Forbid plugin.
#
#    Used against spammers attack 
#
# ---

import plugin
import re
import yaml
import logging
import traceback

trace=None
if 'format_exc' in dir(traceback):
        from traceback import format_exc as trace
else:
        from traceback import print_exc as trace


# --- !! Class name SHOULD BE FileName_plugin
class forbid_plugin(plugin.plugin):
        
	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(forbid_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                if 'forbid' not in self.hub.settings:
                        self.hub.settings['forbid']={'regexps':{}, 'immune':['owner']}
                        # an item:
                                # 'regexp':
                                        # { source, state, action }
                                        # source - mc (main chat)/ pm (private chat)/ all
                                        # action - any command
                
                self.regexps=self.hub.settings['forbid']['regexps']
                self.immune=self.hub.settings['forbid']['immune']

                # --- COMPILE REGEXPS --- 
                
                self.recompile()

                # --- REGISTERING COMMANDS ---
                self.commands['ListForbid']=self.ListForbid
                self.commands['AddForbid']=self.AddForbid
                self.commands['DelForbid']=self.DelForbid
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onMainChatMsg']=self.onMainChatMsg
                self.slots['onPrivMsg']=self.onPrivMsg
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['AddForbid']='$UserCommand 1 2 '+hub._('Forbid\\Add/Modify..')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'AddForbid %[line:'+hub._('regexp')+':]\n%[line:'+hub._('source')+':] %[line:'+hub._('action')+':]&#124;|'
                self.usercommands['DelForbid']='$UserCommand 1 2 '+hub._('Forbid\\Remove..')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'DelForbid %[line:'+hub._('regexp')+':]&#124;|'
                self.usercommands['ListForbid']='$UserCommand 1 2 '+hub._('Forbid\\List')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'ListForbid&#124;|'
		
	def AddForbid(self,addr,params=[]):
		#params ['regexp\nsource' 'action']
                ''' add forbid element into list'''
                full=' '.join(params)
                full=full.split('\n',1)
                if len(full)!=2:
                        return self.hub._('Params error')
                params=[]
                params.append(full[0])
                params.extend(full[1].split(' '))
                
                # params ['regexp' 'source' '...]

                if len(params)>=3:
                        if params[1] in ['mc', 'pm', 'all']:
                                action=' '.join(params[2:])
                                action=self.hub.unmasksyms(action)
                                params[0]=self.hub.unmasksyms(params[0])
                                # -- checking regexp
                                try:
                                        re.compile(params[0])
                                except:
                                        return self.hub._('Error %s' % trace())

                                self.regexps[params[0]]={'source':params[1],'action':action}
                                self.recompile()
                        else:
                                return self.hub._('Params error: %s should be %s recived %s') % ('source', 'mc/pm/all', repr(params))
                else:
                        return self.hub._('Params error')
	        
		return 'Success'

        def DelForbid(self, addr, params=[]):
                # params ['regexp']
                if len(params)!=1:
                        return self.hub._('Params error')
                params[0]=self.hub.unmasksyms(params[0])
                logging.debug('removing regexp %s' % params[0])
                if params[0] not in self.regexps:
                        return self.hub._('Not found')
                del self.regexps[params[0]]

                self.recompile()
                return 'Success'

        def ListForbid(self, addr, params=[]):
                return self.hub.masksyms(self.hub._(' -- Forbid List --\n')+unicode(yaml.safe_dump(self.hub.settings['forbid'],default_flow_style=False, allow_unicode=True),'utf-8'))



        def onMainChatMsg(self, from_nick, message):
                return self.parseMsg(from_nick, message, 'mc')

        def onPrivMsg(self, from_nick, to_nick, message):
                return self.parseMsg(from_nick, message, 'pm')


        def parseMsg(self, from_nick, message, source):
                
                #if source=='mc':
                #        msg=' '.join(params[1:])
                #else:
                #        msg=' '.join(params[2:])
                
                if self.hub.nicks[from_nick].level in self.immune:
                        # user immuned
                        return True
                logging.debug('parsing in forbid')
                for i in self.res:
                        if i.search(message)!=None:
                                #GOTCHA!
                                logging.debug('forbid signal')
                                if self.regexps[i.pattern]['source']==source or self.regexps[i.pattern]['source']=='all':
                                        action=self.regexps[i.pattern]['action']
                                        logging.debug('trigger %s found %s in %s' % (i.pattern,i.search(message).group(0),message))
                                        # -- specical actions!
                                        if action=='ignore':
                                                return False

                                        action=action.replace('%[nick]',from_nick)

                                        actions=action.split('|')


                                        for i in actions:
                                                acmd=i.split(' ')
                                                try:
                                                        addr=self.hub.nicks[from_nick].addr
                                                        if (len(acmd[1:]))>0:
                                                                result=self.hub.commands[acmd[0]](addr,acmd[1:])
                                                        else:
                                                                result=self.hub.commands[acmd[0]](addr)
                                                        if result!='':
                                                                if from_nick in self.hub.nicks:
                                                                        self.hub.send_to_addr(self.hub.nicks[from_nick].addr,self.hub._('<HUB> %s|') % result)
                                                except:
                                                        logging.error('error in forbid module: %s' % trace())

                                        return False
                                else:
                                        #no, different channel
                                        return True
                return True



        # -- INTERNAL METHODS --
        def recompile(self):
                self.res=[]
                for key,value in self.regexps.iteritems():
                        self.res.append(re.compile(key))
