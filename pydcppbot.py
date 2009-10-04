
# -*- coding: utf-8 -*-
# Based on Apkawa's PyDC++ bot
# Currently used for viperhive stability testing.
# Emulate numerous client connections.
import socket, re, time
import thread
import select
import logging

class dcppbot(object):
	def __init__(self, HOST, PORT, NICK, PASS=None, DESCR='PYDCPPBOT', TAG='<PyDC++BOT V:0.002 S:10 H:0/0/0>', SHARE=0, CHARSET='utf-8'):
		self.HOST=HOST
		self.PORT=PORT
		self.NICK=NICK
		self.DESCR=DESCR
		self.PASS=PASS
		self.TAG=TAG
		self.SHARE=SHARE
		self.sock=None
		self.work=False
		self.charset=CHARSET
			
	def close(self):
		self.sock.close()
	
	def send_mainchat(self, text):
		text=('<%s> %s|'%(self.NICK,text))
		self.sock.send(text.encode( self.charset ))
	def send_pm(self,to,text):
		text=('$To: %s From: %s $<%s> %s|'%(to,self.NICK,self.NICK,text))
		self.sock.send(text.encode( self.charset ))
		
	def drop_msgs(self):
		while True:
			self.sock.recv(2048)
		
	def _createKey(self,lock):
		key = {}
		for i in xrange(1, len(lock)):
			key[i] = ord(lock[i]) ^ ord(lock[i-1])
		key[0] = ord(lock[0]) ^ ord(lock[len(lock)-1]) ^ ord(lock[len(lock)-2]) ^ 5
		for i in xrange(0, len(lock)):
			key[i] = ((key[i]<<4) & 240) | ((key[i]>>4) & 15)

		out = ''
		for i in xrange(0, len(lock)):
			out += unichr(key[i])

		out = out.replace(u'\0', u'/%DCN000%/').replace(u'\5', u'/%DCN005%/').replace(u'\44', u'/%DCN036%/')
		out = out.replace(u'\140', u'/%DCN096%/').replace(u'\174', u'/%DCN124%/').replace(u'\176', u'/%DCN126%/')

		return out

	def parser( self, msg ):
		logging.error('BOT WARNING: No parser function')
		return

	def run( self, newparser=None ):
		
		logging.debug( 'RUNNING PYDCPPBOT MESSAGE PARSER' )

		self.work=True
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.HOST,self.PORT))
		lock=self.sock.recv(1024)
		lock_key=re.findall('\$Lock[\s](.*?)[\s]', lock)[0]
		key =self._createKey(lock).encode("utf-8")
		self.sock.send('$Key %s|$ValidateNick %s|'%(key,self.NICK.encode( self.charset )))
		self.sock.recv(4096)
		if self.PASS == None:
			self.sock.send(('$Version 1,0091|$GetNickList|$MyINFO $ALL %s %s%s$ $0$$%s$|' % (self.NICK,self.DESCR,self.TAG,self.SHARE)).encode( self.charset ))
		else: 
			self.sock.send( ('$Version 1,0091|$MyPass %s|$GetNickList|$MyINFO $ALL %s %s%s$ $0$$%s$|' %(self.PASS,self.NICK,self.DESCR,self.TAG,self.SHARE) ).encode( self.charset ))


		if newparser != None:
			logging.debug ( 'New paserr defined' )
			self.parser=newparser
		
		logging.debug( 'Bot parser: %s' % repr(self.parser) )
		self.sock.settimeout(5)

		self.sock.send( '$BotINFO|' )


		while self.work:
			try:
				s = ''
				(sr,sw,sx)=select.select([self.sock],[],[],1)

				if sr==[]:
					continue
				try:
					s = unicode(self.sock.recv(4096), self.charset)
				except:
					logging.error( '%s \nString recived: %s' % (pydcppbot.trace(), s) )
					continue
				

				if s == '':   # connection break
					logging.error( 'pydcppbot: connection lost' )
					break

				# check if message too long?
				k=5
				while s[-1] != '|' and k > 0:
					(sr,sw,sx)=select.select([self.sock],[],[],1)
					if sr == []:
						logging.error( 'pydcppbot eror: String recived: %s' % (s,) )
						break
					try:
						s += unicode(self.sock.recv(4096), self.charset)
					except:
						logging.error( '%s \nString recived: %s' % (trace(), s) )
						continue
				if s[-1] != '|':
					continue

				logging.debug( 'pydcppbot - parsing: %s' % s )
				
				self.parser( s )
			except:
				logging.error( trace() )
				self.work = False
				break

		self.sock.send('$Quit|')
		self.sock.close()

		return





#HE WE ARE. LAUNCHING...	
if __name__=='__main__':
	k=[]
	for i in xrange(0,500):
		try:
			dc=dcppbot('localhost', 11411, '%s' % i)
			thread.start_new_thread(dc.drop_msgs,())
			k.append(dc)
			print(len(k))
			time.sleep(0.1)
		except:
			print(len(k))
			print(traceback.format_exc())
			
			
	while True:
		#pass
		time.sleep(100)
		
		

				
				
				
