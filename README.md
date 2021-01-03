# SmtGdn
Fall 2020 CSE521s Final Project Repository

To set up Data Hub:
1)Upload python program “smtGdnDS.py” to a processor with ethernet capabilities. In the initial experimental setup, a Raspberry Pi B+ was used. 
2)In the python program, a few variables need to be changed to identify the station.
2a)Line 52 indicates the station ID. This must be unique from other Data stations to prevent overwriting data.
2b)Line54 stores the Data station’s IP address and port number. The first argument must be changed to the Pi’s IP address as a string, and an unused port number must be given in the second argument as an integer.
3)Execute the program with python3. 
4)Several messages from the program indicate setup and server events. Once the message “Server listening for events” appears, the server is ready to accept new connections. When it connects to a Garden station, this server will automatically give the garden station a unique station ID and upload any messages to Amazon aws. This process will continue until powered off

How to set up Garden Station:
1)On a computer, open the program “ArduinoSoilSensorEthernetV4.ino” in the Ardunio IDE.
2)On line 9, the ‘ip’ variable must be changed to have a unique Id on the ethernet network.
3)On line 10, the ‘serverip’ variable must be changed to match the ip address of the server (specified in “smtGdnDS.py”).
4)On line 11, the ‘port’ variable must be changed to the port specified in “smtGdnDS.py” 
5)Upload Arduino to an Arduino Uno with ethernet capabilities
6)Ensure the server (machine running “smtGdnDS.py”) and this station are on the same ethernet network, and plug into power. After several seconds, the server should indicate that it has established a connection with the data station
7)Repeat steps 1-6 to set up more garden stations to the same server
