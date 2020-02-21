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
import os
import gpsdGPSListener
import subprocess
import sys
from socket import socket, AF_INET, SOCK_DGRAM
from tkinter import IntVar, messagebox, Menu
from tkinter.ttk import *
from tkinter.scrolledtext import ScrolledText

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
TXT_APRSIS='@APRSIS'
TYPE_STATION_GETCALLSIGN='STATION.GET_CALLSIGN'
UDP_ENABLED=False
MSG_ERROR='ERROR'
MSG_INFO='INFO'
MSG_WARN='WARN'
timeinmins=10

text=""
networkText=""
hostname = ""

def createConfigFile(configFileName):
    #creates the config file if it does not exist
    if not os.path.isfile(configFileName):
            
        config = configparser.ConfigParser()
        config['NETWORK'] = {'serverip': '127.0.0.1',
                             'serverport': 2242
                            }
        config['APP'] = {'autotimeperiod': 10,
                         'autoonatstart':0,
                         'autoselectedoption':0
                        }
            
        with open(configFileName, 'w') as configfile:
            config.write(configfile)
            configfile.close()

configfilename=sys.path[0]+"/js8call.cfg"

createConfigFile(configfilename)

if os.path.isfile(configfilename):
    config = configparser.ConfigParser()
    config.read(configfilename)

    serverip = config.get('NETWORK','serverip')
    serverport = int(config.get('NETWORK', 'serverport'))
    timeinmins = int(config.get('APP', 'autotimeperiod'))
    autoatstart = int(config.get('APP', 'autoonatstart'))
    autooption = int(config.get('APP', 'autoselectedoption'))
    
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
    def showMessage(self, messagetype, messageString):
        if messagetype==MSG_ERROR:
            messagebox.showerror("Error", messageString)
        elif messagetype==MSG_WARN:
            messagebox.showwarning("Warning",messageString)
        elif messagetype==MSG_INFO:
            messagebox.showinfo("Information",messageString)
        
    def createMessageString(self):
        messageString=""
        mode=""
        if self.combo.get()=="Email":
            mode="EMAIL-2"
        elif self.combo.get()=="SMS":
            mode = "SMSGTE"
        elif self.combo.get()=="APRS":
            mode=self.combo.get()
           
        mode = mode.ljust(9)
        if self.tocall.get()=="":
            return "Error, no email address is set"
        
        text=self.st.get('1.0', 'end-1c')  # Get all text in widget.
    
        if text=="":
            return "Error, message is empty, please enter a message to send"
        
        number = self.seq
        number = format(number, '02d')
        if self.combo.get()=="Email":
            message = "@APRSIS CMD :"+mode+":"+self.tocall.get()+" "+text+"{"+number+"}"
        elif self.combo.get()=="APRS":
            tocallsign=self.tocall.get()
            tocallsign=tocallsign.ljust(9)
            message = "@APRSIS CMD :"+tocallsign+":"+text+"{"+number+"}"
        else: 
            message = "@APRSIS CMD :"+mode+":@"+self.tocall.get()+" "+text+"{"+number+"}"
        
        self.seq=self.seq+1
        #APRS sequence number is 2 char, so reset if >99
        if self.seq>99:
            self.seq=1
        
        messageString = message #mode+" "+self.tocall.get()+" "+text
        return messageString

#    def checkJS8CallRunning(self):
#        
#        retval = False
#        if "js8call" in (p.name() for p in psutil.process_iter()):
#            retval = True

        #return retval
    
    def setAPRSMessage(self):
        messageType=TYPE_TX_SETMESSAGE
        
        messageString=self.createMessageString()
        
        if messageString.startswith("Error"):
            self.showMessage(MSG_ERROR, messageString)
            return
    
        self.sendMessage(messageType, messageString)
        
        self.showMessage(MSG_INFO, "Message text set in JS8Call, please use JS8Call to send the message.")
            
    def txAPRSMessage(self):
        messageType=TYPE_TX_SEND
        messageString=self.createMessageString()
        
        if messageString.startswith("Error"):
            return
        self.sendMessage(messageType, messageString)
        self.showMessage(MSG_INFO,"Message sent to JS8Call. It will now transmit the message.")

    def comboChange(self, event):
        mode = self.combo.get()
        if mode=="APRS":
            self.callLbl.config(text='Enter Callsign (including SSID)')
        elif mode=="Email":
            self.callLbl.config(text='Enter Email Address to send to')
        elif mode=="SMS":
            self.callLbl.config(text='Enter cell phone number')
 
    def autoComboChange(self, event):
        mode = self.combo.get()
    def appExit(self):
        None #exit()
    def about(self):
        self.showMessage(MSG_INFO,'JS8Call Utilities\nBy Mark M0IAX\nhttp://m0iax.com/findme\n')
    def buildMenu(self):
        menu = Menu(self.mainWindow)
        self.mainWindow.config(menu=menu)
        file=Menu(menu)
        file.add_command(label='About', command=self.about)
        #file.add_command(label='Exit', command=self.appExit)
        menu.add_cascade(label='File',menu=file)
        
    def __init__(self):

        self.seq=1

        self.MAX_TIMER=timeinmins*60    
    
        self.mainWindow=tk.Tk()
        self.mainWindow.title("JS8CALL Utilities by M0IAX")
        
        self.first=True
        self.getResponse=False
        
        canvas = tk.Canvas(self.mainWindow, height=HEIGHT, width=WIDTH)
        canvas.pack()
        
        self.var1 = StringVar()
        self.var2 = StringVar()

        frame=tk.Frame(self.mainWindow, bg="navy", bd=5)
        frame.place(relx=0.5,rely=0.05, relwidth=0.85, relheight=0.5, anchor='n')
        
        self.titleLabel = tk.Label(frame, font=12, text="Maidenhead Locator")
        self.titleLabel.place(relx=0.05, relwidth=0.9,relheight=0.10)
        
        self.gridrefEntry = tk.Entry(frame, font=40, textvariable=self.var1)
        self.gridrefEntry.place(rely=0.18, relwidth=0.48,relheight=0.18)
        
        self.getGridButton = tk.Button(frame, text="Get Grid from GPS", command=self.getGrid, bg="white", font=30)
        self.getGridButton.place(relx=0.52,rely=0.18,relwidth=0.48,relheight=0.18)
        
        self.ngrStr = StringVar()
        self.ngrStr.set("NGR not set")

        self.NGRLabel = tk.Label(frame, textvariable=self.ngrStr, font=12)
        #self.NGRLabel.place(relx=0.05,rely=0.2, relwidth=0.9,relheight=0.20)
        
        lowerFrame=tk.Frame(self.mainWindow, bg="navy", bd=5)
        lowerFrame.place(relx=0.5,rely=0.25, relwidth=0.85, relheight=0.5, anchor='n')
         
        self.setJS8CallGridButton = tk.Button(lowerFrame, text="Send Grid to JS8Call", command=lambda: self.sendGridToJS8Call(self.gridrefEntry.get()), bg="white", font=40)
        self.setJS8CallGridButton.place(relx=0.02, relwidth=0.45,relheight=0.2)
        self.setJS8CallGridButton.configure(state='disabled')
        
        self.sendJS8CallALLCALLButton = tk.Button(lowerFrame, text="TX Grid", command=lambda: self.sendGridToALLCALL(self.gridrefEntry.get()), bg="white", font=40)
        self.sendJS8CallALLCALLButton.place(relx=0.55,relwidth=0.44,relheight=0.2)
        self.sendJS8CallALLCALLButton.configure(state='disabled')
        
        self.autocombo = Combobox(lowerFrame, state='readonly')
        self.autocombo.state='disabled'
        self.autocombo.bind('<<ComboboxSelected>>', self.comboChange)    
        self.autocombo['values']= ("Auto update JS8Call Grid", "Auto TX Grid to APRSIS")
 
        self.autocombo.current(autooption) #set the selected item
        self.autocombo.place(relx=0.05,rely=0.23, relwidth=0.9,relheight=0.1)
        
        self.autoGridToJS8Call = IntVar(value=autoatstart)
        self.autoGridCheck = tk.Checkbutton(lowerFrame, text="Enable Auto update every "+str(timeinmins)+" mins.", variable=self.autoGridToJS8Call, command=self.cb)
        self.autoGridCheck.place(relx=0.05,rely=0.33, relwidth=0.9,relheight=0.1)
        
        self.timer=60 
        self.timerStr = StringVar()
        
        self.timerStr.set("Timer Not Active")
        self.timerlabel = tk.Label(lowerFrame, textvariable=self.timerStr )
        self.timerlabel.place(relx=0.05,rely=0.43, relwidth=0.9,relheight=0.1)
        
        ############################################################
        #                 APRS Messageing form                     #
        ############################################################

        aprsFrame=tk.Frame(self.mainWindow, bg="black", bd=5)
        aprsFrame.place(relx=0.5,rely=0.55, relwidth=0.85, relheight=0.4, anchor='n')

        self.aprstitleLabel = tk.Label(aprsFrame, font=10, text="APRS Messages")
        self.aprstitleLabel.place(relx=0.05, relwidth=0.9,relheight=0.1)
       
        self.aprstypelabel = Label(aprsFrame, text="APRS Message Type", justify="left")
        self.aprstypelabel.place(relx=0.01, rely=0.14,relwidth=0.3, relheight=0.1)
 
        self.combo = Combobox(aprsFrame, state='readonly')
        self.combo.bind('<<ComboboxSelected>>', self.comboChange)    
        self.combo['values']= ("Email", "SMS", "APRS")
        self.combo.current(0) #set the selected item
        self.combo.place(relx=0.42, rely=0.14, relwidth=0.3, relheight=0.1)
 
        self.lbl1 = Label(aprsFrame, text="JS8Call Mode", justify="left")
        self.lbl1.place(relx=0.01, rely=0.27)
 
        self.combo2 = Combobox(aprsFrame, state='readonly')
        self.combo2['values']= ("Normal")
        self.combo2.current(0) #set the selected item
        self.combo2.place(relx=0.42, rely=0.27, relwidth=0.3)
 
        self.callLbl = Label(aprsFrame, text="Enter Email Address", justify="left")
        self.callLbl.place(relx=0.01, rely=0.41)
 
        self.tocall = Entry(aprsFrame,width=37)
        self.tocall.place(relx=0.42, rely=0.41, relwidth=0.5)
 
        self.msgLabel = Label(aprsFrame, text="Message Text", justify="left")
        self.msgLabel.place(relx=0.01, rely=0.56)
 
        self.st = ScrolledText(aprsFrame, height=5)
        self.st.place(relx=0.35, rely=0.56, relwidth=0.6)

        self.btn = Button(aprsFrame, text="Set JS8Call Text", command=self.setAPRSMessage, width=20)
        self.btn.place(relx=0.01, rely=0.69, relwidth=0.3)

        self.btn2 = Button(aprsFrame, text="TX With JS8Call", command=self.txAPRSMessage, width=20)
        self.btn2.place(relx=0.01, rely=0.83, relwidth=0.3)
        
        self.note1label = Label(aprsFrame, text="Click Set JS8Call text to set the message text in JS8Call", justify="center", wraplength=300)
        self.note1label = Label(aprsFrame, text="Click TX with JS8Call to set the message text in JS8Call and start transmitting", justify="center", wraplength=300)

        self.update_timer()
        self.update_status_timer()
        
        self.buildMenu()
        
        self.mainWindow.mainloop()
    
    def cb(self):
        None
        #if self.autoGridToJS8Call.get()==0:
          #  self.autoGridToJS8Call.set(1)
        #else:
         #   self.autoGridToJS8Call.set(0)
            #self.timerStr.set("Timer Not Active")
            
    def update_timer(self):
        if self.autoGridToJS8Call.get()==0:
            self.initTimer()
            self.timerStr.set("Timer Not Active")
            
        if self.autoGridToJS8Call.get()==1:
            
            if self.timer<=0:
                self.initTimer()
            self.timer=self.timer-1
            t="Timer: " + str(self.timer)
            self.timerStr.set(t)
            
            if self.timer<=0:
                gridstr = self.getGrid()
                
                combotext=self.autocombo.get()

                if gridstr!=None and gridstr!='':
                    if combotext=="Auto update JS8Call Grid":
                        self.sendGridToJS8Call(gridstr)
                    if combotext=="Auto TX Grid to APRSIS":    
                        self.sendGridToALLCALL(gridstr)
                        
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
        print('server ip and port:', ':'.join(map(str, addr)))

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
        message = self.to_message(*args, **kwargs)
        print('sending outgoing message:', message)
        self.sock.sendto(message.encode(), self.reply_to)
    
    
    def sendMessageAndClose(self,messageType,messageText):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(listen)
        
        content, addr = self.sock.recvfrom(65500)
        #contentString = content.decode()
        
        #try:
        #    message = json.loads(content)
        #except ValueError:
        #    message = {}

        self.reply_to = addr

        if messageType!=None:
            self.send(messageType, messageText)
        
        self.sock.close()


    def sendGridToJS8Call(self, gridText):
        if gpsl.getStatus().startswith('Error'):
            self.showMessage(MSG_ERROR, gpsl.getStatus())
            return
        if gridText==None:
            return
        print('Sending Grid to JS8CAll...',gridText) 
        self.sendMessageAndClose(TYPE_STATION_SETGRID, gridText)
        UDP_ENABLED=False
        
    def sendGridToALLCALL(self,gridText):
        if gpsl.getStatus().startswith('Error'):
            self.showMessage(MSG_ERROR, gpsl.getStatus())
            return
        if gridText==None:
            return
        messageToSend = TXT_ALLCALLGRID + gridText
        print("Sending ", messageToSend)
        self.sendMessageAndClose(TYPE_TX_GRID, messageToSend)
    
    def getGrid(self):
        print('Getting Grid from GPS')
        gpsText = gpsl.getMaidenhead()
        if gpsText==None:
            gpsText = "No Fix"
            
        ngr = gpsl.get_ngr()
        
        if gpsText!=None:
            if gpsText=='None':
                gpsText="No Fix"
            #print("Got Grid "+gpsText)
        if ngr!=None:
            None
            #print("Got NGR "+ngr)
        if gpsl.getStatus().startswith('Error'):
            gpsText=gpsl.getStatus()
        self.var1.set(gpsText)
                
        if gpsText!= "No Fix" and gpsText!='JJ00aa00':
            self.setJS8CallGridButton.configure(state='normal')
            self.sendJS8CallALLCALLButton.configure(state='normal')
            self.ngrStr.set(ngr)
        else:
            self.setJS8CallGridButton.configure(state='disabled')
            self.sendJS8CallALLCALLButton.configure(state='disabled')
            self.ngrStr.set('No Fix')
            self.var1.set('No Fix')
        
        if gpsText=='JJ00aa00':
            self.ngrStr.set('No Fix')
    
        return gpsText
        
        

try:

    gpsl = gpsdGPSListener.GpsListener()
    gpsl.start()

    ui = UserInterface()
    
    gpsl.setReadGPS(False)
    
finally:
    gpsl.setReadGPS(False)
    gpsl.join()
    


