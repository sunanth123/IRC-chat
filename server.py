import sys
import select 
import socket

PORT = 1200 #Server port
HOST = ''

#this class is to create channels which will hold the name of channel and list of users in the channel.
class channel:
	
	def __init__(self,name):
		self.name = name	#name of channel
		self.chan_users = []	#users in channel (stores the socket)
	
	#add user to channel
	def add(self,username,ssocket):
		self.chan_users.append(ssocket)
		for i in self.chan_users:
			if i != ssocket:
				i.sendall('%s has joined channel %s' %(username, self.name))
	
	#remove user from channel
	def removeuser(self,username,ssocket):
		for i in self.chan_users:
			if i != ssocket:
				i.sendall('%s has left channel %s\n' %(username, self.name))
		self.chan_users.remove(ssocket)
	
	#verify and return user if exists in channel
	def retuser(self,ssocket):
		for i in self.chan_users:
			if i == ssocket:
				return ssocket
	

#This class is for the server and it will initialize the server socket as well as connect the client sockets.
class server:

	#initialize the server and get it ready to accept incoming client connections.
	def __init__(self):
		self.users = []	#this list will hold tuples (username,socket)
		self.user_channel = []	#this list will hold tuples (socket,channel)
		self.channels = []	#this list will hold channel objects
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
		self.server_socket.bind((HOST, PORT))
		self.server_socket.listen(10)
		self.getdes = [self.server_socket, sys.stdin]

		print('Server connected on port %s' %(PORT))

	#this function will run continously until the server disconnects. 
	def start(self):
		read, write, error = select.select(self.getdes, [], [])	#blocks until socket is ready.
		for s in read:
			#if the read in socket is the server socket then get ready to accept client connection
			if s == self.server_socket:
				newsocket, addr = self.server_socket.accept()
				self.getdes.append(newsocket)
				newsocket.sendall('Connected to server on port %s\n' %PORT)
				print('Client joined server (%s:%s)' % addr)
			#if the server has a command then this branch is taken
			elif s == sys.stdin:
				server_message = sys.stdin.readline()
				cmd = (server_message.split(" ")[0]).split("\n")[0]
				#this server command will remove a client from the server.
				if cmd == "KICK":
					if len(server_message.split(" ")) == 2:
						username = (server_message.split(" ")[1]).split("\n")[0]
						flag = 0
						for i in self.users:
							if i[0] == username:
								ksock = i[1]
								ksock.sendall('Kicked from server')
								self.disconnect(ksock)
								flag = 1
						if flag == 0:
							print('%s does not exist in server'%username)
				#this server command will gracefully disconnect the server
				elif cmd == "DC":
					for i in self.users:
						i[1].sendall('Server shutting down')
					sys.exit()
				#this server command will display all information	
				elif cmd == "INFOALL":
					infousers = 'List of users in server\n'
					infochannels = 'List of channels in server\n'
					mapping = 'Channel with corresponding users\n'
					for i in self.users:
						infousers = infousers + i[0] + '\n'
					for i in self.channels:
						infochannels = infochannels + i.name + '\n'
					for i in self.channels:
						mapping = mapping + i.name + ' --> '
						for y in self.user_channel:
							if i.name == y[1].name:
								for z in self.users:
									if y[0] == z[1]:
										username = z[0]
								mapping = mapping + '|' + username + '|'
						mapping = mapping + '\n'
					print(infousers + '\n' + infochannels + '\n' +  mapping)		
						
				else: 
					print('Not a valid server command')
			#if this branch is taken then the read in socket is from the client so must process data.
			else:
				cmess = s.recv(4096)
				if cmess == '':
					self.disconnect(s)
				else:
					cmd = (cmess.split(" ")[0].split("\n")[0])
					#dispatch table to run respective command
					dispatch = {'EXIT': self.exit, 'REG': self.reg, 'JOIN': self.join, 'LIST': self.listing, 'MEM': self.mem, 'LEAVE':self.leave, 'MESS': self.mess, 'WHISPER': self.whisper, 'GET': self.get}
					try:
						dispatch[cmd](cmess,s)
					except:
						s.sendall('Not valid command')
	
	#this command allows the client to gracefully disconnect from the server.
	def exit(self,cmess,s):
		for i in self.users:
			if s == i[1]:
				username = i[0]
		self.disconnect(s)
		for i in self.users:
			if i[1] == s:
				self.users.remove(i)
		print('Client %s has left the server' % username)

	#this command allows the client to register with a username.
	def reg(self,cmess,s):
		username = (cmess.split(" ")[1]).split("\n")[0]
		ip,port = s.getpeername()
		for i in self.users:
			if i[0] == username:
				if i[1] != s:
					#if username already exists then append unique port to end of username
					username = username + str(port)
					s.sendall('Username already exists, signed in as %s'%username)
		#check if client already has a username and if so replace with new
		for i in self.users:
			if i[1] == s:
				self.users.remove(i)
		x = username,s
		self.users.append(x)

	#this command allows the client to join a channel.
	def join(self,cmess,s):
		if len(cmess.split(" ")) == 1:
			sock.sendall('Error, try: JOIN <Channel>')
		else:
			addr = s.getpeername()
			chan_name = (cmess.split(" ")[1]).split("\n")[0]
			tempchan = None
			for i in self.channels:
				if i.name == chan_name:
					tempchan = i
			for i in self.users:
				if i[1] == s:
					username = i[0]
			#This branch taken if channel already exists
			if tempchan is not None:
				if len(tempchan.chan_users) < 11:	#check if max users in channel
					sockcheck = tempchan.retuser(s)
					if sockcheck is None:
						tempchan.add(username,s)
						self.addinguser(tempchan,s)
						print('Client (%s:%s) has joined channel '%addr + chan_name)
					else:
						s.sendall('Already in channel %s' % chan_name)
				else:
					s.sendall('Channel %s has max users' % chan_name)

			#this branch taken if channel doesnt exist
			else:
				addchannel = channel(chan_name)
				self.channels.append(addchannel)
				addchannel.add(username,s)
				self.addinguser(addchannel,s)
				print('New channel ' + chan_name + ' made and joined by (%s:%s)' % addr)

	#This command lists all the channels in the server
	def listing(self,cmess,s):
		flag = 0
		list_chans = ''
		for i in self.channels:
			list_chans = list_chans + i.name + "\n"
			flag = 1
		#this means no channel exists on server
		if flag == 0:
			s.sendall('No channels exist on server')
		else:
			s.sendall('List of Channels\n' + list_chans)				
	
	#this command lists all members of a desired channel.
	def mem(self,cmess,s):
		if len(cmess.split(" ")) == 1:
			s.sendall('Error, try: MEM <Channel>')
		else:
			channel_name = (cmess.split(" ")[1]).split("\n")[0]
			check = None
			for i in self.channels:
				if i.name == channel_name:
					check = i
			#this means the desired channel doesn't exist
			if check is None:
				s.sendall('%s does not exist' % channel_name)
			else:
				list_users = ''
				flag = 0
				
				for i in self.users:
					if check.retuser(i[1]) != None:
						list_users = list_users + i[0] + '\n'
						flag = 1
				#this means there are no users in the desired channel
				if flag == 0:
					s.sendall('No users in %s' % check.name)
				else:
					s.sendall('Users in ' + check.name + '\n' + list_users)

	#this command allows the client to leave a particulat channel
	def leave(self,cmess,s):
		#if only one arg given then client leaves all channels he/she is in. 
		if len(cmess.split(" ")) == 1:
			s.sendall('Leaving all channels')
			self.leaveall(s)
			addr = s.getpeername()
			print('(%s:%s) has left all channels' %addr)
		else:
			channel_name = (cmess.split(" ")[1]).split("\n")[0]
			check = None
			for i in self.channels:
				if i.name == channel_name:
					check = i
			#this means the channel client tried to leave doesn't exist
			if check == None:
				s.sendall('This channel does not exist')
			else:
				#this means the client tried to leave a channel he/she is not in
				if check.retuser(s) is None:
					s.sendall('Not Currently in %s' %check.name)
				else:
					addr = s.getpeername()
					for i in self.users:
						if i[1] == s:
							username = i[0]
					check.removeuser(username,s)
					self.removinguser(check,s)
					print('(%s:%s) has left '%addr + check.name)
	
	#this command allows the client to send a message to everyone in the chosen channel
	def mess(self,cmess,s):
		if len(cmess.split(" ")) < 3:
			s.sendall('Error, try: MESS <Channel> <message>')
		else:
			channel_name = (cmess.split(" ")[1]).split("\n")[0]
			check = None
			for i in self.channels:
				if i.name == channel_name:
					check = i
			#this means the chosen channel doesn't exist
			if check == None:
				s.sendall('This channel does not exist')
			else:
				#this means the user is not in the channel he/she is trying to chat in
				if check.retuser(s) is None:
					s.sendall('Not Currently in %s' %check.name)
				else:
					message = self.parse(cmess,'MESS')
					message = self.parse(message,channel_name)
					for i in self.users:
						if i[1] == s:
							username = i[0]
					for i in check.chan_users:
						if s != i:
							i.sendall(username + ' #' + check.name + ': ' + message)

	#this command allows the client to private message to another client.
	def whisper(self,cmess,s):
		if len(cmess.split(" ")) < 3:
			s.sendall('Error, try: WHISPER <username> <message>')
		else:
			for i in self.users:
				if i[1] == s:
					username = i[0]
			to_user = (cmess.split(" ")[1]).split("\n")[0]
			rsocket = None
			for i in self.users:
				if i[0] == to_user:
					rsocket = i[1]

			#this means the client tried to private message himself/herself.
			if username == to_user:
				s.sendall('Unable to private message self')
			#this means the client doesn't exist to whisper to.
			elif rsocket is None:
				s.sendall('User %s does not exist'%to_user)
			else:
				message = self.parse(cmess,'WHISPER')
				message = self.parse(message,to_user)
				rsocket.sendall(username + ' Whispers: ' + message)

	#this command allows the client to recieve a file from the server (file transfer) 
	def get(self,cmess,s):
		if len(cmess.split(" ")) == 1:
			s.sendall('Error, try: GET <filename>')
		else:
			file_name = (cmess.split(" ")[1]).split("\n")[0]
			if len(file_name.split(".")) > 1:
				extension = (file_name.split(".")[1])
			flag = 0
			try:
				f = open(file_name,'rb')
			except IOError:
				s.sendall('File does not exist')
				flag = 1
			
			if flag == 0:
				addr = s.getpeername()
				print('Sending ' + file_name + ' file to (%s:%s)'%addr)
				c = f.read(1024)
				while (c):
					s.sendall('#$% '+ extension + ' ' + c)
					c = f.read(1024)
				f.close()		

	#this is a helper parse function that will subtract string two from one.
	def parse(self,one,two):
		return "".join(one.rsplit(two))

	#this is a helper function that will add user and channel to user_channel map list.
	def addinguser(self, channel, ssocket):
			self.user_channel.append((ssocket,channel))

	#this is a helper function that will remove user and channel from user_channel map list.	
	def removinguser(self, channel, ssocket):
		for x in self.user_channel:
			if x[0] == ssocket and x[1] == channel:
				self.user_channel.remove(x)

	#this is a helper function that allows the client to disconnect from the server gracefully
	def disconnect(self, ssocket):
		addr = ssocket.getpeername()
		self.leaveall(ssocket)
		for i in self.users:
			if i[1] == ssocket:
				self.users.remove(i)
		ssocket.shutdown(socket.SHUT_RDWR)
		ssocket.close
		self.getdes.remove(ssocket)
		print ('Client is leaving server (%s:%s)' % addr)	

	#this is a helper function that removes a client from all channels and updates the data structures.
	def leaveall(self, ssocket):
		for y in self.users:
			if y[1] == ssocket:
				username = y[0]
		for i in self.user_channel:
			if i[0] == ssocket:
				i[1].removeuser(username,ssocket)
		self.user_channel[:] = [i for i in self.user_channel if not i[0] == ssocket]



#create server object and run the server forever.
chat = server()
while True:
	chat.start()	
