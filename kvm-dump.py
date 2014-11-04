#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# KVM Memory Dumper
#
# November 3rd, 2014
# Written in one shot by Patrick Marlier and Raphaël P. Barazzutti

import re, sys, textwrap

class KVMMemDumper:

	class MemBlock:
		blockSize = 64 * 1024
		
		def __init__(self, outer, start, end):
			self.outer = outer
			self.start = start
			self.end = end

		def size(self):
			return self.end - self.start

		def dump(self, start, length):
			try:
				mem = open("/proc/" + self.outer.pid + "/mem", 'r')
				mem.seek(self.start + start)
				remaining = length 

				if(start < 0 or length < 0):
					raise RuntimeError("Start position and length are positive values")			

				if(start + length > self.size()):
					raise RuntimeError("Trying to read to far")
			
				while(remaining>0):
					toRead = min(self.blockSize, remaining)
					chunk = mem.read(toRead)
					remaining -= toRead
					sys.stdout.write(chunk)

				mem.close()
			except:				
				raise RuntimeError("Error reading memory of process " + self.outer.pid)

	def __init__(self, pid):
		self.pid = pid
		self.bestBlock = self.MemBlock(self, 0, 0)
		try:
			mapsFile = open("/proc/"+ self.pid+"/maps", 'r')

			# the memory allocated for the VM is read, write, private (cow) and not executable
			rx = re.compile('([0-9a-f]+)-([0-9a-f]+) rw-p')

			# Searching for the biggest allocated memory area (KVM itself doesn't need
			# huge areas, we expect that the biggest one is for the VM itself)			
			for line in mapsFile.readlines():
				r=rx.match(line)
				if(r):
					curBlock = self.MemBlock(self, int(r.group(1), 16), int(r.group(2), 16))
					if(curBlock.size() > self.bestBlock.size()):
						self.bestBlock = curBlock
			mapsFile.close()
		except Exception as e:
			raise RuntimeError("Error  retrieving memory mapping of process " + self.pid)
	
	def dumpVmMemAll(self):
		self.dumpVmMem(0, self.bestBlock.size())

	def dumpVmMem(self, start, length):
		self.bestBlock.dump(start, length)
		


if(len(sys.argv) in [2, 4]):
	kvmMemDumper = KVMMemDumper(sys.argv[1])

	if(len(sys.argv) == 2):
		kvmMemDumper.dumpVmMemAll()
	else:
		kvmMemDumper.dumpVmMem(int(sys.argv[2]), int(sys.argv[3]))
else:
	print >> sys.stderr,(textwrap.dedent(
			"""
			Usage:
			./kvmDump <PID>
			to dump the whole memory of the KVM process

			./kvmDump <PID> <start> <length>
			to dump a part of the memory of the KVM process

			- PID:    Process Identifier
			- start:  Start position in bytes
			- length: Length of the memory area to read
			"""
	))

	



