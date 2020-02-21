'''
Created on 21 May 2019
JS8CallGPSUI Copyright 2019 M0IAX
@author: Mark Bumstead M0IAX
http://m0iax.com
'''

#from OSGridConverter import latlong2grid 
import threading
from gps import *
import time
import os
import maidenhead as mh
import sys
import configparser

exitFlag=False
configfilename=sys.path[0]+"/gps.cfg"

def setexit(flag):
    exitFlag=flag
    
class GpsListener(threading.Thread):
    def setReadGPS(self, set):
       self.readGPS=set
    def __init__(self):
        try:
            threading.Thread.__init__(self)
            self.readGPS=False
            self.status=""
            self.current_ngr = None
            self.current_lon = None
            self.current_lat = None
            self.current_gpstime = None
            self.current_gpstime =  None
            self.current_mhgrid = "No Fix"
            self.current_latlon = None
            self.runFlag=True
            self.enabled=False
            self.locator_precision=self.getLocatorPrecision()
            self.session = gps(mode=WATCH_ENABLE)
            self.readGPS=True
       
        except:
            self.setStatus("Error initilizing GPS, check com port and restart this app.")
    def getSettingValue(self,section,setting):
        global configfilename    
        
        self.createConfigFile(configfilename)
        val = None
        if os.path.isfile(configfilename):
            config = configparser.ConfigParser()
            config.read(configfilename)
            val=config.get(section, setting)
        
        return val
        
    def getLocatorPrecision(self):
        
        prec=self.getSettingValue('LOCATOR', 'precision')
            
        p = 4
        if prec!=None:
            p=int(prec)
            
        return p
    
    def getComportName(self):

        comport = self.getSettingValue('HARDWARE','gpscomport')
        
        if comport==None: #and platform.system()==platform_windows:
            comport = 'COM8'
    
        return comport
    
    def createConfigFile(self, configFileName):
        #cretes the config file if it does not exist
        if not os.path.isfile(configFileName):
            
            config = configparser.ConfigParser()
            config['HARDWARE'] = {'gpscomport': 'COM8'
                              }
            config['LOCATOR'] = {'precision': 4
                              }
            
            with open(configFileName, 'w') as configfile:
                config.write(configfile)
                configfile.close()    
    def setStatus(self, statusString):
        self.status=statusString  
    def getStatus(self):
        return self.status
    
    def set_enabled(self,flag):
        self.enabled=flag
    def get_enabled(self):
        return self.enabled
    def set_exitFlag(self,flag):
        self.exitflag=flag
    def get_current_lon(self):
        return self.current_lon
    def get_current_lat(self):
        return self.current_lat
    def get_current_latlon(self):
        self.current_latlon = self.current_lat+" "+self.current_lon
        return self.current_latlon
    def get_current_gpstime(self):
        return self.current_gpstime
    def get_current_mhgrid(self):
        return self.current_mhgrid
    def getMaidenhead(self):
        return self.current_mhgrid 
    def get_current_ngr(self):
        #return self.current_ngr
        return get_current_latlon()
    def get_ngr(self):
        #return self.current_ngr
        return ""
    def setrun(self,flag):
        print("Shutting down gps listener. Please wait...")
        self.runFlag=flag
       

    def run(self):
        try:
            while self.readGPS:
                if self.locator_precision==None:
                    self.locator_precision=4
                    
                data = self.session.next()
                #print(data)
                if data['class'] == 'TPV':
                    
                    lat= getattr(data,'lat',0.0)
                    lon = getattr(data, 'lon', 0.0)
#            
                    gpstime = getattr(data,'time', 0)
#
                    if gpstime=="0":
                        self.currentmhgrid="No Fix"
                    else:
                        latlon = (lat,lon)
                        
                        grid = mh.toMaiden(lat, lon, precision=self.locator_precision)
                        
                        self.current_lat = lat
                        self.current_lon = lon
                        self.current_gpstime = gpstime
                        self.current_mhgrid = grid
                        currentMHGrid = grid
                        
                        #try:
                        #    if grid != 'JJ00aa00':
                                #g=latlong2grid(lat,lon)
                                #self.current_ngr = str(g)
                        #    else:
                        #        self.current_ngr = ''
     
                        #except:
                        #    self.current_ngr = ''
 
                time.sleep(1)
                
                
                
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            print ("\nKilling Thread...")
            self.runFlag = False
            self.join() # wait for the thread to finish what it's doing
            print ("Done.\nExiting.")


if __name__ == "__main__":
    try:
        gpsl = GpsListener()
        gpsl.start()    
        #gpsl.setReadGPS(False)
    except (KeyboardInterrupt, SystemExit):
        gpsl.setReadGPS(False)
        print("Done.\nClosing GPS Listener.")

