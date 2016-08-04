#!/usr/bin/python
# -*- coding: utf-8 -*-

import serial
import graphitesend, time

g = graphitesend.init(graphite_server='127.0.0.1', group='mppt', prefix='')


class vedirect:

    def __init__(self, serialport):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, 19200, timeout=10)
        self.header1 = '\r'
        self.header2 = '\n'
        self.delimiter = '\t'
        self.key = ''
        self.value = ''
        self.bytes_sum = 0
        self.state = self.WAIT_HEADER
        self.dict = {}


    (WAIT_HEADER, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(4)

    def input(self, byte):
        if self.state == self.WAIT_HEADER:
            self.bytes_sum += ord(byte)
            if byte == self.header1:
                self.state = self.WAIT_HEADER
            elif byte == self.header2:
                self.state = self.IN_KEY

            return None
        elif self.state == self.IN_KEY:
            self.bytes_sum += ord(byte)
            if byte == self.delimiter:
                if self.key == 'Checksum':
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += byte
            return None
        elif self.state == self.IN_VALUE:
            self.bytes_sum += ord(byte)
            if byte == self.header1:
                self.state = self.WAIT_HEADER
                if self.key[0] != ':':
                    self.dict[self.key] = self.value
                self.key = ''
                self.value = ''
            else:
                self.value += byte
            return None
        elif self.state == self.IN_CHECKSUM:
            self.bytes_sum += ord(byte)
            self.key = ''
            self.value = ''
            self.state = self.WAIT_HEADER
            if self.bytes_sum % 256 == 0:
                self.bytes_sum = 0
                return self.dict
            else:
                self.bytes_sum = 0

        else:
            raise AssertionError()

    def read_data(self):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)

    def read_data_single(self):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)
            if packet != None:
                return packet


    def read_data_callback(self, callbackFunction):
        while True:
            byte = self.ser.read(1)
            packet = self.input(byte)
            if packet != None:
                callbackFunction(packet)



def print_data_callback(data):

    # See https://github.com/fab13n/elorn_energy/blob/master/src/victron/mppt.lua
    # for field description.

    out = dict()

    for k in ['V', 'I', 'VPV']:
        out[k] = float(data[k])/1000

    for k in ['H19', 'H20', 'H22']:
        out[k] = float(data[k])/100

    for k in ['CS', 'ERR', 'H21', 'H23', 'P']:
        out[k] = data[k]

    g.send_dict(out)
    time.sleep(1)


if __name__ == '__main__':
    ve = vedirect('/dev/ttyUSB0')
    ve.read_data_callback(print_data_callback)
    #print(ve.read_data_single())


