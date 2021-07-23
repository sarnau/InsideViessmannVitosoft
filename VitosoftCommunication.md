# Viessmann Communication

## Hardware Layer

### Communication via OptoLink/USB Serial

A simple serial port with a baud rate of 4800 8E2.

### Communication via WLAN

Vitosoft is searching for Wireless Access Point `VIESSMANN-12345678`. `12345678` is the password to the WLAN Access Point. After connecting to the access point, it creates a TCP Connection to `10.45.161.1:45317` (10.x.x.x is a private Class-A network), which is treated very similar to the serial port, except sync is not necessary – it seems to be managed on the device side. Besides that it seems identical to the VS2 protocol.


## Software Layer

Communication is a package based serial communication. In pseudo-code it works like this:
```
	sendPackage()
	for retry=0 to RETRYCOUNT
		if hasReply() then
			receiveReplyPackage()
			return
		sleep(RETRYDELAY)
```

In the following section I write `RETRYCOUNT x RETRYDELAY ms`, e.g. `10x50ms` to define the delays.

### GWG

The GWG protocol is only used for old "Gas Wand Geräte" (Gas Wall Units). It is detected, but no longer supported by the Vitosoft 300 application. It only supports 8-bit addresses with several function codes, allowing a slightly larger address space.

The detection works as follows: wait up to 10x50ms for an `ENQ` (0x05). Then send `0xC7,0xF8,0x04` (Virtual Read 0xF8, 4 bytes). The reply should be `0x20,0x53` or `0x20,0x54` to detect the GWG hardware. `0x20` is the "Gruppenidentifikation" (group identification) and `0x53` or `0x54` are the "Regleridentifikation" (controller unit identification)

### VS1

Version 1 of the Vitotronic protocol, supported by the KW units from Viessmann. It supports 16-bit addresses plus several function codes.

Because the whole communication is timing based, a timer is called every 50ms to check the current state of the connection and does the following:

1. after opening the serial port or in case of an error, a connection is created by waiting for up to 30x100ms for an `ENQ` (0x05). It then immediately is confirmed by sending a `0x01`. In case an `VS2_ACK` (`0x06`) or `VS2_NACK` (`0x15`) was received, the VS2 protocol is also supported.
2. If there is a pending message to be send, the message is written out and for up to 20x50ms serial data is read. Once the number of expected bytes have been received, the data is then processed. If within the giving time, not enough data was received, a connection reset it triggered (see step #1)
3. If nothing needs to be send to the unit, every 500ms the connection is kept alive, by sending a check connection message (Virtual Read: 0xF8, 2 bytes), which expects a 2-byte reply within 20x50ms.

#### VS1 Message Format

The message is a simply list of bytes:

1. Command/Function Code (`Virtuell_Write` = `0xF4`, `Virtuell_Read` = `0xF7`, `GFA_Read` = `0x6B`, `GFA_Write` = `0x68`, `PROZESS_WRITE` = `0x78`, `PROZESS_READ` = `0x7B`)
2. Address High Byte
3. Address Low Byte
4. Block Length
5. For write functions: Block Length additional bytes

Read functions send a reply containing of the number of bytes in the block. All write functions send a single byte `vs1_data`, which is `0x00` in case the write was successful, any other value is undefined and is a failure.

### VS2

Version 2 of the Vitotronic protocol. It is supported by all modern Viessmann units. These modern units also seem to be backward compatible with the VS1 protocol. It is an extension of the VS1 protocol, mostly to be faster and more reliable – thanks to checksums. But it is also more complex, because of hand-shaking requirements.

To initiate the connection, after the serial port read buffer is emptied, then an `EOT` (`0x04`) is send and for 30x100ms waited for an `ENQ` (`0x05`), after which a `VS2_START_VS2, 0, 0` (`0x16,0x00,0x00`) is send and within 30x100ms an `VS2_ACK` (`0x06`) is expected. If an `VS2_ACK` (`0x06`) is received, before the start was sent, the start is resent (and the timeout is reset). In case a `VS2_NACK` (`0x15`) is received, it also resents the start and resets the timeout.

After message is send, for up 30x100ms serial data is read. An `VS2_ACK` (`0x06`) or `VS2_NACK` (`0x15`) is expected first. If more than one is received, the oldest ones are removed from the receive buffer. If it is not received as the first byte, the message was not send successfully. Further bytes are collected till a full message is received. If the checksum is valid, an `VS2_ACK` is send out to confirm the successful transmission. A `VS2_NACK` is never send!

If no message was send within 5s, the connection is restarted, the serial port read buffer is emptied and then sending a `VS2_START_VS2, 0, 0` (`0x16,0x00,0x00`) and within 30x100ms expecting an `VS2_ACK` (`0x06`).

In case a UNACKD Message was send, only a single `VS2_ACK` or `VS2_NACK` is expected.


#### VS2 Message Format

The message requires a simple checksum.

1. `VS2_DAP_STANDARD` (0x41)
2. Package length for the CRC
3. Protocol Identifier (0x00 = LDAP, 0x10 = RDAP, unused) | Message Identifier (0 = Request Message, 1 = Response Message, 2 = UNACKD Message, 3 = Error Message)
4. Message Sequenz Number (top 3 bits in the byte) | Function Code
5. Address High Byte
6. Address Low Byte
7. Block Length
8. Block Length additional bytes
9. CRC, a modulo-256 addition of bytes from Block Length and the additional bytes. CRC is technically the wrong name, it is more a checksum. But that is what Viessmann calls it.

##### Defined Commands/Function Codes:

There are many commands defined, but only very few are actually used by Vitosoft, which seems to be `Virtual_READ`, `Virtual_WRITE`, `Remote_Procedure_Call`, `PROZESS_READ`, `PROZESS_WRITE`, `GFA_READ`, `GFA_WRITE`.

Here is the complete list:
- `undefined` = 0
- `Virtual_READ` = 1
- `Virtual_WRITE` = 2
- `Physical_READ` = 3
- `Physical_WRITE` = 4
- `EEPROM_READ` = 5
- `EEPROM_WRITE` = 6
- `Remote_Procedure_Call` = 7
- `Virtual_MBUS` = 33
- `Virtual_MarktManager_READ` = 34
- `Virtual_MarktManager_WRITE` = 35
- `Virtual_WILO_READ` = 36
- `Virtual_WILO_WRITE` = 37
- `XRAM_READ` = 49
- `XRAM_WRITE` = 50
- `Port_READ` = 51
- `Port_WRITE` = 52
- `BE_READ` = 53
- `BE_WRITE` = 54
- `KMBUS_RAM_READ` = 65
- `KMBUS_EEPROM_READ` = 67
- `KBUS_DATAELEMENT_READ` = 81
- `KBUS_DATAELEMENT_WRITE` = 82
- `KBUS_DATABLOCK_READ` = 83
- `KBUS_DATABLOCK_WRITE` = 84
- `KBUS_TRANSPARENT_READ` = 85
- `KBUS_TRANSPARENT_WRITE` = 86
- `KBUS_INITIALISATION_READ` = 87
- `KBUS_INITIALISATION_WRITE` = 88
- `KBUS_EEPROM_LT_READ` = 89
- `KBUS_EEPROM_LT_WRITE` = 90
- `KBUS_CONTROL_WRITE` = 91
- `KBUS_MEMBERLIST_READ` = 93
- `KBUS_MEMBERLIST_WRITE` = 94
- `KBUS_VIRTUAL_READ` = 95
- `KBUS_VIRTUAL_WRITE` = 96
- `KBUS_DIRECT_READ` = 97
- `KBUS_DIRECT_WRITE` = 98
- `KBUS_INDIRECT_READ` = 99
- `KBUS_INDIRECT_WRITE` = 100
- `KBUS_GATEWAY_READ` = 101
- `KBUS_GATEWAY_WRITE` = 102
- `PROZESS_WRITE` = 120
- `PROZESS_READ` = 123
- `OT_Physical_Read` = 180
- `OT_Virtual_Read` = 181
- `OT_Physical_Write` = 182
- `OT_Virtual_Write` = 183
- `GFA_READ` = 201
- `GFA_WRITE` = 202
