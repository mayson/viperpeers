#!/usr/bin/env python


class plugin(object):
        
        def __init__(self,hub):
                self.hub=hub
		self.commands={}
		self.slots={}
		self.usercommands={}

	def unload( self ):
		pass

	def update_menu( self ):
		pass

