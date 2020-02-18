#! /usr/bin/python3
'''
Created on 21 May 2019
JS8CallGPSUI Copyright 2019 M0IAX
@author: Mark Bumstead M0IAX
http://m0iax.com
'''
import configparser
import tkinter as tk
from tkinter import StringVar
import time, json
import gpsdGPSListener
import os
import subprocess
import sys
#import udpServer
import what3words
from socket import socket, AF_INET, SOCK_DGRAM

HEIGHT=500
WIDTH=500
JS8CALL_IPADDRESS='127.0.0.1'
JS8CALL_PORT=2242
SERIAL_ENABLED=False
TYPE_STATION_SETGRID='STATION.SET_GRID'
TYPE_TX_GRID='TX.SEND_MESSAGE'
TYPE_TX_SETMESSAGE='TX.SET_TEXT'
TYPE_TX_SEND='TX.SEND_MESSAGE'
TYPE_GET_CALL_ACTIVITY="RX.GET_CALL_ACTIVITY"
TYPE_WINDOWRAISE='WINDOW.RAISE'
TXT_ALLCALLGRID='@APRSIS GRID '
TXT_ALLCALL='@ALLCALL '
TYPE_STATION_GETCALLSIGN='STATION.GET_CALLSIGN'
UDP_ENABLED=False

text=""
networkText=""
hostname = ""

def createConfigFile(configFileName):
    #cretes the config file if it does not exist
    if not os.path.isfile(configFileName):
            
        config = configparser.ConfigParser()
        config['NETWORK'] = {'serverip': '127.0.0.1',
                             'serverport': 2242
                            }
            
        with open(configFileName, 'w') as configfile:
            config.write(configfile)
            configfile.close()



configfilename="./js8call.cfg"
createConfigFile(configfilename)

if os.path.isfile(configfilename):
    config = configparser.ConfigParser()
    config.read(configfilename)

    serverip = config.get('NETWORK','serverip')
    serverport = int(config.get('NETWORK', 'serverport'))

listen = (serverip, serverport)

class utils:
    def from_message(self,content):
        try:
            return json.loads(content)
        except ValueError:
            return {}
    def to_message(self,typ, value, params=None):
        if params is None:
            params = {}
        if typ==TYPE_STATION_GETCALLSIGN:
            self.getResponse=True
        return json.dumps({'type': typ, 'value': value, 'params': params})
     
class UserInterface:
    
    first=True
    addr = ('127.0.0.1',65500)
    getResponse=False
    laststatusString=""
    sock=None
        
    def __init__(self):
        
        
        self.MAX_TIMER=600    
    
        self.mainWindow=tk.Tk()
        self.mainWindow.title("JS8CALL GPS Utilities by M0IAX")
        
        self.first=True
        self.getResponse=False
        
        canvas = tk.Canvas(self.mainWindow, height=HEIGHT, width=WIDTH)
        canvas.pack()
        
        self.var1 = StringVar()
        self.var2 = StringVar()

        frame=tk.Frame(self.mainWindow, bg="navy", bd=5)
        frame.place(relx=0.5,rely=0.05, relwidth=0.85, relheight=0.35, anchor='n')
        
        self.gridrefEntry = tk.Entry(frame, font=40, textvariable=self.var1)
        self.gridrefEntry.place(relwidth=0.48,relheight=0.3)
        
        self.getGridButton = tk.Button(frame, text="Get Grid from GPS", command=self.getGrid, bg="white", font=30)
        self.getGridButton.place(relx=0.52,relwidth=0.48,relheight=0.3)
        
        self.ngrStr = StringVar()
        
        self.ngrStr.set("NGR not set")
        self.NGRLabel = tk.Label(frame, textvariable=self.ngrStr )
        self.NGRLabel.place(relx=0.05,rely=0.55, relwidth=0.9,relheight=0.18)
        
        self.ngrEntry = tk.Entry(frame, font=12, justify='center', textvariable=self.ngrStr)
        self.ngrEntry.place(rely=0.55,relwidth=1,relheight=0.18)
        
        self.wtwStr = StringVar()
         
        self.wtwEntry = tk.Entry(frame, font=12, justify='center', textvariable=self.wtwStr)
        self.wtwEntry.place(rely=0.75,relwidth=1, relheight=0.18)
        
        
        lowerFrame=tk.Frame(self.mainWindow, bg="navy", bd=5)
        lowerFrame.place(relx=0.5,rely=0.4, relwidth=0.85, relheight=0.5, anchor='n')
        
        
        self.setJS8CallGridButton = tk.Button(lowerFrame, text="Send Grid to JS8Call", command=lambda: self.sendGridToJS8Call(self.gridrefEntry.get()), bg="white", font=40)
        self.setJS8CallGridButton.place(relx=0.02, relwidth=0.45,relheight=0.2)
        self.setJS8CallGridButton.configure(state='disabled')
        
        self.sendJS8CallALLCALLButton = tk.Button(lowerFrame, text="TX Grid", command=lambda: self.sendGridToALLCALL(self.gridrefEntry.get()), bg="white", font=40)
        self.sendJS8CallALLCALLButton.place(relx=0.55,relwidth=0.44,relheight=0.2)
        self.sendJS8CallALLCALLButton.configure(state='disabled')
        
        self.autoGridToJS8Call = 0
        self.autoGridCheck = tk.Checkbutton(lowerFrame, text="Auto update JS8Call Grid every 10 minutes.", variable=self.autoGridToJS8Call, command=self.cb)
        self.autoGridCheck.place(relx=0.05,rely=0.5, relwidth=0.9,relheight=0.1)
        
        self.timerlabel = tk.Label(lowerFrame,text="When timer reaches zero\nThe Grid in JS8Call will be updated.\nIt does NOT transmit, use the button above to do that.", bg="navy", fg="white")
        self.timerlabel.place(relx=0.05,rely=0.6, relwidth=0.9,relheight=0.18)
        
        self.timer=30
        self.timerStr = StringVar()
        
        self.timerStr.set("Timer Not Active")
        self.timerlabel = tk.Label(lowerFrame, textvariable=self.timerStr )
        self.timerlabel.place(relx=0.05,rely=0.9, relwidth=0.9,relheight=0.1)
        
        self.update_timer()
        self.update_status_timer()
        self.mainWindow.mainloop()
     
    
    def cb(self):
        if self.autoGridToJS8Call==0:
            self.autoGridToJS8Call=1
        else:
            self.autoGridToJS8Call=0
            self.timerStr.set("Timer Not Active")
    def update_timer(self):
        if self.autoGridToJS8Call==0:
            self.initTimer()
        if self.autoGridToJS8Call==1:
            if self.timer<=0:
                self.initTimer()
            self.timer=self.timer-1
            t="Timer: " + str(self.timer)
            self.timerStr.set(t)
            if self.timer<=0:
                gridstr = self.getGrid()
                self.sendGridToJS8Call(gridstr)
                self.initTimer()
        self.mainWindow.after(1000, self.update_timer)
    
    def update_status_timer(self):

        self.mainWindow.after(10000, self.update_status_timer)

    def initTimer(self):
            self.timer=self.MAX_TIMER
    
    def sendMessage(self, messageType,messageText):
        
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(listen)
        
        content, addr = self.sock.recvfrom(65500)
        print('incoming message:', ':'.join(map(str, addr)))

        try:
            message = json.loads(content)
        except ValueError:
            message = {}

        self.reply_to = addr

        if messageType!=None:
            self.send(messageType, messageText)
        
        self.sock.close()

    def to_message(self,typ, value='', params=None):
        if params is None:
            params = {}
        return json.dumps({'type': typ, 'value': value, 'params': params})

    def send(self, *args, **kwargs):
        params = kwargs.get('params', {})
        if '_ID' not in params:
            params['_ID'] = int(time.time()*1000)
            kwargs['params'] = params
            #print("Params ". params)
        message = self.to_message(*args, **kwargs)
        print('sending outgoing message:', message)
        self.sock.sendto(message.encode(), self.reply_to)
    
    
    def sendMessageAndClose(self,messageType,messageText):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(listen)
        
        content, addr = self.sock.recvfrom(65500)
        print('incoming message:', ':'.join(map(str, addr)))

        try:
            message = json.loads(content)
        except ValueError:
            message = {}

        #if not message:
        #    continue

        self.reply_to = addr

        if messageType!=None:
            self.send(messageType, messageText)
            #self.messageText=None
            #self.messageType=None
        
        self.sock.close()


    def sendGridToJS8Call(self, gridText):
        print('Sending Grid to JS8CAll...',gridText) 
        #UDP_ENABLED=True
        self.sendMessageAndClose(TYPE_STATION_SETGRID, gridText)
        #SendToJS8Call.send(self,TYPE_STATION_SETGRID, gridText)
        UDP_ENABLED=False
        #self.getHeardList()
    def sendGridToALLCALL(self,gridText):
        messageToSend = TXT_ALLCALLGRID + gridText
        print("Sending ", messageToSend)
        self.sendMessageAndClose(TYPE_TX_GRID, gridText)
    
    def getGrid(self):
        print('Getting Grid from GPS')
        gpsText = gpsl.getMaidenhead()
        ngr = gpsl.get_ngr()
        
        print("Got Grid "+gpsText)
        if ngr!=None:
            print("Got NGR "+ngr)
            
        #    res = geocoder.convert_to_3wa(what3words.Coordinates(gpsl.getCurrentLat(), gpsl.getCurrentLon()))
        #    print("What3Words: %s" % (res['words'],))
        #    self.wtwStr.set(res['words'])
        
        self.var1.set(gpsText)
                
        if gpsText!= "No Fix" and gpsText!='JJ00aa00':
            self.setJS8CallGridButton.configure(state='normal')
            self.sendJS8CallALLCALLButton.configure(state='normal')
            #self.sendWTWJS8CallALLCALLButton.configure(state='normal')
            self.ngrStr.set(ngr)
        else:
            self.setJS8CallGridButton.configure(state='disabled')
            self.sendJS8CallALLCALLButton.configure(state='disabled')
            #self.sendWTWJS8CallALLCALLButton.configure(state='disabled')
            self.ngrStr.set('No Fix')
            self.var1.set('No Fix')
        
        if gpsText=='JJ00aa00':
            self.ngrStr.set('No Fix')
    
        return gpsText
        
        

try:

    gpsl = serialGPSlistener.GPSListenerWin()
    gpsl.start()

    ui = UserInterface()
    
    gpsl.setReadGPS(False)
  #  udp.close()
    
finally:
    gpsl.setReadGPS(False)
    gpsl.join()
    


