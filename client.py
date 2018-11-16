import sys
import select
import socket

#this class is the chat client and will essentially set up and run the client for the IRC program
class chat:
	#chat class is initialized by connecting the client socket to internet and TCP connection. 
	def __init__(self,username,port,host):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.settimeout(2)
		self.username = username
		#attempt to connect client socket with server and pass in the registered username.
		try:
			self.client_socket.connect((host,port))
		except:
			print('Error, not able to connect to server')
			sys.exit()

		try:
			self.client_socket.send("REG " +username+"\n")
		except:
			print('Unable to register to server')
			sys.exit()

		print('You are connected to server')
		self.getdes = [sys.stdin, self.client_socket]	#store the client socket and sys.stdin info

	#This function will run continously untill a disconnect from server. 
	def start(self):
		read, write, error = select.select(self.getdes,[],[])	#block until socket ready and put into read
		for s in read:
			#if socket in read is the client then it recieves info from the server
			if s == self.client_socket:
				info = s.recv(4096)
				if not info:
					print('You are disconnected from server\n')
					sys.exit()
				#this branch taken if client wants file transfer
				elif (info.split(" ")[0].split("\n")[0]) == '#$%':
					extension = (info.split(" ")[1]).split("\n")[0]
					data = self.parse(info,'#$% ')	
					data = self.parse(data,(extension + ' '))
					with open(('Transfered_file.'+ extension), 'wb') as f:
						f.write(data)
					f.close()
					print('Recieved the file')
				#information written out to stdout	
				else:
					sys.stdout.write(info)
					print('')
			#This branch taken if recieve sys.stdin from user and will send that to the server.
			else:
				clientmess = sys.stdin.readline()
				self.client_socket.send(clientmess)
	
	#helper function used for parsing. It will subtract string two from one.
	def parse(self,one,two):
		return "".join(one.rsplit(two))


#Check if there are less than 4 args given in command prompt.
if(len(sys.argv) < 4):
	print ('Connect to server with: python client.py username hostname port')
	sys.exit()
username = sys.argv[1]
hostname = sys.argv[2]
port = int(sys.argv[3])

#create the chat class and begin running the client.
client = chat(username,port,hostname)
while True:
	client.start()
