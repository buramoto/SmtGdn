import serial
import sys
import boto3
import json
import socket
import select
import os
import socketserver
import struct
from datetime import datetime
import numpy as np


#Global variables- Serial
#portString = '/dev/ttyACM0'

#Global variables- certificate paths
rootCertificate = "/home/pi/Documents/cse521/awsComm/certs/smart-plant-server.cert.pem"
privateKey = "/home/pi/Documents/cse521/awsComm/certs/smart-plant-server.private.key"
deviceCertificate = "/home/pi/Documents/cse521/awsComm/certs/64a3543566-certificate.pem.crt"
#Global variables- aws communication

#Begin initalization
print("Initalizing SmartGarden data station.")

#Arduino connection via serial
#print("Connecting to Arduino...")
#try:
#    ser = serial.Serial(portString, 9600)
#except:
#    print("Could not find Arduino at ", portString)
#    sys.exit()

#Connect to Amazon aws iot
s3 = boto3.resource('s3')
#print("Connected to aws, listing 'buckets'...\n")

print("Creating SNS client...")
sns = boto3.client('iot-data', region_name='us-east-2', verify=False)
#print("Printing initalization message to server...")
#testMessage = json.dumps({
#        "row" : "10",
#        "pos" : "11",
#        "moisture" : "12"
#        })
#response = sns.publish(TopicArn='arn:aws:sns:us-east-2:640308236574:SoilSensor', Message=testMessage)
#response = sns.publish(topic='SoilSensor', qos=0, payload=testMessage)
#print(response)

#Ethernet variables
print("Initalizing ethernet parameters...")
smtGdnDataStationID = 18
gardenStationID = 20
serverAddress = ('192.168.10.17', 6109)
#server = socket.create_server(serverAddress)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(serverAddress)
server.listen()
serverPoll = select.epoll()
serverPoll.register(server.fileno(), select.EPOLLIN)
currentConnections = [server]
print("Server set up with fd ", server.fileno())

#Global variables- data. This creates a file to store buffered data
#dataBufferFile = open("dataBuffer.txt", "w") #future goal: make append functionality to boot with existing data
class stationData:
    soilDataBuffer = [0] * 100
    lightDataBuffer = [0] * 100
    timeDataBuffer = ["0"] * 100
    dataPointer = 0
masterDataDict = {}
#Strech goal: put data into file, but no time to figure out csvs right now

#Send data method
def uploadData(unpackedData):
    #used to send data to amazon aws iot and store data in bufferes
    timeStamp = datetime.now()
    currentDataClass = masterDataDict[unpackedData[0]]
    currentDataClass.soilDataBuffer[currentDataClass.dataPointer] = unpackedData[1] #log soil reading
    currentDataClass.lightDataBuffer[currentDataClass.dataPointer] = unpackedData[2] #log light reading
    currentDataClass.timeDataBuffer[currentDataClass.dataPointer] =  timeStamp.strftime("%d/%m/%Y %H:%M:%S") #log time
    print("For garden station ", unpackedData[0], " this is sample number ", currentDataClass.dataPointer)
    currentDataClass.dataPointer = currentDataClass.dataPointer + 1
    if(currentDataClass.dataPointer > 99):
        currentDataClass.dataPointer = 0 #Start overwriting data at beginning if at 100, (buffer limit)
    print("Uploading data to amazon aws iot")
    publishMessage = json.dumps({
        "row" : str(smtGdnDataStationID),
        "pos" : str(unpackedData[0]), 
        "timestamp" : ", ".join(currentDataClass.timeDataBuffer),
        "moistureSensor" : list(currentDataClass.soilDataBuffer), 
        "lightSensor" : list(currentDataClass.lightDataBuffer)
        })
    sns.publish(topic='SoilSensor', qos=0, payload=publishMessage)
    print("Uploaded data to server.")

def storeData(unpackedData):
    #Used to buffer previous reads of sensors
    dataBufferFile.write()

#main program
if __name__ == '__main__':
    print("Initalization complete\n")
    while 1:
        print("\nServer listening for events...")
        serverEvents = serverPoll.poll()
        print("Event detected. Fd of ", serverEvents[0][0], "Event of ", "{0:b}".format(serverEvents[0][1]))
        if not serverEvents:
            continue
        for i in serverEvents:
            if(i[0] == server.fileno()):
                #Server has recived a connection request
                #This if statement to handle incoming connections
                #print("Server fd event detected. Has event of ", i[1])
                if(i[1] == select.EPOLLIN):
                    newClient = server.accept()
                    serverPoll.register(newClient[0].fileno(), select.EPOLLOUT|select.EPOLLRDHUP|select.EPOLLERR)
                    currentConnections.append(newClient[0])
                    print("New client detected. Assigning fd of ", newClient[0].fileno())
                    continue
            if(i[1] == select.EPOLLOUT):
                #This statement is used to initalize new clients.
                #It switches clients to write only after init values are sent
                print("Assigning", gardenStationID, "to new client")
                os.write(i[0], gardenStationID.to_bytes(2, 'little'))
                masterDataDict[gardenStationID] = stationData()
                gardenStationID = gardenStationID + 1
                serverPoll.modify(i[0], select.EPOLLIN|select.EPOLLRDHUP|select.EPOLLERR)
                continue
            if(i[1] == select.EPOLLIN):
                #We are getting data from a client
                arduinoInput = os.read(i[0], 100)
                #print("Recieved from arduino...", arduinoInput)
                unpackedInput = struct.unpack('hhh', arduinoInput)
                print("Unpacked input:", unpackedInput)
                uploadData(unpackedInput)
                continue
            hangupDetector = i[1]&8192
            if(hangupDetector == select.EPOLLRDHUP):
                #client closed connection
                print("A client with fd", i[0], "has closed")
                serverPoll.unregister(i[0])
                for j in currentConnections:
                    if(j.fileno() == i[0]):
                        j.close()
                        currentConnections.remove(j)
