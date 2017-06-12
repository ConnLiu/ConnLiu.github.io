from tkinter import *
from tkinter import messagebox
import sys, getopt, os, time, socket, struct, select, random, asyncore

def checkSum(data):
	Sum = 0
	size = int(len(data)/2)*2
	count = 0
	while count+1 < size:
		value = (data[count])*256 + (data[count+1])
		Sum = Sum + value
		if Sum > 0xffff:
			Sum = Sum & 0xffff
			Sum = Sum + 1
		count = count + 2
	if size < len(data):
		Sum = Sum + (data[size])*256
		if Sum > 0xffff:
			Sum = Sum & 0xffff
			Sum = Sum + 1
	return (~Sum) & 0xffff
class Application(Frame):
	
	def ping(self, s, ip, ID, seq):
		# icmp + data
		nowTime = struct.pack('!d',time.time())
		dataSize = 55
		data = (dataSize-8) * b'\x01'
		data = nowTime + data
		icmpHead = struct.pack('!BBHHH', 8, 0, 0, ID, seq)

		check = checkSum(icmpHead + data)
		icmpHead = struct.pack('!BBHHH', 8, 0, check, ID, seq)
		#ipPacket = ipHead + icmpHead + data
		icmp = icmpHead + data
		s.sendto(icmp,(ip,1))

	def receivePing(self, s, timeout, ID, seq, ip):
		timeLeft = timeout
		while True:
			beginSelect = time.time()
			whatReady = select.select([s], [], [], timeLeft)
			howLongInSelect = time.time() - beginSelect
			if whatReady[0] == []: #timeout
				return 
		
			timeReceived = time.time()
			recPacket, addr = s.recvfrom(1024)
			icmpHead = recPacket[20:28]
			typ, code, check, packetId, sequence = struct.unpack("!bbHHH", icmpHead)
			if typ == 0 and packetId == ID and sequence == seq:
				timeSent = struct.unpack('!d', recPacket[28:28+8])[0]
				#ip = struct.unpack('!4p', recPacket[16:20])[0].decode('utf-8')
				ttl = struct.unpack('!B', recPacket[8:9])[0]
				delay = timeReceived - timeSent
				print('64 bytes from',ip,': icmp_seq=',seq,'ttl=',ttl,'time=%.2f'%(delay*1000),'ms')
				
				def trans(s):
    					return "b'%s'" % ''.join(' %.2x' % x for x in s)
				tmp = "recPacke"+str(seq)+":\nIPHeader:"+trans(recPacket[0:20])+"END\n"
				self.t.insert(END,tmp)
				tmp = "icmpHeader:" + trans(icmpHead) + "END\n"
				self.t.insert(END,tmp)
				tmp = "data:" + trans(recPacket[28:]) + "END\n"
				self.t.insert(END,tmp)
				return delay
			timeLeft = timeLeft - howLongInSelect
			if timeLeft <= 0:
				return 

	def icmp_ping(self, dns, count, timeout):
		ip = socket.gethostbyname(dns)		
		print ('ping',dns,'(', ip,')','56(84) bytes of data')
		# ip4 ; icmp (root) ; 
		icmp = socket.getprotobyname("icmp")
		s = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
		lossCnt = 0
		beginTime = time.time()
		for i in range(1,count+1):
			ID = os.getpid() & 0xffff
			self.ping(s, ip, ID, i)
		
			delay = self.receivePing(s, timeout, ID, i, ip)
			if delay == None:
				lossCnt = lossCnt + 1			
				print ('from',ip,': icmp_seq=',i,'Time to live exceeded')
		
		print ('--- ',dns,' ping statistics ---')
		print (count,'packets transmitted,',count-lossCnt,'received',lossCnt,'errors',(lossCnt/count*100),'% packet loss, time','%dms'%((time.time()-beginTime)*1000))
	

	def startping(self):
		f_handler=open('out.log', 'w')   
		sys.stdout=f_handler
		cmd = self.w.get().split()
		opts, args = getopt.getopt(cmd[1:], "hc:t:")
		if ( len(args) != 0 ):
			self.t.insert (INSERT,"Ping error, you should use ping like this:\n")
			self.t.insert (INSERT,"Usage: ./ping.py destination [-c count] [-t timeout] ")
			return
		dic = {'-c':4, '-t':1}
		for op, value in opts:
			if(value != ''):
				value = int(value)
				dic[op] = value

		try :
			self.icmp_ping( cmd[0], dic['-c'], dic['-t'])
		except socket.error as e:
			messagebox.showinfo("Error", "Input dns error!")
			
			return
		sys.stdout.flush()
		outfile = open('out.log')
		while True:
			line = outfile.readline()
			if not line:
				break
			self.mylist.insert(END,line)
		self.mylist.insert(END,'====================')
		self.mylist.insert(END,'')
		self.t.insert(END,'====================\n')
		self.t.insert(END,'\n')
		outfile.close()
	def clear(self):
		self.mylist.delete(0, self.mylist.size())	
		self.t.delete(0.0,END)

	def __init__(self, master=None):
		Frame.__init__(self,master)
		self.pack()
		self.createWidgets()
	def createWidgets(self):
		self.bottomframe = Frame(self)
		self.bottomframe.pack(side=BOTTOM)

		self.helloLabel = Label(self, text = 'Usage: ping destination [-c count] [-t timeout]')
		self.helloLabel.pack()
		self.w = Entry(self, bd=5)
		self.w.pack()

		self.scrollbar = Scrollbar(self)
		self.scrollbar.pack(side=RIGHT, fill=Y)
		
		self.mylist = Listbox(self, height=12, width=90, yscrollcommand = self.scrollbar.set )
		self.mylist.pack( side = LEFT, fill = BOTH )
		self.scrollbar.config(command = self.mylist.yview)
	
		self.t = Text(self.bottomframe, width=105, height=9)
		
		self.t.pack()
	
		self.startButton = Button(self.bottomframe, text='Start', command = self.startping)
		self.startButton.pack(side=LEFT)

		self.clrButton = Button(self.bottomframe, text='Clear', command = self.clear)
		self.clrButton.pack(side=LEFT)

		self.quitButton = Button(self.bottomframe, text='Quit', command = self.quit)
		self.quitButton.pack(side=RIGHT)

		if os.geteuid() != 0:
			messagebox.showinfo("Error", "Ping procedure must run with sudo")
			sys.exit()
	

if __name__ == '__main__':
	
	app = Application()
	app.master.title('ping procedure')	
	app.mainloop()
