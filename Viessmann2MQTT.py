#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import os
import serial
import binascii
import enum
from datetime import datetime
import struct
import paho.mqtt.client as mqtt
import logging
import logging.handlers

logging.getLogger().setLevel('DEBUG')
logging.info('Starting Viessmann2mqtt')

MQTT_USER = "mqtt username"
MQTT_PASSWORD = "mqtt password"
MQTT_SERVER = 'mqtt server name or IP'
MQTT_TOPIC = 'Viessmann'

if not MQTT_TOPIC.endswith("/"):
    MQTT_TOPIC+="/"

scriptPathAndName = None
lastModDate = None
def wait100ms():
    global scriptPathAndName,lastModDate
    if not scriptPathAndName:
        scriptPathAndName = os.path.realpath(__file__)
    if not lastModDate:
        lastModDate = time.ctime(os.path.getmtime(scriptPathAndName))
    if lastModDate != time.ctime(os.path.getmtime(scriptPathAndName)):
        print ('#### RELAUNCH ####')
        os.execv(sys.argv[0], sys.argv)
        sys.exit(0)
    time.sleep(0.1)

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=4800, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS)

def connecthandler(mqc,userdata,flags,rc):
    logging.info("Connected to MQTT broker with rc=%d" % (rc))
    mqc.publish(MQTT_TOPIC+"connected",True,qos=1,retain=True)

def disconnecthandler(mqc,userdata,rc):
    logging.warning("Disconnected from MQTT broker with rc=%d" % (rc))


def startCommunication():
    #print("SEND EOT")
    ser.flush()
    ser.write(binascii.unhexlify('04'))
    sendStart = False
    t = 0
    while t < 3000:
        #print("... %.1fms" % (t*0.001))
        if ser.in_waiting:
            buf = ser.read()
            if len(buf) == 1:
                if buf[0] == 0x05:
                    #print("RECEIVED ENQ")
                    #print("SEND VS2_START_VS2")
                    ser.write(binascii.unhexlify('160000'))
                    sendStart = True
                    t = 0
                elif sendStart:
                    if buf[0] == 0x06: # VS2_ACK
                        #print("RECEIVED VS2_ACK")
                        return True
                    elif buf[0] == 0x15: # VS2_NACK
                        #print("RECEIVED VS2_NACK")
                        #print("SEND VS2_START_VS2")
                        ser.write(binascii.unhexlify('160000'))
                        sendStart = True
                        t = 0
                    else:
                        #print("RECEIVED %s" % binascii.hexlify(buf))
                        pass
            else:
                #print("RECEIVED %s" % binascii.hexlify(buf))
                pass
        wait100ms()
        t += 100
    return False

class ReceiveState(enum.IntEnum):
    unknown = 0
    ENQ = 1
    ACK = 2
    NACK = 3
class ProtocolIdentifier(enum.IntEnum):
    LDAP = 0
    RDAP = 0x10
class MessageIdentifier(enum.IntEnum):
    RequestMessage = 0
    ResponseMessage = 1
    UNACKDMessage = 2
    ErrorMessage = 3
class FunctionCodes(enum.IntEnum):
    undefined = 0
    Virtual_READ = 1
    Virtual_WRITE = 2
    Physical_READ = 3
    Physical_WRITE = 4
    EEPROM_READ = 5
    EEPROM_WRITE = 6
    Remote_Procedure_Call = 7
    Virtual_MBUS = 33
    Virtual_MarktManager_READ = 34
    Virtual_MarktManager_WRITE = 35
    Virtual_WILO_READ = 36
    Virtual_WILO_WRITE = 37
    XRAM_READ = 49
    XRAM_WRITE = 50
    Port_READ = 51
    Port_WRITE = 52
    BE_READ = 53
    BE_WRITE = 54
    KMBUS_RAM_READ = 65
    KMBUS_EEPROM_READ = 67
    KBUS_DATAELEMENT_READ = 81
    KBUS_DATAELEMENT_WRITE = 82
    KBUS_DATABLOCK_READ = 83
    KBUS_DATABLOCK_WRITE = 84
    KBUS_TRANSPARENT_READ = 85
    KBUS_TRANSPARENT_WRITE = 86
    KBUS_INITIALISATION_READ = 87
    KBUS_INITIALISATION_WRITE = 88
    KBUS_EEPROM_LT_READ = 89
    KBUS_EEPROM_LT_WRITE = 90
    KBUS_CONTROL_WRITE = 91
    KBUS_MEMBERLIST_READ = 93
    KBUS_MEMBERLIST_WRITE = 94
    KBUS_VIRTUAL_READ = 95
    KBUS_VIRTUAL_WRITE = 96
    KBUS_DIRECT_READ = 97
    KBUS_DIRECT_WRITE = 98
    KBUS_INDIRECT_READ = 99
    KBUS_INDIRECT_WRITE = 100
    KBUS_GATEWAY_READ = 101
    KBUS_GATEWAY_WRITE = 102
    PROZESS_WRITE = 120
    PROZESS_READ = 123
    OT_Physical_Read = 180
    OT_Virtual_Read = 181
    OT_Physical_Write = 182
    OT_Virtual_Write = 183
    GFA_READ = 201
    GFA_WRITE = 202

class VS2Message():
    protocol = ProtocolIdentifier.LDAP
    identifier = MessageIdentifier.RequestMessage
    Command = FunctionCodes.undefined
    ADDR = 0
    Data = bytes()
    msgBytes = bytes()

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self.msgBytes = args[0]
            #print("VS2Message(%s)" % binascii.hexlify(self.msgBytes))
            self.protocol = ProtocolIdentifier(self.msgBytes[0] & 0xF0)
            self.identifier = MessageIdentifier(self.msgBytes[0] & 0x0F)
            self.Command = FunctionCodes(self.msgBytes[1])
            self.ADDR = (self.msgBytes[2] << 8) + self.msgBytes[3]
            self.BlockSize = self.msgBytes[4]
            self.Data = self.msgBytes[5:]
        else:
            self.protocol = args[0]
            self.identifier = args[1]
            self.Command = args[2]
            self.ADDR = args[3]
            self.BlockSize = args[4]
            if len(args) > 5:
                self.Data = args[5]
            else:
                self.Data = None

            buf = bytearray([self.protocol.value | self.identifier.value, self.Command.value, self.ADDR >> 8, self.ADDR & 0xFF, self.BlockSize])
            if self.Data:
                buf += bytearray(self.Data)
            buf = bytearray([0x41, len(buf)]) + buf
            buf = buf + bytearray([sum(buf[1:]) & 0xFF])
            self.msgBytes = bytes(buf)
            #print("VS2Message(%s)" % binascii.hexlify(self.msgBytes))

    def __str__(self):
        if self.Data:
            str = '%s' % self.Data.hex()
        else:
            str = ''
        return f'%s %s %s 0x%04x %d:%s' % (self.protocol, self.identifier, self.Command, self.ADDR, self.BlockSize, str)

def sendVS2Message(message):
    #print("SEND %s" % binascii.hexlify(message.msgBytes))
    ser.write(message.msgBytes)
    t = 0
    buf = None
    receiveStatus = ReceiveState.unknown
    while t < 3000:
        #print("... %.1fms" % (t*0.001))
        if ser.in_waiting:
            if buf == None:
                buf = ser.read(ser.in_waiting)
            else:
                buf += ser.read(ser.in_waiting)
            if len(buf):
                if buf[0] == 0x06: # VS2_ACK
                    if receiveStatus != ReceiveState.ACK:
                        #print("RECEIVED VS2_ACK")
                        pass
                    receiveStatus = ReceiveState.ACK
                elif buf[0] == 0x15: # VS2_NACK
                    if receiveStatus != ReceiveState.NACK:
                        #print("RECEIVED VS2_NACK")
                        pass
                    receiveStatus = ReceiveState.NACK
                if len(buf) > 1:
                    if receiveStatus == ReceiveState.NACK:
                        if buf[1] == 0x06: # VS2_ACK
                            buf = buf[1:]
                            receiveStatus = ReceiveState.ACK
                        elif buf[1] == 0x15: # VS2_NACK
                            buf = buf[1:]
                    if len(buf) > 1:
                        if receiveStatus != ReceiveState.ACK and receiveStatus != ReceiveState.NACK:
                            break # unknown state
                        #print("RECEIVED %s" % binascii.hexlify(buf))
                        if len(buf) > 3 and buf[1] == 0x41 and len(buf) == 1 + buf[2] + 3 and (sum(buf[2:-1]) & 0xff) == buf[-1]:
                            msg = None
                            if buf[0] == 0x06: # VS2_ACK
                                msg = VS2Message(buf[3:-1])
                            ser.write(binascii.unhexlify('06')) # VS2_ACK
                            return msg
        wait100ms()
        t += 100
    return None

commStarted = False

def errorcode(errorcode):
    errorcode_VScotHO1_72 = {
        0x00: "Anlage ohne Fehler",
        0x0F: "Wartung durchführen",
        0x10: "Kurzschluss Außentemperatursensor",
        0x18: "Unterbrechung Außentemperatursensor",
        0x19: "Fehler externer Außentemperatursensor (Anschlusserweiterung ATS1)",
        0x1D: "Störung Volumenstromsensor (STRS1)",
        0x1E: "Störung Volumenstromsensor (STRS1)",
        0x1F: "Störung Volumenstromsensor (STRS1)",
        0x20: "Kurzschluss Vorlaufsensor Anlage",
        0x28: "Unterbrechung Vorlaufsensor Anlage",
        0x30: "Kurzschluss Kesseltemperatursensor",
        0x38: "Unterbrechung Kesseltemperatursensor",
        0x40: "Kurzschluss Vorlaufsensor HK2",
        0x41: "Rücklauftemperatur HK2 Kurzschluss",
        0x44: "Kurzschluss Vorlaufsensor HK3",
        0x45: "Rücklauftemperatur HK3 Kurzschluss",
        0x48: "Unterbrechung Vorlaufsensor HK2",
        0x49: "Rücklauftemperatur HK2 Unterbrechung",
        0x4C: "Unterbrechung Vorlaufsensor HK3",
        0x4D: "Rücklauftemperatur HK3 Unterbrechung",
        0x50: "Kurzschluss Speichertemperatursensor / Komfortsensor / Ladesensor",
        0x51: "Kurzschluss Auslauftemperatursensor",
        0x58: "Unterbrechung Speichertemperatursensor/ Komfortsensor/ Ladesensor",
        0x59: "Unterbrechung Auslauftemperatursensor",
        0x90: "Solarmodul: Kurzschluss Sensor 7",
        0x91: "Solarmodul: Kurzschluss Sensor 10",
        0x92: "Solarregelung: Kurzschluss Kollektortemp.Sensor",
        0x93: "Solarregelung: Kurzschluss Kollektorrücklauf-Sensor",
        0x94: "Solarregelung: Kurzschluss Speichertemp.Sensor",
        0x98: "Solarmodul: Unterbrechung Sensor 7",
        0x99: "Solarmodul: Unterbrechung Sensor 10",
        0x9A: "Solar: Unterbrech. Kollektortemp.Sensor",
        0x9B: "Vitosolic: Unterbrech. Kollektorrücklauf",
        0x9C: "Solar: Unterbrech. Speichertemp.Sensor",
        0x9E: "Solarmodul: Delta-T Überwachung",
        0x9F: "Solarregelung: allgemeiner Fehler ",
        0xA2: "Fehler niedriger Wasserdruck Regelung",
        0xA3: "Abgastemperatursensor gesteckt",
        0xA4: "Überschreitung Anlagenmaximaldruck",
        0xA6: "Fehler Fremdstromanode nicht in Ordnung",
        0xA7: "Fehler Uhrenbaustein Bedienteil ",
        0xA8: "Interne Pumpe meldet Luft",
        0xA9: "Interne Pumpe blockiert",
        0xB0: "Kurzschluss Abgastemperatursensor",
        0xB1: "Fehler Bedienteil",
        0xB4: "interner Fehler Temperaturmessung",
        0xB5: "interner Fehler EEPROM",
        0xB7: "Kesselcodierkarte falsch/fehlerhaft",
        0xB8: "Unterbrechung Abgastemperatursensor",
        0xB9: "Fehlerhafte Übertragung Codiersteckerdaten",
        0xBA: "Kommunikationsfehler Mischer HK2",
        0xBB: "Kommunikationsfehler Mischer HK3",
        0xBC: "Fehler Fernbedienung HK1",
        0xBD: "Fehler Fernbedienung HK2",
        0xBE: "Fehler Fernbedienung HK3",
        0xBF: "LON-Modul falsch/fehlerhaft",
        0xC1: "Kommunikationsfehler Anschl.Erw. EA1",
        0xC2: "Kommunikationsfehler Solarregelung",
        0xC3: "Kommunikationsfehler Anschl.Erw. AM1",
        0xC4: "Kommunikationsfehler Anschl.Erw. OT",
        0xC5: "Fehler Drehzahlgeregelte Pumpe - Interne Pumpe",
        0xC6: "Fehler Drehzahlgeregelte Pumpe Heizkreis 2",
        0xC7: "Fehler Drehzahlgeregelte Pumpe Heizkreis 1",
        0xC8: "Fehler Drehzahlgeregelte Pumpe Heizkreis 3",
        0xC9: "Komm.-fehler KM-Bus Gerät DAP1",
        0xCA: "Komm.-fehler KM-Bus Gerät DAP2",
        0xCD: "Kommunikationsfehler Vitocom 100",
        0xCE: "Kommunikationsfehler Anschlußerweiterung extern",
        0xCF: "Kommunikationsfehler LON-Modul",
        0xD1: "Brennerstörung",
        0xD6: "Störung Digitaler Eingang 1",
        0xD7: "Störung Digitaler Eingang 2",
        0xD8: "Störung Digitaler Eingang 3",
        0xDA: "Kurzschluss Raumtemperatursensor HK1",
        0xDB: "Kurzschluss Raumtemperatursensor HK2",
        0xDC: "Kurzschluss Raumtemperatursensor HK3",
        0xDD: "Unterbrechung Raumtemperatursensor HK1",
        0xDE: "Unterbrechung Raumtemperatursensor HK2",
        0xDF: "Unterbrechung Raumtemperatursensor HK3",
        0xE0: "Fehler externer Teilnehmer LON",
        0xE1: "SCOT Kalibrationswert Grenzverletzung O",
        0xE2: "Keine Kalibration wg mangelnder Strömung",
        0xE3: "Kalibrationsfehler thermisch",
        0xE4: "Fehler in Spannungsversorgung 24V - Feuerungsautomat",
        0xE5: "Fehler Flammenverstärker - Feuerungsautomat",
        0xE6: "Min. Luft-/Wasserdruck nicht erreicht",
        0xE7: "SCOT Kalibrationswert Grenzverletzung U",
        0xE8: "SCOT Ionisationssignal weicht ab",
        0xEA: "SCOT Kalibrationswert abw. von Vorgänger",
        0xEB: "SCOT Kalibration nicht ausgeführt",
        0xEC: "SCOT Ionisationssollwert fehlerhaft",
        0xED: "SCOT Systemfehler",
        0xEE: "Keine Flammbildung",
        0xEF: "Flammenausfall in Sicherheitszeit",
        0xF0: "Kommunikationsfehler zum Feuerungsatomat",
        0xF1: "Abgastemperaturbegrenzer ausgelöst",
        0xF2: "TB ausgelöst - Übertemperatur",
        0xF3: "Flammenvortäuschung",
        0xF4: "Keine Flammenbildung",
        0xF5: "Fehler Luftdruckwächter",
        0xF6: "Fehler Gasdruckschalter",
        0xF7: "Fehler Luftdruckschalter",
        0xF8: "Fehler Gasventil",
        0xF9: "Fehler Gebläse - Drehzahl nicht erreicht",
        0xFA: "Fehler Gebläse - Stillstand nicht erreicht",
        0xFB: "Flammenausfall im Betrieb",
        0xFC: "Fehler in der elektrischen Ansteuerung der Gasarmatur",
        0xFD: "Interner Fehler Feuerungsautomat",
        0xFE: "Vorwarnung Wartung fällig (Warnung) ",
        0xFF: "Fehler Feuerungsautomat ohne eigenen Fehlercode",
    }
    if errorcode in errorcode_VScotHO1_72:
        return errorcode_VScotHO1_72[errorcode]
    return 'errorcode_%02x' % errorcode

def DateTimeFromBCD(data, offset):
    # data[4+offset] == weekday, 0 = Monday
    return datetime.strptime('%02x%02x-%02x-%02x %02x:%02x:%02x' % (data[0+offset],data[1+offset],data[2+offset],data[3+offset],data[5+offset],data[6+offset],data[7+offset]), '%Y-%m-%d %H:%M:%S')

def PhaseDay(data):
    dayStrs = []
    for dayOffset in range(0,7):
        phases = []
        dateStr = ''
        for r in range(0,8):
            offs = dayOffset*8+r
            if offs >= len(data): # my Viessmann returns just 57 bytes on a 58 byte request
                bb = 0xff
            else:
                bb = data[dayOffset*8+r]
            hour = bb >> 3
            if hour >= 24:
                dateStr += '24:00'
            else:
                min = (bb & 7) * 10
                dateStr += '%02d:%02d' % (hour,min)
            if r & 1:
                phases.append(dateStr)
                dateStr = ''
            else:
                dateStr += '-'
        while phases[-1]=='24:00-24:00':
            del phases[-1]
        dayStrs.append('  '.join(phases))
    result = ''
    lastStr = None
    firstDay = 0
    currentDay = 0
    weekDayList = ['Mo','Di','Mi','Do','Fr','Sa','So']
    for weekDayStr in dayStrs:
        if lastStr == None:
            lastStr = weekDayStr
        elif lastStr != weekDayStr:
            result += '%s-%s:%s ' % (weekDayList[firstDay],weekDayList[currentDay],lastStr)
            firstDay = currentDay + 1
        currentDay += 1
    if currentDay != firstDay:
        result += '%s-%s:%s' % (weekDayList[firstDay],weekDayList[currentDay-1],lastStr)
    return result.strip()

eventTypeConversionFunctions = {
    'Mult2': (lambda data,offset: '%d' % (struct.unpack("<h", data[offset:offset+2])[0] * 2.0)),
    'Mult5': (lambda data,offset: '%d' % (struct.unpack("<h", data[offset:offset+2])[0] * 5.0)),
    'Mult10': (lambda data,offset: '%d' % (struct.unpack("<h", data[offset:offset+2])[0] * 10.0)),
    'Mult100': (lambda data,offset: '%d' % (struct.unpack("<h", data[offset:offset+2])[0] * 100.0)),
    'Div2': (lambda data,offset: '%.1f' % (struct.unpack("<h", data[offset:offset+2])[0] / 2.0)),
    'Div5': (lambda data,offset: '%.1f' % (struct.unpack("<h", data[offset:offset+2])[0] / 5.0)),
    'Div10': (lambda data,offset: '%.1f' % (struct.unpack("<h", data[offset:offset+2])[0] / 10.0)),
    'Div100': (lambda data,offset: '%.01f' % (struct.unpack("<h", data[offset:offset+2])[0] / 10.0)),
    'Sec2Hour': (lambda data,offset: '%.2f' % (struct.unpack("<i", data[offset:offset+4])[0] / 3600.0)),

     'Mult100_Int8': (lambda data,offset: '%d' % (data[offset] * 100)),
     'Int8': (lambda data,offset: '%d' % (data[offset])),
    'Int16': (lambda data,offset: '%d' % (struct.unpack("<h", data[offset:offset+2])[0])),
    'Int32': (lambda data,offset: '%d' % (struct.unpack("<i", data[offset:offset+4])[0])),
#    'Solar': (lambda data,offset: 'Heute:%d Wh, -1:%d Wh, -2:%d Wh, -3:%d Wh, -4:%d Wh, -5:%d Wh, -6:%d Wh, -7:%d Wh' % struct.unpack("<8i", data[offset:])),
    'Solar': (lambda data,offset: '%d;%d;%d;%d;%d;%d;%d;%d' % struct.unpack("<8i", data[offset:])),
    'FehlerHistory': (lambda data,offset: '"%s %s"' % (DateTimeFromBCD(data,offset+1), errorcode(data[offset]))),
    'PhaseType': (lambda data,offset: 'PhaseType(%s)' % PhaseDay(data[offset:])),
    'DatumUhrzeit': (lambda data,offset: DateTimeFromBCD(data,offset)),
}

readCmds = [
            { 'addr':0x00F8,'size':8, 'name':'ID' },
            { 'addr':0x088E,'size':8,'conv':'DatumUhrzeit', 'name':'Datum und Uhrzeit' },

            { 'addr':0x7700,'size':1, 'name':'(00) Heizkreis-Warmwasserschema' },
            { 'addr':0x7701,'size':1, 'name':'(01) Anlagentyp' },
            { 'addr':0x7754,'size':1, 'name':'(54) Solarregelung' },
            { 'addr':0x777F,'size':1, 'name':'(7F) Unterscheidung Einfamilienhaus - Mehrparteienhaus' },

            { 'addr':0x2000,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten HK A1M1' },
            { 'addr':0x2100,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten WW A1M1' },
            { 'addr':0x2200,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten ZP A1M1' },

            { 'addr':0x3000,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten M2' },
            { 'addr':0x3100,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten WW M2' },
            { 'addr':0x3200,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten ZP M2' },

            { 'addr':0x4000,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten M3' },
            { 'addr':0x4100,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten WW M3' },
            { 'addr':0x4200,'size':56,'conv':'PhaseType', 'name':'Schaltzeiten ZP M3' },

            { 'addr':0x7590+9*0,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 0' },
            { 'addr':0x7590+9*1,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 1' },
            { 'addr':0x7590+9*2,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 2' },
            { 'addr':0x7590+9*3,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 3' },
            { 'addr':0x7590+9*4,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 4' },
            { 'addr':0x7590+9*5,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 5' },
            { 'addr':0x7590+9*6,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 6' },
            { 'addr':0x7590+9*7,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 7' },
            { 'addr':0x7590+9*8,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 8' },
            { 'addr':0x7590+9*9,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 9' },
            { 'addr':0x7590+9*10,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 10' },
            { 'addr':0x7590+9*11,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 11' },
            { 'addr':0x7590+9*12,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 12' },
            { 'addr':0x7590+9*13,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 13' },
            { 'addr':0x7590+9*14,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 14' },
            { 'addr':0x7590+9*15,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 15' },
            { 'addr':0x7590+9*16,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 16' },
            { 'addr':0x7590+9*17,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 17' },
            { 'addr':0x7590+9*18,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 18' },
            { 'addr':0x7590+9*19,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie FA 19' },

            { 'addr':0x7561,'size':10, 'name':'ecnsysEventType-ErrorIndex' },
            { 'addr':0x7507+9*0,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 0' },
            { 'addr':0x7507+9*1,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 1' },
            { 'addr':0x7507+9*2,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 2' },
            { 'addr':0x7507+9*3,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 3' },
            { 'addr':0x7507+9*4,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 4' },
            { 'addr':0x7507+9*5,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 5' },
            { 'addr':0x7507+9*6,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 6' },
            { 'addr':0x7507+9*7,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 7' },
            { 'addr':0x7507+9*8,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 8' },
            { 'addr':0x7507+9*9,'size':9,'conv':'FehlerHistory', 'name':'Fehlerhistorie 9' },

            { 'addr':0xCF30,'size':32,'conv':'Solar', 'name':'Solarertrag' },
            { 'addr':0x6564,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Solar Kollektortemperatur' },
            { 'addr':0x6566,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Solar Speichertemperatur' },
            { 'addr':0x6560,'size':2,'conv':'Int16', 'unit':'kWh', 'name':'Solar Wärmemenge' },
            { 'addr':0x6568,'size':2,'conv':'Int16', 'unit':'Stunden', 'name':'Solar Betriebsstunden' },

            { 'addr':0x7700,'size':1, 'name':'Heizkreis-Warmwasserschema' },

#           { 'addr':0x47C5,'size':1, 'name':'Vorlauf - Minimalbegrenzung M3' },
#           { 'addr':0x47C6,'size':1, 'name':'Vorlauf - Maximalbegrenzung M3' },
#
            { 'addr':0x0800,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Aussentemperatur' },
            { 'addr':0x5525,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Aussentemperatur Tiefpass' },
            { 'addr':0x5527,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Aussentemperatur gedämpft' },
            { 'addr':0x0810,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Kesseltemperatur' },
            { 'addr':0x555A,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Kesselsolltemperatur' },
            { 'addr':0x0816,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Abgastemperatur' },
#           { 'addr':0x0810,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Vorlauftemperatur A1M1' },
            { 'addr':0x081A,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Gem. Vorlauftemperatur' },
            { 'addr':0x3900,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Vorlauftemperatur M2' },
            { 'addr':0x4900,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Vorlauftemperatur M3' },
            { 'addr':0x0812,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Temperatur Speicher Ladesensor Komfortsensor' },
            { 'addr':0x0814,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Auslauftemperatur' },
            { 'addr':0x0804,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Warmwassertemperatur Ist' },
            { 'addr':0x6500,'size':2,'conv':'Div10', 'unit':'℃', 'name':'Warmwassertemperatur Soll (effektiv)' },
            { 'addr':0xCF90,'size':20,'conv':'Div10','offset':6, 'unit':'℃', 'name':'Sensor 7' },
            { 'addr':0xCF90,'size':20,'conv':'Div10','offset':8, 'unit':'℃', 'name':'Sensor 10' },
            { 'addr':0x08A7,'size':4,'conv':'Sec2Hour', 'unit':'Stunden', 'name':'Brenner-Betriebsstunden' },
            { 'addr':0x088A,'size':4,'conv':'Int32', 'name':'Brennerstarts' },
            { 'addr':0x0C24,'size':2,'conv':'Int16', 'name':'Durchfluss Strömungssensor' },
            { 'addr':0x7660,'size':2,'conv':'Int16', 'unit':'%', 'name':'Interne Pumpe Drehzahl' },
            { 'addr':0x6300,'size':1,'conv':'Int8', 'unit':'℃', 'name':'Warmwasser-Solltemperatur' },
            { 'addr':0x5706,'size':1,'conv':'Int8', 'unit':'℃', 'name':'Kesselmaximal-Temperatur' },
          ]

try:
    mqc=mqtt.Client()
    mqc.username_pw_set(username=MQTT_USER,password=MQTT_PASSWORD)
    mqc.on_connect=connecthandler
    mqc.on_disconnect=disconnecthandler
    mqc.will_set(MQTT_TOPIC+"connected",False,qos=2,retain=True)
    mqc.disconnected =True
    mqc.connect(MQTT_SERVER,1883,60)
    mqc.loop_start()

    while True:
        if not commStarted:
            commStarted = startCommunication()
            if commStarted:
                #print("### connectionn estabilished")
                logging.info('### connectionn estabilished')
        if commStarted:
            resultJSON = '{'
            for cmd in readCmds:
                jsonname = cmd['name'].replace(' ','_').replace('-','_').replace('.','').replace('ä','ae').replace('Ä','Ae').replace('ö','oe').replace('Ö','Oe').replace('ü','ue').replace('Ü','Ue').replace('ß','ss').replace('(','').replace(')','')
                if 'cmd' in cmd:
                    fc = cmd['cmd']
                else:
                    fc = FunctionCodes.Virtual_READ
                msg = VS2Message(ProtocolIdentifier.LDAP, MessageIdentifier.RequestMessage, fc, cmd['addr'], cmd['size'])
                for _ in range(0,5): # 5 tries to read a parameter
                    rmsg = sendVS2Message(msg)
                    if rmsg:
                        break
                if not rmsg: # ignore, if no success
                    continue
                if rmsg.identifier != MessageIdentifier.ResponseMessage:
                    print("RECEIVED %s" % rmsg)
                    continue
                if 'conv' in cmd:
                    if 'offset' in cmd:
                        offset = cmd['offset']
                    else:
                        offset = 0
                    result = '%s' % eventTypeConversionFunctions[cmd['conv']](rmsg.Data, offset)
                    if cmd['name']=='ID' or cmd['name'].startswith('Schaltzeiten') or cmd['name']=='Datum und Uhrzeit':
                        resultJSON += '"%s":"%s",' % (jsonname,result)
                    elif cmd['name']=='Solarertrag':
                        resultJSON += '"%s":%s,' % (jsonname,result.split(';',1)[0])
                        resultJSON += '"%s_Woche":%s,' % (jsonname,('%s' % (result.split(';'))).replace("'",''))
                    else:
                        resultJSON += '"%s":%s,' % (jsonname,result)
                else:
                    result = '0x%s' % rmsg.Data.hex()
                    if len(rmsg.Data) == 2:
                        result += ' %d' % (rmsg.Data[0] + 256 * rmsg.Data[1])
                    resultJSON += '"%s":"%s",' % (jsonname,result)
                if 'unit' in cmd:
                    result += ' ' + cmd['unit']
                logging.info('%04x:%02x - %s - %s' % (cmd['addr'], cmd['size'], cmd['name'], result))
            resultJSON = resultJSON[:-1] + '}'
            mqc.publish(MQTT_TOPIC + 'status/json',resultJSON,qos=0,retain=True)
            time.sleep(15)

except Exception as e:
    logging.error("Unhandled error [" + str(e) + "]")
    sys.exit(1)
