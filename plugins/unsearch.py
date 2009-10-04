#!/usr/bin/env python
#coding: utf-8

# --- unsearch plugin
# refuses often search requests - more than 1 in a minute
# ---

import plugin
import yaml
import datetime
import time
import logging

# --- !! Class name SHOULD BE FileName_plugin
class unsearch_plugin(plugin.plugin):
#        i=0

	def __init__(self, hub):

                # Don't forget replace 'name_plugin' here
		super(unsearch_plugin,self).__init__(hub)
                

                # --- SETTINGS FOR PLUGIN ---
                #if 'name' not in self.hub.settings:
                #        self.hub.settings['name']={}
#                if 'unsearch.db' not in self.hub.settings:
                self.hub.settings['unsearch.db']=[]
                        

                self.db=self.hub.settings['unsearch.db']
        
                # --- REGISTERING COMMANDS ---
                self.commands['stime']=self.stime
		
                # --- REGISTERING SLOTS (On Event reaction)
		self.slots['onSearch']=self.onSearch
		self.slots['onSearchHub']=self.onSearch
		self.slots['onSearchResult']=self.onSearchResult
                
                # --- REGISTERING USERCOMMANDS
		#self.usercommands['?']='$UserCommand 1 2 '+hub._('MENU\\ITEM')+'$<%[mynick]> '+hub.core_settings['cmdsymbol']+'COMMAND %[nick] %[line:'+hub._('message')+':]&#124;|'
		
	#def COMMAND(self,addr,params=[]):
	#	#params 'nick' 'message'
	#
	#	return RESULT_STRING
	def onSearch( self, addr, sstr):
#                logging.info('%s %s' % (addr,sstr) )
                ip=addr.split(':')[0]
                if ip=='Hub':
                        ip=addr.split(':')[1]
                        ip=self.hub.nicks[ip].addr.split(':')[0]
                ptime=len(self.hub.nicks)/5*3
#                logging.info('%s %s' % (_i,ptime) )
#                if (_i*30<ptime):
#                        _i=ptime/30
#                logging.info('ptime %s' % (ptime) )
                t = datetime.datetime.now()
                tm=time.mktime(t.timetuple())
#                logging.info('%s %s %s' % (t,ip,tm) )                
                for i in self.db:
			if i[0]==ip:
                                if (tm-i[1])<ptime:
                                        #logging.info('False %s %s %s' % (i[0],i[1],tm) )
                                        return False
                                else:
                                        i[1]=tm
                                        i[2]=0
                                        #logging.info('True %s %s %s' % (i[0],i[1],tm) )
                                        return True
                self.db.append( [ip, time.mktime(t.timetuple()),0] )
                return True
                
        def stime(self,addr,params=[]):
                return self.hub._('Minimal search interval - %s s') % (len(self.hub.nicks)/5*3)
        
        def onSearchResult (self, from_nick, to_nick, message):
                try:
                        ip=self.hub.nicks[to_nick].addr.split(':')[0]
                        for i in self.db:
                                if i[0]==ip:
                                        if i[2]<5:
                                                i[2]+=1
                                                #logging.info('TRUE: %s %s' % (i[0],i[2]))
                                                return True
                                else:
                                                #logging.info('FALSE: %s %s' % (i[0],i[2]))
                                                return False                        
                except:
#                        logging.error('unable to find user with nick %s' % to_nick)
                        return False
                #logging.info('ONSR: %s - %s:%s - %s' % (from_nick, to_nick,ip, message) )                

                #logging.info('No such ip')
                return False

