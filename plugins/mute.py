#!\\usr\\bin\\env python

# --- mute plugin.
#
#   Mute nicks\\addres
#
# ---

import plugin
import yaml
import datetime
import time

class mute_plugin(plugin.plugin):
        
	def __init__(self, hub):
		super(mute_plugin,self).__init__(hub)


                # --- SETTINGS FOR PLUGIN ---
                if 'mute' not in self.hub.settings:
                        self.hub.settings['mute']={'nicks':{},'addrs':{}, 'immune':['owner']}

                self.mutelist=hub.settings['mute']
                
                        #{'reason':reason,'what':(mc,pm,all),'expired':datetime}
        
                # --- REGISTERING COMMANDS ---
                self.commands['mute']=self.mute
                self.commands['muteNick']=self.muteNick
                self.commands['muteAddr']=self.muteAddr
                self.commands['unmute']=self.unmute
                self.commands['unmuteNick']=self.unmuteNick
                self.commands['unmuteAddr']=self.unmuteAddr
                self.commands['ListMute']=self.ListMute
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onMainChatMsg']=self.onMainChatMsg
                self.slots['onPrivMsg']=self.onPrivMsg
                
                # --- REGISTERING USERCOMMANDS
		self.usercommands['mute']='$UserCommand 1 2 '+hub._('Mute\\Mute mc+pm...')+'$<%[mynick]> !mute %[nick] all %[line:'+hub._('reason')+':]&#124;|$UserCommand 1 2 '+hub._('Mute\\Mute mc...')+'$<%[mynick]> !mute %[nick] mc %[line:'+hub._('reason')+':]&#124;|$UserCommand 1 2 '+hub._('Mute\\Mute pm...')+'$<%[mynick]> !mute %[nick] pm %[line:'+hub._('reason')+':]&#124;|$UserCommand 1 2 '+hub._('Mute\\Time Mute mc+pm...')+'$<%[mynick]> !mute %[nick] all %[line:'+hub._('time')+':] %[line:'+hub._('reason')+':]&#124;|$UserCommand 1 2 '+hub._('Mute\\Time Mute mc...')+'$<%[mynick]> !mute %[nick] mc %[line:'+hub._('time')+':] %[line:'+hub._('reason')+':]&#124;|$UserCommand 1 2 '+hub._('Mute\\Time Mute pm...')+'$<%[mynick]> !mute %[nick] pm %[line:'+hub._('time')+':] %[line:'+hub._('reason')+':]&#124;|'
                self.usercommands['unmute']='$UserCommand 1 2 '+hub._('Mute\\Unmute selected nick')+'$<%[mynick]> !unmute %[nick]&#124;|'
                self.usercommands['ListMute']='$UserCommand 1 2 '+hub._('Mute\\ListMute')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'ListMute &#124;|'

	
        def onMainChatMsg(self, from_nick, msg):
                if from_nick not in self.hub.nicks:
                        return True
                user=self.hub.nicks[from_nick]
                if user.level in self.mutelist['immune']:
                        return True
                if user.nick in self.mutelist['nicks']:
			if datetime.datetime(*(time.strptime(self.mutelist['nicks'][user.nick]['expired'],'%Y-%m-%dT%H:%M:%S')[0:6]))>datetime.datetime.now():
                                if self.mutelist['nicks'][user.nick]['what'] in ['mc', 'all']:
                                        return False
                        else:
                                self.mutelist['nicks'].pop(user.nick)

                adr=user.addr.split(':')[0]
                if adr in self.mutelist['addrs']:
			if datetime.datetime(*(time.strptime(self.mutelist['addrs'][adr]['expired'],'%Y-%m-%dT%H:%M:%S')[0:6]))>datetime.datetime.now():
                                if self.mutelist['addrs'][adr]['what'] in ['mc', 'all']:
                                        return False
                        else:
                                self.mutelist['addrs'].pop(adr)
                return True

        def onPrivMsg(self, from_nick, to_nick, msg):
                if from_nick not in self.hub.nicks:
                        return True
                user=self.hub.nicks[from_nick]
                if user.level in self.mutelist['immune']:
                        return True
                if user.nick in self.mutelist['nicks']:
			if datetime.datetime(*(time.strptime(self.mutelist['nicks'][user.nick]['expired'],'%Y-%m-%dT%H:%M:%S')[0:6]))>datetime.datetime.now():
                                if self.mutelist['nicks'][user.nick]['what'] in ['pm', 'all']:
                                        return False
                        else:
                                self.mutelist['nicks'].pop(user.nick)

                adr=user.addr.split(':')[0]
                if adr in self.mutelist['addrs']:
			if datetime.datetime(*(time.strptime(self.mutelist['addrs'][adr]['expired'],'%Y-%m-%dT%H:%M:%S')[0:6]))>datetime.datetime.now():
                                if self.mutelist['addrs'][adr]['what'] in ['pm', 'all']:
                                        return False
                        else:
                                self.mutelist['addrs'].pop(adr)
                return True

        def mute (self, addr, params=[]):
                #params 'nick' 'what' ('time') 'reason'
                if len(params)>=3:
                        if params[0] in self.hub.nicks:
                                maddr=self.hub.nicks[params[0]].addr.split(':')[0]

                                self.muteNick(addr, params)

                                params[0]=maddr
                                self.muteAddr(addr, params)
                                return self.hub._('Success')
                        else:
                                return self.hub._('No such nick')
                else:
                        return hub._('Params error')
        def muteNick (self, addr, params=[]):
                # params: 'nick' 'what' ('time') 'reason'

                if len(params)>=3:
                        what=params[1]
                        if what not in ['mc','pm','all']:
                                return self.hub._('Params error: should be %s') % ('nick what(mc/pm/all) (time) reason)')
                        try:
                                mutetime=float(params[2])
                        except:
                                mutetime=None

                        if len(params)>3 and mutetime!=None:
                                # time mute
                                tomute=(datetime.datetime.now()+datetime.timedelta(hours=mutetime)).strftime('%Y-%m-%dT%H:%M:%S')
                                reason=" ".join(params[3:])
                        else:
                                # 2000 years
                                tomute=(datetime.datetime.now()+datetime.timedelta(days=999999)).strftime('%Y-%m-%dT%H:%M:%S')
                                reason=" ".join(params[2:])
                        reason+=" by "+self.hub.addrs[addr].nick
                        self.mutelist['nicks'][params[0]]={'what':what,'expired':tomute,'reason':reason}
                        return self.hub._('Success')

                else:
                       return self.hub._('Params error: should be %s') % ('ip (time) reason') 

        def muteAddr (self, addr, params=[]):
                if len(params)>=3:
                        what=params[1]
                        if what not in ['mc','pm','all']:
                                return self.hub._('Params error: should be %s') % ('nick what(mc/pm/all) (time) reason)')
                        try:
                                mutetime=float(params[2])
                        except:
                                mutetime=None

                        if len(params)>3 and mutetime!=None:
                                # time mute
                                tomute=(datetime.datetime.now()+datetime.timedelta(hours=mutetime)).strftime('%Y-%m-%dT%H:%M:%S')
                                reason=" ".join(params[3:])
                        else:
                                # 2000 years
                                tomute=(datetime.datetime.now()+datetime.timedelta(days=999999)).strftime('%Y-%m-%dT%H:%M:%S')
                                reason=" ".join(params[2:])
                        reason+=" by "+self.hub.addrs[addr].nick
                        self.mutelist['addrs'][params[0]]={'what':what,'expired':tomute,'reason':reason}
                        return self.hub._('Success')

                else:
                       return self.hub._('Params error: should be %s') % ('ip (time) reason') 
        def unmute (self, addr, params=[]):
                #params 'nick'
                if len(params)>=1:
                        if params[0] in self.hub.nicks:
                                maddr=self.hub.nicks[params[0]].addr.split(':')[0]

                                self.unmuteNick(addr, params)

                                params[0]=maddr
                                self.unmuteAddr(addr, params)
                                return self.hub._('Success')
                        else:
                                return self.hub._('No such nick')
                else:
                        return self.hub._('Params error')
        def unmuteNick (self, addr, params=[]):
                i=self.mutelist['nicks'].pop(params[0],None)
                if i!=None:
                        return self.hub._('Success')
                else:
                        return self.hub._('Not Found')

        def unmuteAddr (self, addr, params=[]):
                i=self.mutelist['addrs'].pop(params[0],None)
                if i!=None:
                        return self.hub._('Success')
                else:
                        return self.hub._('Not Found')

        def ListMute(self, addr, params=[]):
                return self.hub._(' -- Mute List --\n')+unicode(yaml.safe_dump(self.hub.settings['mute'],default_flow_style=False, allow_unicode=True),'utf-8')

