# Inside Viessmann Vitosoft

## Documentation

- [Vitosoft Software](./VitosoftSoftware.md)
- [Vitosoft Communication](./VitosoftCommunication.md)
- [Vitosoft XML](./VitosoftXML.md)

## Sample code

All Print-sample code requires XML files from the Vitosoft software inside the `data` folder!

- [PrintDatapoints.py](PrintDatapoints.py) Prints all supported data points (heating units)
- [PrintEventsForDatapoint.py](PrintEventsForDatapoint.py) Prints all events for a specific heating unit, sorted by groups
- [PrintEventTypes.py](PrintEventTypes.py) Prints all event types in a readable form. Combined with the two scripts above you can get all information on how to read specific values from your heating system
- [vcontrold_test.py](vcontrold_test.py) If you have vcontrold already installed on a Raspberry Pi, you can use this script to read specific events directly without adopting the `vito.xml` file in vcontrold to match your heating unit.
- [Viessmann2MQTT.py](Viessmann2MQTT.py) A script to be run on e.g. a Raspberry Pi with Optolink. It polls a list of events (look at the source code – they need to be adopted to your heating unit!) and sends them via MQTT.
- [VitosoftWLANServer.py](VitosoftWLANServer.py) A script to be run on e.g. a Raspberry Pi with Optolink. It implements a Vitosoft compatible WLAN server. This requires the routing tables on the Raspberry Pi to be set up for WLAN, etc. Complicated, the script is also a hack. Feel free to experiment with it, if you know what you are doing.
