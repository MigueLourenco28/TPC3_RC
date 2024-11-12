import socket
import sys
import os
import pickle
import random
import time

def sendMovie( fileName, cHost, cUDPport, sessionID):
	dest = (cHost, cUDPport)
	su = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# to guarantee that the send buffer has space for the biggest JPEG files
	su.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32000) 
	frameNo = 1
	fr = open(fileName, 'rb')
		
	while True:
		dat = fr.read(5)
		if len(dat) == 0: 
				return
		else:
			imageLen = int(dat)
			dat=fr.read(imageLen)
			if frameNo % 100 == 0:
				print(f'nseq={frameNo} JPEG file size = {len(dat)}')
			#-----------Added-----------#
			# TODO students shouldbuild the RTP header
			# TODO and replace the sendto of byte array dat
			# TODO by the concatenation of the RTP header with byte array dat
			
			# Build RTP header
			header = bytearray(12)

			header[0] = 0b10000000 # Versão 2, P=0, X=0, CC=0
			header[1] = 26		   # PT = 26 para MJPEG
			header[2] = (frameNo >> 8) & 0xFF
			header[3] = frameNo & 0xFF

			timestamp = int(time.time() * 1000)

			header[4] = (timestamp >> 24) & 0xFF
			header[5] = (timestamp >> 16) & 0xFF
			header[6] = (timestamp >> 8) & 0xFF
			header[7] = timestamp & 0xFF
			header[8] = (sessionID >> 24) & 0xFF
			header[9] = (sessionID >> 16) & 0xFF
			header[10] = (sessionID >> 8) & 0xFF
			header[11] = sessionID & 0xFF
			#-----------Added-----------#
			#-----------Changed-----------#
			su.sendto(header + dat, dest)
			#-----------Changed-----------#
			time.sleep(0.05)  # one image every 50 ms
			frameNo = frameNo+1


def handleClient( clientHost, sock):
	# receive fileName and UDP port
	# reply with random sessionID, -1 if file not available

	nreq = sock.recv(128)
	req = pickle.loads(nreq)
	fileName = req[1]
	clientUDPPort = req[0]
	if not os.path.exists(fileName):
		rep=(-1,)
		sock.send(pickle.dumps(rep))
		return
	
	sid = random.randint(0,4000000)
	rep=(sid,)
	sock.send(pickle.dumps(rep))
	#wait for ack from client
	rep = sock.recv(128)
	if rep.decode() == "Go":
		sock.close()
		sendMovie( fileName, clientHost, clientUDPPort, sid)

if __name__ == "__main__":
    # python Server.py serverTCPPort
	if len(sys.argv)!=2:
		print("Usage: python3 Client.py  ServerTCPControlPort")
		sys.exit(1)
	else:
		serverTCPControlPort = int(sys.argv[1])
		st = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			st.bind(("0.0.0.0", serverTCPControlPort))
		except socket.error as e:
			print(f"Error binding TCP server socket: {e}")
			st.close()
			sys.exit(2)
		st.listen(1)
		while True:
			print("Waiting for client")
			try:
				sa, end = st.accept()
			except KeyboardInterrupt:
				print("server exiting")
				st.close()
				sys.exit(0)
			print(f"Handling client connecting from {end}")
			handleClient( end[0], sa )


