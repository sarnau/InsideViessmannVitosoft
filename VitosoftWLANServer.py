#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import serial
import time
import binascii

# This script can run on e.g. a Raspberry Pi that is configured to be configured as a WLAN
# access point, while the Ethernet port is configured as a started network port.

# It is just an example and does not work reliably. Feel free to improve it.

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('10.45.161.1', 45317)
print >>sys.stderr, 'starting up on %s:%s' % server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=4800,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS
)

print("SEND EOT")
ser.write(binascii.unhexlify('04'))
if ser.read(1)==binascii.unhexlify('05'):
  ser.write(binascii.unhexlify('160000'))
  print(binascii.hexlify(ser.read(1)))
print("START")

while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()

    try:
        print >>sys.stderr, 'connection from', client_address

        while True:
            data = connection.recv(8)
            print >>sys.stderr, 'OptoLink > %s' % " ".join("{:02x}".format(ord(c)) for c in data)
            if data:
#                print >>sys.stderr, 'serial send'
                ser.write(data)
#                print >>sys.stderr, 'serial wait'
                time.sleep(1/(4800/12)*1.2)
                out = ''
                while ser.in_waiting > 0:
                    out += ser.read(1)
                    time.sleep(1/(4800/12)*1.2)
                if out != '':
                    print >>sys.stderr, 'OptoLink < %s' % " ".join("{:02x}".format(ord(c)) for c in out)
                    connection.sendall(out)
            else:
                print >>sys.stderr, 'no more data from', client_address
                break
    finally:
        # Clean up the connection
        connection.close()
