# Vitosoft data structures

Vitosoft uses a large Microsoft SQL Server database `ecnViessmann.mdf/ldf` to keep track of all heating systems, devices and all their parameters. Besides that database, the information is also available as XML files, which is what we will use to find out all events, which are supported by our system.

## Definition of terms

- Device is a vendor. Only one exists: Viessmann
- Datapoints are heating units or devices. Typically there is only one active at any given time. There are about 400 datapoints known.
- Events are readable and/or writeable values or callable functions to the heating unit.
- Event Values are specific values for specific events. This allows naming certain values or creating named enums.
- Event Groups allow grouping of events, e.g. all solar parameters in one group. This is only used for a nicer presentation within the Vitosoft application.
- Display Condition and Display Condition Group are used to hide individual events, e.g. if not solar system is installed, then it will not show up in the UI. It allows relatively complex terms.


## XML files

There are several XML files of interest. *Warning*: You actually need to launch Vitosoft _once_ for it to generate the `ecnDataPointType.xml` and `ecnEventType.xml` files from `ecnViessmann.mdf`. The outdated files from the EXE will be moved to a folder named `configbackup`.

- `DPDefinitions.xml` - a massive almost 200GB large file, which contains the database of all data points in XML format
- `ecnVersion.xml` – contains the `DataPointDefinitionVersion`. It is regenerated on first launch from the SQL database, which bumps the version number to `0.0.26.4683`.
- `ecnDataPointType.xml` - The file contains all information needed to identify the Viessmann heating unit. The `ID` of the unit is used as `Address` in the `ecnDatapointType` inside `DPDefinitions.xml`.
- `ecnEventType.xml` - Events are readable and/or writeable values or callable functions to the heating unit. The `ID` of the event is used as `Address` in the `ecnEventType` inside `DPDefinitions.xml`.
- `ecnEventTypeGroup.xml` - this XML allows to combines events into groups, like all solar events together. The `ID` of the event is used as `Address` in the `ecnEventTypeGroup` inside `DPDefinitions.xml`.
- `Textresource_de.xml` (for German) and `Textresource_en.xml` (for English) - translate `Labels` into a `Value`, which is a readable label for a field in the databases if the `Name` starts with `@@`.
- `sysDeviceIdent.xml` - additional common events, which are needed to identify a specific heating system.


## `sysDeviceIdent.xml`

Eight addresses to be used via `Virtual Read` are defined for all devices.

| Viessmann internal name    | Address | in XML files |
| -------------------------- | ------- | ----------- |
| `ProtocolIdentifierOffset` |  `0xF0` | `ecnsysDeviceIdentF0` |
| `GRUPPENIDENTIFIKATION`    |  `0xF8` | `sysDeviceGroupIdent` |
| `REGLERIDENTIFIKATION`     |  `0xF9` | `sysDeviceIdent` |
| `HARDWAREINDEX`            |  `0xFA` | `sysHardwareIndexIdent` |
| `SOFTWAREINDEX`            |  `0xFB` | `sysSoftwareIndexIdent` |
| `VERSION_LDA`              |  `0xFC` | `sysProtokollversionLDAIdent` |
| `VERSION_RDA`              |  `0xFD` | `sysProtokollversionRDAIdent` |
| `VERSION_SW1`              |  `0xFE` | `sysHighByteDeveloperVersionIdent` |
| `VERSION_SW2`              |  `0xFF` | `sysLowByteDeveloperVersionIdent` |


## `ecnDataPointType.xml`

`ecnDataPointType.xml` contains all information to identify supported systems. It is essential to run Vitosoft _once_ for this file to be generated correctly – otherwise you have a very outdated version.

- `ID` is the global id, which is referenced by other databases as `Address`.
- `Description` is an internal description of the system
- `Identification` must match `sysDeviceGroupIdent` and `sysDeviceIdent`, which are combined as 4-digit hex-values. This is the main way to identify the actual system.
- `IdentificationExtension` allows to identify specific hardware and software revisions, which might have different limitations. It must match the combined hex-values of `sysHardwareIndexIdent` and `sysSoftwareIndexIdent`. If this key is larger than 4 hex-characters, it does not seem to match with the Vitosoft app, it might be used for an internal app only.
- `IdentificationExtensionTill` if this one exists, then `IdentificationExtension` till `IdentificationExtensionTill` is a range of systems, which match.
- `EventOptimisation` can be 0 (allowed) or 1 (not allowed). It allows Vitosoft to combine certain read requests into one for better performance.
- `EventOptimisationExceptionList` disables event optimization for specific events.
- `Options` additional options for the system. Only `undefined`, `trending` and `appointeddate` are defined and i think none of them is used by Vitosoft.
- `ControllerType` can have the following values: `GWG` = 0, `WP` = 1, `NR` = 2, `VC300Old` = 3, `BHKW` = 4, `WO1A` = 5, `VC100Old` = 6, `VC200Old` = 7, `VC100New` = 8, `VC200New` = 9, `VC300New` = 10, `WPR3` = 11, `VitotwinGW_BATI` = 12, `NRP` = 14 – it seems that only VC100–VC300 are supported by Vitosoft Optolink.
- `ErrorType` can have the following values: 0 = Unknown, 1 = Default, 2 = VCom, 3 = WP, 4 = BHKW, 5 = DefaultRPC, 6 = WPR3, 7 = VitotwinGW_BATI. It seems to be ignored by Vitosoft.
- `F0` match the `ProtocolIdentifierOffset` value.
- `F0Till` similar to `IdentificationExtensionTill`, it allows defining a range.

There are some special cases for identification of systems, which are hard-coded in the Vitosoft application, be aware.

## DPDefinitions

`ecnConverter` → `ecnDeviceType` (Vendor, always Viessmann) → `ecnDatapointType` (Heating units, devices) → `ecnEventType` (parameter) → `ecnEventValueType` (individual values for a specific parameter)

`ecnEventTypeGroup` (groups of parameters) → `ecnEventType` (individual parameter)

![Graph of the dependencies](graph.gv.pdf)

### ecnConverter
Base class, only exist once. Can be ignored.

`Id` unique ID of the converters

          <Id>1</Id>
          <ConverterClassName>vsm.Dispatcher.Notification</ConverterClassName>
          <ConverterAssembly>vsm.Dispatcher, Version=1.2.0.0, Culture=neutral, PublicKeyToken=6ffa2c8f99f9eb6d</ConverterAssembly>

### ecnConverterDeviceTypeLink
Defines a relationship between the converter and the devices. There is only one devices: Viessmann. Can be ignored.

`ConverterId` is a reference to `Id` in `ecnConverter`
`DeviceTypeTechnicalIdentificationAddress` is a reference to `TechnicalIdentificationAddress` in `ecnDeviceType`

          <ConverterId>1</ConverterId>
          <DeviceTypeTechnicalIdentificationAddress>7</DeviceTypeTechnicalIdentificationAddress>


### ecnDeviceType
Sits below the converter, only exists once (ID 54). Unimportant when communicating with the unit. The "device" is always Viessmann! Can be ignored.

`Id` unique ID of the device
`Name` name of the device
`Manufacturer` manufacturer of the device
`Description` internal description
`StatusEventTypeId` `ecnEventType` with the status
`TechnicalIdentificationAddress` a reference to `ecnConverterDeviceTypeLink`

          <Id>54</Id>
          <Name>Viessmann Anlage</Name>
          <Manufacturer></Manufacturer>
          <Description></Description>
          <StatusDataPointTypeId>1</StatusDataPointTypeId>
          <TechnicalIdentificationAddress>7</TechnicalIdentificationAddress>

#### ecnDeviceTypeDataPointTypeLink
Defines a relationship between a device and multiple data points. A device in this context is "Viessmann", while data points are the heating units. Can be ignored.

`DeviceTypeId` is a reference to `Id` in `ecnDeviceType`
`DataPointTypeId` is a reference to `Id` in `ecnDatapointType`

          <DeviceTypeId>54</DeviceTypeId>
          <DataPointTypeId>1</DataPointTypeId>


### ecnDatapointType
A data point is an actual heating unit. There are about 400 defined. This is the first important type!

`Id` unique ID of the data point
`Name` name of the data point. '@@' as a prefix points into `Textresource_xx.xml` for translation.
`Description` internal info about this datapoint. Always in German.
`StatusEventTypeId` a `ecnEventType` with the status
`Address` a reference to the `ID` in `ecnDataPointType.xml`, which describes how the heating unit can be identified.

          <Id>350</Id>
          <Name>@@viessmann.datapointtype.name.VScotHO1_72</Name>
          <Description>Technische Produktbeschreibung: ab Softwareindex 72 (Projekt Neptun)</Description>
          <StatusEventTypeId>1</StatusEventTypeId>
          <Address>VScotHO1_72</Address>

#### ecnDataPointTypeEventTypeLink
Defines a relationship between a data point and multiple events.

`DataPointTypeId` is a reference to `Id` in `ecnDatapointType`
`EventTypeId` is a reference to `Id` in `ecnEventType`

          <DataPointTypeId>10</DataPointTypeId>
          <EventTypeId>2</EventTypeId>


### ecnEventType
Events are individual parameter in the heating unit.

`Id` unique ID of the event
`EnumType` Is this event an enum value? Only `true` or `false` are valid.
`Name` name of the events. '@@' as a prefix points into `Textresource_xx.xml` for translation.
`Address` a reference to the `ID` in `ecnEventType.xml`, which has information on how to access the value in the heating unit as well as value ranges or lists (for enums)
`Conversion` How to convert the binary value, see conversion
`Description` internal info about this event. Always in German.
`Priority` The default is 100, sometimes (enums, adressen 0xF8…0xFF=1…8) it is 50. Probably used to sort the order of requests.
`Filtercriterion` always seems to be `true`?
`Reportingcriterion` always seems to be `true`?
`Type` allowed access to this event: 1=Read-only, 2=Read/Write, 3=Write-only
`URL` Vitosoft internal web server URL to visualize the datapoint, e.g. an editor the time/date scheduling.
`DefaultValue` default value for this event, if not read from the heating unit. Can be an integer or float.

          <Id>329</Id>
          <EnumType>false</EnumType>
          <Name>@@viessmann.eventtype.name.GWG_Aussentemperatur</Name>
          <Address>GWG_Aussentemperatur~0x006F</Address>
          <Conversion>Div2</Conversion>
          <Description>@@viessmann.eventtype.GWG_Aussentemperatur.description</Description>
          <Priority>100</Priority>
          <Filtercriterion>true</Filtercriterion>
          <Reportingcriterion>true</Reportingcriterion>
          <Type>1</Type>
          <URL></URL>
          <DefaultValue></DefaultValue>

#### ecnEventTypeEventValueTypeLink
Defines a relationship between an event and multiple event values.

`EventTypeId` is a reference to `Id` in `ecnEventType`
`EventValueId` is a reference to `Id` in `ecnEventValueType`

          <EventTypeId>1</EventTypeId>
          <EventValueId>13287</EventValueId>

### ecnEventValueType
Value of an event, used to define conditions.

`Id` unique ID of the event value
`Name` name of this event value. '@@' as a prefix points into `Textresource_xx.xml` for translation.

          <Id>2</Id>
          <Name>@@viessmann.eventvaluetype.name.Absenkzeit_gelerntA1M1</Name>
          <EnumReplaceValue></EnumReplaceValue>
          <StatusTypeId>0</StatusTypeId>
          <Unit>ecnUnit.Minuten</Unit>
          <DataType>Int</DataType>
          <Stepping>10</Stepping>
          <LowerBorder>0</LowerBorder>
          <UpperBorder>250</UpperBorder>
          <Description></Description>


### ecnEventTypeGroup
Allows to group events together, like all solar events. Used for a more pleasant visualization.

`Id` unique ID of the group
`Name` name of the group. '@@' as a prefix points into `Textresource_xx.xml` for translation.
`ParentId` is a reference to `Id` in `ecnEventTypeGroup`. -1 = no parent.
`EntrancePoint` is the group an entrance or only a subgroup of another one? Only `true` or `false` are valid.
`Address` a reference to `ecnEventTypeGroup.xml`
`DeviceTypeId` is a reference to `Id` in `ecnDeviceType`. There is only one: 54 (Viessmann)
`DataPointTypeId` is a reference to `Id` in `ecnDatapointType`.
`OrderIndex` Sorting order for the group within the `DeviceTypeId`/`DataPointTypeId` selection.

          <Id>3</Id>
          <Name>@@viessmann.eventtypegroup.name.Dekamatik_E~10_Bedienung</Name>
          <Description></Description>
          <ParentId>-1</ParentId>
          <EntrancePoint>true</EntrancePoint>
          <Address>Dekamatik_E~10_Bedienung</Address>
          <DeviceTypeId>54</DeviceTypeId>
          <DataPointTypeId>144</DataPointTypeId>
          <OrderIndex>1</OrderIndex>

#### ecnEventTypeEventTypeGroupLink
Defines a relationship between a group and multiple events including an order value.

`EventTypeId` is a reference to `Id` in `ecnEventType`
`EventTypeGroupId` is a reference to `Id` in `ecnEventTypeGroup`
`EventTypeOrder` ist die Sortierreihenfolge des Event Type innerhalb der Gruppe. Dubletten sind möglich!

          <EventTypeId>1134</EventTypeId>
          <EventTypeGroupId>4</EventTypeGroupId>
          <EventTypeOrder>17</EventTypeOrder>


### ecnDisplayCondition
A single condition to hide an event in the UI, because e.g. the hardware does not exist or other settings prohibit this event. As you can see: it allows to compare the event with a specific value for this event. This is extremely common for events, which are enums. But it is also possible to compare the event with a specific value, which could be a temperature limit.

`Id` unique ID of the display condition
`Name` name of the display condition - never set
`ConditionGroupId` is a reference to `Id` in `ecnDisplayConditionGroup`
`EventTypeIdCondition` is a reference to `Id` in `ecnEventType`
`EventTypeValueCondition` is a reference to `Id` in `ecnEventValueType`
`Description` internal info for this display condition
`Condition` compare operator: 0=Equal, 1=NotEqual, 2=GreaterThan, 3=GreaterThanOrEqualTo, 4=LessThan, 5=LessThanOrEqualTo
`ConditionValue` defined, if `Condition` >= 2, contains the value for the comparism

          <Id>19922</Id>
          <Name></Name>
          <ConditionGroupId>5993</ConditionGroupId>
          <EventTypeIdCondition>5276</EventTypeIdCondition>
          <EventTypeValueCondition>8403</EventTypeValueCondition>
          <Description></Description>
          <Condition>2</Condition>
          <ConditionValue>300</ConditionValue>

### ecnDisplayConditionGroup
A display condition group allows combining multiple display conditions via AND or OR to a complex term. Best to look at the Python sample code for more details.

`Id` unique ID of the condition group
`Name` name of the condition group
`Type` 1=AND or 2=OR all conditions
`ParentId` is a reference to `Id` in `ecnDisplayConditionGroup`. -1 = no parent.
`Description` internal info for this condition group
`EventTypeIdDest` is a reference to `Id` in `ecnEventType`. -1 = not defined
`EventTypeGroupIdDest` is a reference to `Id` in `ecnEventTypeGroup`. -1 = not defined

          <Id>1</Id>
          <Name>VDensHC2 Überblick Solar</Name>
          <Type>1</Type>
          <ParentId>-1</ParentId>
          <Description></Description>
          <EventTypeIdDest>-1</EventTypeIdDest>
          <EventTypeGroupIdDest>5604</EventTypeGroupIdDest>

## Conversion

If a `ConversionFactor` is not defined, it is assumed to be `1`. If a `ConversionOffset` is not defined, it is assumed to be `0`.

| conversion name       	| result type | conversion of the byte buffer `buf` |
|---------------------------|-----|---------------|
| NoConversion				| – | no conversion |
| MultOffset				| Double | `V * ConversionFactor + ConversionOffset` |
| Mult2						| Double | `V * 2` |
| Mult5						| Double | `V * 5` |
| Mult10					| Double | `V * 10` |
| Mult100					| Double | `V * 100` |
| Div2						| Double | `V / 2` |
| Div10						| Double | `V / 10` |
| Div100					| Double | `V / 100` |
| Div1000					| Double | `V / 1000` |
| Time53					| String | `HH:MM` with `HH=buf[0] >> 3; MM=(buf[0] & 7) * 10;` or an empty string, if `buffer[0]==0xFF` |
| DateBCD					| DateTime | BCD in `buf` with 8 bytes `YYYYMMDDxxHHMMSS` |
| DateTimeBCD				| DateTime | identical to DateTimeBCD |
| DateTimeVitocom			| ? | *NOT IMPLEMENTED* |
| Sec2Minute				| Double | `Round(V / 60, 2)` |
| Sec2Hour					| Double | `Round(V / (60*60)), 2)` |
| Sec2Day					| Double | `Round(V / (24*60*60), 2)` |
| Sec2Week					| Double | `Round(V / (7*24*60*60), 2)` |
| Sec2Month					| Double | *NOT IMPLEMENTED* |
| Estrich					| ? | *NOT IMPLEMENTED* |
| Kesselfolge				| ? | *NOT IMPLEMENTED* |
| IPAddress					| String | IP4 buf[3]+'.'+buf[2]+'.'+buf[1]+'.'+buf[0] |
| Steuerzeichen				| ? | *NOT IMPLEMENTED* |
| UTCDiff2Hour				| ? | *NOT IMPLEMENTED* |
| UTCDiff2Day				| ? | *NOT IMPLEMENTED* |
| UTCDiff2Month				| ? | *NOT IMPLEMENTED* |
| HourDiffSec2Hour			| ? | *NOT IMPLEMENTED* |
| VitocomEingang			| ? | *NOT IMPLEMENTED* |
| Vitocom300SGEinrichtenKanalLON  | ? | *NOT IMPLEMENTED* |
| Vitocom300SGEinrichtenKanalMBUS | ? | *NOT IMPLEMENTED* |
| Vitocom300SGEinrichtenKanalWILO | ? | *NOT IMPLEMENTED* |
| VitocomNV					| ? | *NOT IMPLEMENTED* |
| Vitocom3NV				| ? | *NOT IMPLEMENTED* |
| HexByte2DecimalByte		| ByteArray | standard byte array |
| RotateBytes				| ByteArray | reverse all bytes in the array |
| Phone2BCD					| ByteArray | converts BCD data (0-9) in a ByteArray. Assumes the BCD value 15 to be ignored. |
| ImpulszaehlerV300FA2		| ? | *NOT IMPLEMENTED* |
| DatenpunktADDR			| ? | *NOT IMPLEMENTED* |
| DateTimeMBus				| ? | *NOT IMPLEMENTED* |
| DateMBus					| ? | *NOT IMPLEMENTED* |
| MultOffsetBCD				| Double | Up to 0-4 byte LSB value `V`, then applies `V * ConversionFactor + ConversionOffset` |
| HexToFloat				| ? | *NOT IMPLEMENTED* |
| MultOffsetFloat			| Double | *NOT IMPLEMENTED* |
| HexByte2AsciiByte			| ByteArray | standard byte array – same as `HexByte2DecimalByte` |
| DayToDate					| DateTime | `buf` of up to 8 bytes will be interpreted as a 64-bit LSB value, which represents the number of days starting 1.1.1970 – UNIX timestamp |
| FixedStringTerminalZeroes	|     | zero terminated string |
| LastBurnerCheck			| ? | *NOT IMPLEMENTED* |
| LastCheckInterval			| ? | *NOT IMPLEMENTED* |
| Convert4BytesToFloat		| | Converts 4 IEEE bytes into a float |


## Unnecessary or unknown

### ecnConfigSet

`Id` unique ID of the config set

          <Id>1</Id>
          <Name>IO_VC_DE1</Name>
          <ProcessingBL>vsmCommInterface.businesslogic.IOConfigSetProcessorBL, vsmCommInterface</ProcessingBL>

### ecnConfigSetParameter

`Id` unique ID of the config set parameter

          <Id>1</Id>
          <ConfigSetId>1</ConfigSetId>
          <Parameter>Evaluate</Parameter>
          <Required>true</Required>

### ecnCulture

Used for translations of the interface in different languages. Not necessary to communicate with the system.

`Id` unique ID of the culture
`Name` ISO-Sprachcode

          <Id>2</Id>
          <Name>en</Name>

### ecnStatusType

Error status (ecnEventType #1). The following `Id` are defined:

0
: Undefined (SortOrder = 100, ShowInEventTray = false)

1
: OK (SortOrder = 3, ShowInEventTray = false)

2
: Warning (SortOrder = 2, ShowInEventTray = true)

3
: Error (SortOrder = 1, ShowInEventTray = true)

4
: illegal value (SortOrder = 4, ShowInEventTray = true)

5
: --- (SortOrder = 5, ShowInEventTray = true)

`Id` unique ID of the status (0-5 are possible)
`Name` name of the status. '@@' as a prefix points into `Textresource_xx.xml` for translation.
`ShowInEventTray` Is the status value shown in the event tray?
`Image` Base64 of a GIF representing the status
`SortOrder` sort oder for the status

          <Id>5</Id>
          <Name>@@viessmann.vitodata.valuestatus.notevaluate</Name>
          <ShowInEventTray>true</ShowInEventTray>
          <Image>………</Image>
          <SortOrder>5</SortOrder>
