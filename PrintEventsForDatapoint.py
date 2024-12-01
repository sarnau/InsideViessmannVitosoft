#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree as etree
import pprint
import sys
import binascii
import re

pp = pprint.PrettyPrinter(width=200,compact=True)

# This path needs to be adjusted to point to a directory for all XML files
DATAPATH = "../data/"

MAX_STR_LENGTH = 1000 # certain strings (e.g. conditions) can be very long. This shortens them. 1000 matches "print everything"

textList = {}
def parse_Textresource(lang):
	root = etree.parse(DATAPATH + "Textresource_%s.xml" % lang).getroot()
	for rootNodes in root:
		if 'TextResources' in rootNodes.tag:
			for textNode in rootNodes:
				textList[textNode.attrib['Label']] = textNode.attrib['Value'].replace('##ecnnewline##','\\n').replace('##ecntab##','\\t')

def translate(node,key):
	if key in node and node[key] and node[key].startswith('@@'):
		if node[key][2:] in textList and len(node[key][2:]):
			node[key] = textList[node[key][2:]]

def parse_node(root,nodeName):
	elements = []
	for xmlEvent in root.findall(".//" + nodeName):
		dp = {}
		for cell in xmlEvent:
			if cell.tag in ['Description','URL','DefaultValue','Filtercriterion','Reportingcriterion','Priority']:
				continue
			if cell.tag in ['Conversion','EnumType']: # these are not needed
				continue
			value = cell.text
			if value == 'true':
				value = True
			elif value == 'false':
				value = False
			if cell.tag in ['ConverterId','Id','Type','ConfigSetId','EventValueId','EnumAddressValue','StatusTypeId','EventTypeValueCondition','EventTypeIdCondition','ConditionGroupId','EventTypeGroupIdDest','EventTypeIdDest','EventTypeId','EventTypeGroupId','DataPointTypeId','DeviceTypeId','DataPointTypeId','OrderIndex','EventTypeOrder','ParentId','StatusDataPointTypeId','TechnicalIdentificationAddress','SortOrder']:
				value = int(value)
			if cell.tag == 'ParentId' and value == -1:
				continue
			dp[cell.tag] = value
			if cell.tag in ['Description','Name','EnumReplaceValue']:
				translate(dp,cell.tag)
		elements.append(dp)
	return elements

ecnEventTypes = {}
def parse_ecnEventTypes():
	for nodes in etree.parse(DATAPATH + "ecnEventType.xml").getroot():
		eventType = {}
		for cell in nodes:
			if cell.tag in []:
				continue
			value = cell.text
			if cell.tag == 'ValueList':
				valueDict = {}
				for valueEnum in value.split(';'):
					valueEnumVal,valueEnumStr = valueEnum.split('=', 1)
					if valueEnumStr.startswith('@@'):
						if valueEnumStr[2:] in textList and len(valueEnumStr[2:]):
							valueEnumStr = textList[valueEnumStr[2:]]
					try:
						valueEnumVal = int(valueEnumVal)
					except:
						pass
					valueDict[valueEnumVal] = valueEnumStr
				value = valueDict
			if value == 'true':
				value = True
			elif value == 'false':
				value = False
			elif cell.tag in ['BitLength', 'BitPosition', 'BlockLength', 'ByteLength', 'BytePosition', 'RPCHandler', 'MappingType']:
				try:
					value = int(value)
				except:
					pass
			elif cell.tag in ['ConversionFactor', 'Stepping', 'UpperBorder', 'LowerBorder']:
				try:
					value = float(value)
				except:
					pass
#			elif cell.tag in ['PrefixRead', 'PrefixWrite', 'ALZ'] and value:
#				if value.startswith('0x'):
#					value = value[2:]
#				value = binascii.unhexlify(value)
			eventType[cell.tag] = value
			if cell.tag in ['Description']:
				translate(eventType,cell.tag)
			if cell.tag in []:#['Unit']:
				if eventType[cell.tag] in textList and len(eventType[cell.tag]):
					eventType[cell.tag] = textList[eventType[cell.tag]]
		eventID = eventType['ID']
		del eventType['ID']
		if 'Conversion' in eventType:
			if eventType['Conversion'] == 'NoConversion':
				del eventType['Conversion']
				if 'ConversionFactor' in eventType:
					del eventType['ConversionFactor']
				if 'ConversionOffset' in eventType:
					del eventType['ConversionOffset']
		if 'FCRead' in eventType and eventType['FCRead'] == 'undefined':
			eventType['FCRead'] = None
		if 'FCWrite' in eventType and eventType['FCWrite'] == 'undefined':
			eventType['FCWrite'] = None
		if 'OptionList' in eventType:
			eventType['OptionList'] = eventType['OptionList'].split(';')
		ecnEventTypes[eventID] = eventType

usedEventTypes = set()
def eventTypeDescr(eventID):
	if eventID not in ecnEventTypes:
		return eventID
	usedEventTypes.add(eventID)
	et = ecnEventTypes[eventID]
	result = eventID
	#cmd = et['FCRead']
	#if cmd == 'Virtual_READ':
	#	cmd = 'VR'
	#elif cmd == 'Virtual_WRITE':
	#	cmd = 'VW'
	#result += ': ' + cmd
	#result += ':' + et['Address']
	#if et['BlockLength'] == et['ByteLength']:
	#	result += ':%d' % et['BlockLength']
	#else:
	#	result += ':%d' % et['ByteLength']
	result += ' (%s)' % et['Parameter']
	return result

def parse_DPDefinitions(selectedDatapointTypeAddress):
	classes = set()
	root = etree.fromstring(re.sub(' xmlns="[^"]+"', '', open(DATAPATH + "DPDefinitions.xml",'r').read()))
	for xmlEvent in root.find("ECNDataSet/{urn:schemas-microsoft-com:xml-diffgram-v1}diffgram/ECNDataSet"):
		classes.add(xmlEvent.tag)

	nodeListe = {}
	for cl in classes:
		nodes = parse_node(root,cl)
		if True:
			if cl == 'ecnEventValueType':
				for dd in nodes:
					st = int(dd['StatusTypeId'])
					if st == 5:
						dd['StatusTypeId'] = '@@viessmann.vitodata.valuestatus.notevaluate'
					elif st == 4:
						dd['StatusTypeId'] = '@@viessmann.vitodata.valuestatus.outofinterval'
					elif st == 3:
						dd['StatusTypeId'] = 'Error'
					elif st == 2:
						dd['StatusTypeId'] = 'Warning'
					elif st == 1:
						dd['StatusTypeId'] = 'OK'
					elif st == 0:
						dd['StatusTypeId'] = 'Undefined'
					else:
						dd['StatusTypeId'] = '???'
			if len(nodes) > 0 and 'Id' in nodes[0]:
				dd = {}
				for e in nodes:
					foundId = e['Id']
					del e['Id']
					dd[foundId] = e
				nodes = dd
		nodeListe[cl] = nodes
		if cl in [ 'ecnVersion',
				   'ecnDeviceType',
				   'ecnStatusType',
				   'ecnDatapointType','ecnDeviceTypeDataPointTypeLink',
				   'ecnEventType','ecnDataPointTypeEventTypeLink',
				   'ecnTableExtension','ecnTableExtensionValue',
				   'ecnEventValueType','ecnEventTypeEventValueTypeLink',
				   'ecnEventTypeGroup','ecnEventTypeEventTypeGroupLink',
				   'ecnConverter','ecnConverterDeviceTypeLink','ecnCulture',
				    ]:
#				   'ecnConfigSet','ecnStatusType','ecnConfigSetParameter']:
#			continue
			pass
		if False and cl == 'ecnDisplayConditionGroup':
			print(cl, len(nodeListe[cl]), type(nodeListe[cl]))
			for node in nodeListe:
				if isinstance(nodeListe[cl], list): 
					pp.pprint(nodeListe[cl])
				elif isinstance(nodeListe[cl], dict): 
					pp.pprint(nodeListe[cl])
			print('-' * 40)
	#			break
			#sys.exit(0)
			pass

	usedConditionEventTypeIds = set()
	def getCondStr(groupId,groupOrEvent='EventTypeGroupIdDest'):
		condDict = { 0:'=', 1:'≠', 2:'>', 3:'≥', 4:'<', 5:'≤' }
		operDict = { 1:'AND', 2:'OR' }
		shortName = { # to avoid the conditions get incredibly long, we shorten some known common events
					'(00) Heizkreis-Warmwasserschema':'00_WWS',
					'(54) Solarregelung':'54_SR',
					'(7F) Unterscheidung Einfamilienhaus - Mehrparteienhaus':'7F_EFH',
					'Software-Index des Gerätes':'SWIdx',
					'SW-Index Solarmodul SM1':'SWIdxSolarSM1',
					'HW-Index Solarmodul SM1':'HWIdxSolarSM1',
					'(00) Anlagen-Warmwasserschema':'00_AnlWWS',
					'(76) Konfiguration Kommunikationsmodul':'76_KonfKommMod',
					'(76) Kommunikationsmodul':'76_KommMod',
					'(A0) Kennung Fernbedienung A1M1':'A0_KennFBA1M1',
					'(A0) Kennung Fernbedienung M2':'A0_KennFBM2',
					'(A0) Kennung Fernbedienung M3':'A0_KennFBM3',
					'Fernbedienung Heizkreis A1M1':'FBA1M1',
					'Fernbedienung Heizkreis M2':'FBM2',
					'Fernbedienung Heizkreis M3':'FBM3',
					'(E5) Kennung Pumpe Heizkreis A1':'E5_KennPumpHzkA1',
					'(E5) Kennung Pumpe Heizkreis M2':'E5_KennPumpHzkM2',
					'(E5) Kennung Pumpe Heizkreis M3':'E5_KennPumpHzkM3',
					'Status Raumtemp.-Sensor HK1':'RaumTempSensHK1',
					'Status Raumtemp.-Sensor HK2':'RaumTempSensHK2',
					'Status Raumtemp.-Sensor HK3':'RaumTempSensHK3',
					'(30) Kennung Interne Umwälzpumpe':'30_KennIntUmwPumpe',
					'(91) Zuordnung externe Betriebsarten-umschaltung':'ZuordExtBetrUmsch',
					'(35) Kennung Anschlusserweiterung EA1':'35_KennAnschlErwEA1',
					'(5B) Kennung Anschlusserweiterung EA1':'5B_KennAnschlErwEA1',
					'(32) Kennung Anschlusserweiterung AM1':'32_KennAnschlErwAM1',
					}

		groupCond = ''
		for displayConditionGroupId,displayConditionGroup in nodeListe['ecnDisplayConditionGroup'].items():
			if displayConditionGroup[groupOrEvent] != groupId:
				continue
			ll = []
			for dispCondId,dispCond in nodeListe['ecnDisplayCondition'].items():
				if dispCond['ConditionGroupId'] != displayConditionGroupId:
					continue
				eventTypeId = int(dispCond['EventTypeIdCondition'])
				usedConditionEventTypeIds.add(eventTypeId)
				eventType = nodeListe['ecnEventType'][eventTypeId]
				name = eventType['Name'].strip()
				if name in shortName:
					name = shortName[name]
				else:
					name = '"%s"' % name
				#name += ' (%d)' % (eventTypeId)
				eventValue = nodeListe['ecnEventValueType'][int(dispCond['EventTypeValueCondition'])]
				if 'EnumReplaceValue' in eventValue:
					val = '"%s"' % eventValue['EnumReplaceValue']
				elif 'EnumAddressValue' in eventValue:
					val = '"%s"' % eventValue['EnumAddressValue']
				else:
					val = '%s' % eventValue
				if 'EqualCondition' in dispCond:
					ll.append(name + '=' + val)
				else:
					ll.append(name + condDict[int(dispCond['Condition'])] + val)
			groupCond += (' ' + operDict[displayConditionGroup['Type']] + ' ').join(ll)
		if groupCond:
			return ' HIDDEN:(%s)' % groupCond
		return ''

	# find datapoint for a given address
	for datapointTypeId,datapointType in nodeListe['ecnDatapointType'].items():
		if datapointType['Address'] != selectedDatapointTypeAddress:
			continue
		print(datapointType['Name'])
		print('=' * len(datapointType['Name']))
		break

	# find all event IDs for a given data datapoint ID
	eventTypeIds = set()
	for dataPointTypeEventTypeLink in nodeListe['ecnDataPointTypeEventTypeLink']:
		if dataPointTypeEventTypeLink['DataPointTypeId'] != datapointTypeId:
			continue
		eventTypeIds.add(dataPointTypeEventTypeLink['EventTypeId'])

	usedGroups = {}
	for eventTypeId in eventTypeIds:
		eventType = nodeListe['ecnEventType'][eventTypeId].copy()
		eventType['Id'] = eventTypeId
		eventTypeAddress = eventType['Address']
		#del eventType['Address']
		if eventTypeAddress == 'DatabaseVersionForExport':
			continue
		if eventType['Name'] in ['ecnStatusEventType','ecnsysEventType~ErrorNotification']:
			continue
		if eventTypeAddress in ecnEventTypes and 'FCRead' in ecnEventTypes[eventTypeAddress]:
			eventType['FCRead'] = ecnEventTypes[eventTypeAddress]['FCRead']
			#if eventType['FCRead'] == 'Remote_Procedure_Call':
			#	continue
			pass
		else:
			continue # URL only event
		#if eventTypeAddress in ecnEventTypes and 'FCWrite' in ecnEventTypes[eventTypeAddress] and ecnEventTypes[eventTypeAddress]['FCWrite']:
		#	eventType['FCWrite'] = ecnEventTypes[eventTypeAddress]['FCWrite']
		del eventType['Type']

		# build a list of value types for an event type
		if True: # for enums there is a list of possible values
			evalueDict = {}
			evalueList = []
			for evl in nodeListe['ecnEventTypeEventValueTypeLink']:
				if evl['EventTypeId'] != eventTypeId:
					continue
				eventValueType = nodeListe['ecnEventValueType'][evl['EventValueId']]
				if 'Name' in eventValueType:
					del eventValueType['Name']
				if 'StatusTypeId' in eventValueType and eventValueType['StatusTypeId'] == 'Undefined':
					del eventValueType['StatusTypeId']
				if 'Unit' in eventValueType:
					if eventValueType['Unit'] == None:
						del eventValueType['Unit']
					elif eventValueType['Unit'].startswith('ecnUnit.'):
						eventValueType['Unit'] = eventValueType['Unit'][8:]
				if eventValueType['DataType'] == 'Int':
					if 'ValuePrecision' in eventValueType:
						eventValueType['ValuePrecision'] = int(eventValueType['ValuePrecision'])
					if 'LowerBorder' in eventValueType:
						eventValueType['LowerBorder'] = int(eventValueType['LowerBorder'])
					if 'UpperBorder' in eventValueType:
						eventValueType['UpperBorder'] = int(eventValueType['UpperBorder'])
					if 'Stepping' in eventValueType:
						eventValueType['Stepping'] = int(eventValueType['Stepping'])
						if eventValueType['Stepping'] == 1:
							del eventValueType['Stepping']
				elif eventValueType['DataType'] == 'Float':
					if 'LowerBorder' in eventValueType:
						eventValueType['LowerBorder'] = float(eventValueType['LowerBorder'])
					if 'UpperBorder' in eventValueType:
						eventValueType['UpperBorder'] = float(eventValueType['UpperBorder'])
					if 'Stepping' in eventValueType:
						eventValueType['Stepping'] = float(eventValueType['Stepping'])
						if eventValueType['Stepping'] == 1.0:
							del eventValueType['Stepping']
				elif eventValueType['DataType'] == 'DateTime':
					if 'ValuePrecision' in eventValueType:
						eventValueType['ValuePrecision'] = int(eventValueType['ValuePrecision'])
				elif eventValueType['DataType'] == 'Binary':
					if 'LowerBorder' in eventValueType:
						eventValueType['LowerBorder'] = float(eventValueType['LowerBorder'])
					if 'UpperBorder' in eventValueType:
						eventValueType['UpperBorder'] = float(eventValueType['UpperBorder'])
					if 'Stepping' in eventValueType:
						eventValueType['Stepping'] = float(eventValueType['Stepping'])
						if eventValueType['Stepping'] == 1.0:
							del eventValueType['Stepping']
#				else:
#					pp.pprint(eventValueType)
				if 'EnumAddressValue' in eventValueType and 'EnumReplaceValue' in eventValueType:
					evalueDict[int(eventValueType['EnumAddressValue'])] = eventValueType['EnumReplaceValue']
				else:
					if 'EnumAddressValue' in eventValueType:
						del eventValueType['EnumAddressValue']
					if 'EnumReplaceValue' in eventValueType:
						del eventValueType['EnumReplaceValue']
					evalueList.append(eventValueType)
			if len(evalueList):
				if len(evalueList)==1:
					eventType['_VALUE_'] = evalueList[0]
				else:
					eventType['_VALUE_'] = evalueList
			else:
				eventType['_VALUE_'] = evalueDict

		if True: # events can be in several groups
			foundGroup = False
			for eventTypeEventTypeGroupLink in nodeListe['ecnEventTypeEventTypeGroupLink']:
				if eventTypeEventTypeGroupLink['EventTypeId'] != eventTypeId:
					continue
				if eventTypeEventTypeGroupLink['EventTypeGroupId'] not in nodeListe['ecnEventTypeGroup']: # the DP is missing entries!
					continue
				etgOrder = eventTypeEventTypeGroupLink['EventTypeOrder']
				eventTypeGroup = nodeListe['ecnEventTypeGroup'][eventTypeEventTypeGroupLink['EventTypeGroupId']]
				if eventTypeGroup['DataPointTypeId'] == datapointTypeId:
					group = eventTypeGroup.copy()
					del group['EntrancePoint'] # always true
					if 'ParentId' in group:
						parent = nodeListe['ecnEventTypeGroup'][group['ParentId']].copy()
						del group['ParentId']
						del parent['DataPointTypeId']
						del parent['DeviceTypeId']
						pname = parent['Name']
						if pname in textList and len(pname):
							pname = textList[pname]
							parent['Name'] = pname
						group['Name'] = '%s - %s' % (pname, group['Name'])
					del group['DataPointTypeId']
					del group['DeviceTypeId']
					del group['OrderIndex']
					if eventTypeEventTypeGroupLink['EventTypeGroupId'] not in usedGroups:
						usedGroups[eventTypeEventTypeGroupLink['EventTypeGroupId']] = {}
					etgOrder *= 10
					while etgOrder in usedGroups[eventTypeEventTypeGroupLink['EventTypeGroupId']]:
						etgOrder += 1
					usedGroups[eventTypeEventTypeGroupLink['EventTypeGroupId']][etgOrder] = eventType
					foundGroup = True
			if not foundGroup:
				if '_NO_GROUP_' in usedGroups:
					usedGroups[0].append(eventType)
				else:
					usedGroups[0] = [eventType]

	eventTypeGroups = {}
	for eventTypeGroupId,eventTypeGroup in nodeListe['ecnEventTypeGroup'].items():
		if eventTypeGroup['DataPointTypeId'] == datapointTypeId:
			del eventTypeGroup['DataPointTypeId']
			del eventTypeGroup['DeviceTypeId']
			eventTypeGroups[eventTypeGroupId] = eventTypeGroup
	sortedEventTypeGroups = sorted(eventTypeGroups,key=lambda x:eventTypeGroups[x]['OrderIndex'])
	for eventTypeGroupId in sortedEventTypeGroups:
		eventTypeGroup = eventTypeGroups[eventTypeGroupId]
		if 'ParentId' not in eventTypeGroup:
			eventTypeGroupName = eventTypeGroup['Name']
			if eventTypeGroupName in textList and len(eventTypeGroupName):
				eventTypeGroupName= textList[eventTypeGroupName]
			if eventTypeGroupName.startswith('ecnsys'):
				continue
			if eventTypeGroupName == 'Feuerungsautomat':
				break
			# find all children of this parent
			eventTypeGroupChildren = {}
			for eventTypeGroupChildId in sortedEventTypeGroups:
				eventTypeGroupChild = eventTypeGroups[eventTypeGroupChildId]
				if 'ParentId' not in eventTypeGroupChild:
					continue
				if eventTypeGroupChild['ParentId'] == eventTypeGroupId:
					del eventTypeGroupChild['ParentId']
					eventTypeGroupChildren[eventTypeGroupChildId] = eventTypeGroupChild
			if len(eventTypeGroupChildren): # no children, parent is not needed
				def groupStr(groupId,groupName):
					result = groupName.strip()
					result += ' (%d)' % groupId
					condStr = getCondStr(groupId)
					if len(condStr)>MAX_STR_LENGTH:
						condStr = condStr[:MAX_STR_LENGTH]+'…)'
					result += condStr
					return result
				print()
				print("# " + groupStr(eventTypeGroupId,eventTypeGroupName))
				for eventTypeGroupChildId in sorted(eventTypeGroupChildren,key=lambda x:eventTypeGroupChildren[x]['OrderIndex']):
					eventTypeGroupChild = eventTypeGroupChildren[eventTypeGroupChildId]
					eventTypeGroupChildName = eventTypeGroupChild['Name']
					if eventTypeGroupChildName in textList and len(eventTypeGroupChildName):
						eventTypeGroupChildName= textList[eventTypeGroupChildName]
					if eventTypeGroupChildId in usedGroups and len(usedGroups[eventTypeGroupChildId]):
						print("- " + groupStr(eventTypeGroupChildId,eventTypeGroupChildName))
						if eventTypeGroupChildId in usedGroups:
							for kk in sorted(usedGroups[eventTypeGroupChildId]):
								eventType = usedGroups[eventTypeGroupChildId][kk]
								def eventTypeStr(eventType):
									result = eventType['Name'].strip()
									result += ' (%d)' % eventType['Id']
									valStr = '%s' % eventType['_VALUE_']
									if len(valStr)>MAX_STR_LENGTH:
										valStr = valStr[:MAX_STR_LENGTH]+'…}'
									#result += ' ' + valStr
									result += ' [' + eventTypeDescr(eventType['Address']) + ']'
									condStr = getCondStr(eventType['Id'],'EventTypeIdDest')
									if len(condStr)>MAX_STR_LENGTH:
										condStr = condStr[:MAX_STR_LENGTH]+'…)'
									result += condStr
									return result
								print('    - ' + eventTypeStr(eventType))

		if False:
			print()
			for eventTypeId in sorted(usedConditionEventTypeIds):
				eventType = nodeListe['ecnEventType'][eventTypeId]
				name = eventType['Name'].strip()
				print('%s (%d) %s' % (name,eventTypeId,eventType['Address']))


if __name__ == "__main__":
	# print all events with their conditions, sorted by groups for a specific data point
	parse_Textresource('de') # load english localization, 'de' is German
	parse_ecnEventTypes()
	parse_DPDefinitions('VScotHO1_72')
	# 20cb 0351 0000 0146
