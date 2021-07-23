import telnetlib

# This little script communicates with e.g. a Raspberry Pi running vcontrold, which
# has a connection via an Optolink to the heating system.
# It uses raw commands to execute various read functions, which removes the
# need to create a custom vito.xml file for vcontrold.

HOST = 'GatewayViessmann.local' # vcontrold telnet host
PORT = '3002' # vcontrold port

EOT = 4
ENQ = 5
VS2_ACK = 6
NACK = 21
VS2_NACK = 21
VS2_START_VS2 = 22
VS2_DAP_STANDARD = 65 # plus two 0x00 bytes

VS1 = True
VS2 = False

if VS1: # VS1
	Virtual_Write = 244
	Virtual_READ = 247
	GFA_Read = 107
	GFA_Write = 104
	PROZESS_WRITE = 120
	PROZESS_READ = 123
if VS2: # VS2
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


def buildVS2Package(fc,addr,length):
	crc = (5 + 0 + fc + ((addr >> 8) & 0xFF) + (addr & 0xFF) + length) & 0xFF
	return ('%02X ' * 8) % (VS2_DAP_STANDARD,5,0,fc,(addr >> 8),(addr & 0xF8),length,crc)

readCmds = [
			{ 'addr':0x00F8,'size':8,'cmd':Virtual_READ, 'name':'ID' },
#			{ 'addr':0xF000,'size':16,'cmd':Virtual_READ },
#			{ 'addr':0xF010,'size':16,'cmd':Virtual_READ },
#			{ 'addr':0x08E0,'size':7,'cmd':Virtual_READ },

# 			{ 'addr':0x7700,'size':1,'cmd':Virtual_READ, 'name':'Heizkreis-Warmwasserschema' },


# 			{ 'addr':0x47C5,'size':1,'cmd':Virtual_READ, 'name':'Vorlauf - Minimalbegrenzung M3' },
# 			{ 'addr':0x47C6,'size':1,'cmd':Virtual_READ, 'name':'Vorlauf - Maximalbegrenzung M3' },
# 
# 			{ 'addr':0x5525,'size':2,'cmd':Virtual_READ, 'name':'Aussentemperatur' },
# 			{ 'addr':0x0810,'size':2,'cmd':Virtual_READ, 'name':'Kesseltemperatur' },
# 			{ 'addr':0x555A,'size':2,'cmd':Virtual_READ, 'name':'Kesselsolltemperatur' },
# 			{ 'addr':0x0816,'size':2,'cmd':Virtual_READ, 'name':'Abgastemperatur' },
# 			{ 'addr':0x0810,'size':2,'cmd':Virtual_READ, 'name':'Vorlauftemperatur A1M1' },
# 			{ 'addr':0x3900,'size':2,'cmd':Virtual_READ, 'name':'Vorlauftemperatur M2' },
# 			{ 'addr':0x4900,'size':2,'cmd':Virtual_READ, 'name':'Vorlauftemperatur M3' },
# 			{ 'addr':0x0812,'size':2,'cmd':Virtual_READ, 'name':'Temperatur Speicher Ladesensor Komfortsensor' },
# 			{ 'addr':0x0814,'size':2,'cmd':Virtual_READ, 'name':'Auslauftemperatur' },

			{ 'addr':0xCF30,'size':32,'cmd':Virtual_READ, 'name':'Solarertrag' },
# 			{ 'addr':0x6564,'size':2,'cmd':Virtual_READ, 'name':'Solar Kollektortemperatur' },
# 			{ 'addr':0x6566,'size':2,'cmd':Virtual_READ, 'name':'Solar Speichertemperatur' },
 			{ 'addr':0x6560,'size':2,'cmd':Virtual_READ, 'name':'Solar Wärmemenge' },
 			{ 'addr':0x6568,'size':2,'cmd':Virtual_READ, 'name':'Solar Betriebsstunden' },
		  ]

telnet_client = telnetlib.Telnet(HOST, PORT)
for cmd in readCmds:
	#print(cmd)
	telnet_client.read_until(b"vctrld>")
	#print('raw\nSEND %02X\nWAIT %02X\nSEND %02X 00 00\nWAIT %02X\nSEND %s\nRECV %d\nEND\n' % (EOT, ENQ, VS2_START_VS2, VS2_ACK, buildPackage(cmd['cmd'], cmd['addr'], cmd['size']), 1+7+cmd['size']+1))
	if VS1:
		telnet_client.write(('raw\nSEND 04\nWAIT 05\nSEND 01 %02X %02X %02X %02X\nRECV %d\nEND\n' % (cmd['cmd'], (cmd['addr'] >> 8), cmd['addr'] & 0xFF, cmd['size'], cmd['size'])).encode())
	if VS2:
		telnet_client.write(('raw\nSEND %02X\nWAIT %02X\nSEND %02X 00 00\nWAIT %02X\nSEND %s\nRECV %d\nEND\n' % (EOT, ENQ, VS2_START_VS2, VS2_ACK, buildVS2Package(cmd['cmd'], cmd['addr'], cmd['size']), 1+7+cmd['size']+1)).encode())
	out = telnet_client.read_until(b'\n').decode('utf-8').strip()
	out = out.replace('Result: ','')
	out = bytes.fromhex(out)
	if VS1:
		val = 0
		if cmd['size'] == 1:
			val = out[0]
		elif cmd['size'] == 2:
			val = (out[0] + (out[1] << 8)) * 0.1
		print('%04x : %.1f [%s] - %s' % (cmd['addr'],val,out.hex(),cmd['name']))
	if VS2:
		if out[0] != VS2_ACK or out[1] != VS2_DAP_STANDARD:
			continue
		checksum = 0x00
		for val in out[2:-1]:
			checksum = (checksum + val) & 0xff
		if checksum != out[-1]:
			continue
		out = out[2:-1]
		print('%04x : %s - %s' % (cmd['addr'],out[6:6+cmd['size']].hex(),cmd['name']))
