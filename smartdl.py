#!/usr/bin/env python
# -*- coding: utf-8 -*-

#       Copyright 2012 AmirH Hassaneini <mytechmix@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import sys,os
import socket
import math
import time
import threading

class HTTPzer: # HTTP response analyzer!
	def __init__(self, data=""):
		self.data = data
	def getHeader(self, header):
		hedz = self.data.replace("\r\n", " `").split(" ")
		for i in range(len(hedz)):
			if hedz[i] == ("`" + header + ":"):
				return hedz[i+1]
	def getBody(self):
		bodyPos = self.data.find("\r\n\r\n")
		if  bodyPos == -1:
			return self.data
		else:
			return self.data[bodyPos+4:]
	def getStatusCode(self):
		return self.data.split(" ")[1]
				
class HTTPker: # HTTP request maker!
	def __init__(self, method="GET", host="", object=""):
		self.headers = ""
		self.head = method + " " + object + " HTTP/1.1\r\n"
		self.addHeader("Host", host)
		
	def getData(self):
		return (self.head + self.headers + "\r\n")
		
	def setMethod(self, method):
		self.method = method
		
	def setHost(self, host):
		self.host = host
		
	def addHeader(self, header, value):
		self.headers = self.headers + header + ": " + value + "\r\n"

class MySocket:
	def __init__(self):
		self.port = 0
		self.host = ""
		self.serverMode = True
		
	def create(self):
		pass
		
	def connectTo(self, host, port):
		self.serverMode = False
		self.port = port
		self.host = socket.gethostbyname(host)
		self.clientSockFD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.clientSockFD.connect((self.host,self.port))
	
	def reConnect(self):
		if not (self.host == ""):
			self.connectTo(self.host, self.port)
			
	def send(self, data):
		if self.serverMode == False:
			self.clientSockFD.send(data)
			
	def recieve(self, byte=1024):
		if self.serverMode == False:
			return self.clientSockFD.recv(byte)
		else:
			return self.serverSockFD.recv(byte)
			
	def close(self):
		if self.serverMode == False:
			self.clientSockFD.close()
		else:
			self.serverSockFD.close()

def downloadToFile(*args):
	fileHost = args[0]
	fileObject = args[1]
	fileName = args[2]
	resumeSupport = args[3]
	range1 = args[4]
	range2 = args[5]
	pSize = int(range2) - int(range1)

	partSock = MySocket()
	partSock.connectTo(fileHost, 80)
	hed = HTTPker("GET", fileHost, fileObject)
	if resumeSupport == True:
		hed.addHeader("Range", "bytes=" + range1 + "-" + range2)
	partSock.send(hed.getData())
	
	totRecv = 0
	prog = 0
	fileOut = open(fileName, "wb+")
	while not prog==1000:
		data = partSock.recieve(pSize)
		mData = HTTPzer(data)
		totRecv += len(mData.getBody())
		fileOut.write(mData.getBody())
		prog = (totRecv * 1000) / pSize
		print fileName + ": " + str(prog/10) + "%"
	fileOut.close()
	

def smartDownload(fileUrl, partCount=4):
	
	partCount = int(partCount)
	if fileUrl.find("http://") == -1:
		print "ERR: Only HTTP supported"
		return
	fileUrl = fileUrl.replace("http://", "")
	firstSlashPos = fileUrl.find("/")
	lastSlashPos = len(fileUrl) - fileUrl[::-1].find("/")
	fileHost = fileUrl[:firstSlashPos]
	fileObject = fileUrl[firstSlashPos:]
	fileName = fileUrl[lastSlashPos:]
	
	measureS = MySocket()
	measureS.connectTo(fileHost, 80)
	req = HTTPker("GET", fileHost, fileObject)
	req.addHeader("Connection", "close")
	measureS.send(req.getData())
	resp = HTTPzer(measureS.recieve())
	measureS.close()
	if resp.getStatusCode() == "200":
		fileLength = resp.getHeader("Content-Length")
	else:
		print "ERR: File not avalible."
		return
	
	measureS.reConnect()
	req.addHeader("Range", "bytes= 0-")
	measureS.send(req.getData())
	statusCode = HTTPzer(measureS.recieve()).getStatusCode()
	measureS.close()
	if statusCode == "206":
		resumeSupport = True
	else:
		resumeSupport = False
		partCount = 1
	
	partSize = int(math.floor(int(fileLength) / partCount))
	for i in range(partCount):
		startRange = str(i*partSize)
		if (i+1) == partCount:
			endRange = fileLength	
		else:
			endRange = str((i+1)*partSize-1)
		dlArgs = (fileHost, fileObject, fileName+".part_"+str(i+1), resumeSupport, startRange, endRange)
		threading.Thread(target = downloadToFile, args=dlArgs).start()
	
	while threading.activeCount()>1:
		time.sleep(1)
		
	finalFile = open(fileName, "wb+")
	for i in range(partCount):
		finalFile.write(open(fileName+".part_"+str(i+1), "rb").read())
		os.remove(fileName+".part_"+str(i+1))
	finalFile.close()
	
	print "done!"
	return 0

if __name__ == '__main__':
	if len(sys.argv)>2:
		smartDownload(sys.argv[1], sys.argv[2])
	elif len(sys.argv) == 2:
		smartDownload(sys.argv[1])
	else:
		print "Please pass me a URL!"
