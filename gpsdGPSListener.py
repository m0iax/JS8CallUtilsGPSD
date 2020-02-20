'''
Created on 21 May 2019
JS8CallGPSUI Copyright 2019 M0IAX
@author: Mark Bumstead M0IAX
http://m0iax.com
'''

from OSGridConverter import latlong2grid 
import threading
from gps import *
import time
import os
import maidenhead as mh
import sys

exitFlag=False

def setexit(flag):
    exitFlag=flag
    
class GpsListener(threading.Thread):

   def __init__(self):
       threading.Thread.__init__(self)
       self.current_ngr = None
       self.current_lon = None
       self.current_lat = None
       self.current_gpstime = None
       self.current_gpstime =  None
       self.current_mhgrid = "No Fix"
       self.current_latlon = None
       self.runFlag=True
       self.enabled=False
       
       self.session = gps(mode=WATCH_ENABLE)
       
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
       self.current_latlon = self.current_lat, self.current_lon
       return self.current_latlon
   def get_current_gpstime(self):
       return self.current_gpstime
   def get_current_mhgrid(self):
       return self.current_mhgrid
   def getMaidenhead(self):
       return self.current_mhgrid 
   def get_current_ngr(self):
       return self.current_ngr
    
   def setrun(self,flag):
       print("Shutting down gps listener. Please wait...")
       self.runFlag=flag
       

   def run(self):
       try:
            while self.runFlag:

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
                        
                        grid = mh.toMaiden(lat, lon, precision=4)
                        
                        #grid = mh.toMaiden(lat, lon, 4)
                        self.current_lat = lat
                        self.current_lon = lon
                        self.current_gpstime = gpstime
                        self.current_mhgrid = grid
                        currentMHGrid = grid
                        
                        try:
                            if grid != 'JJ00aa00':
                                g=latlong2grid(lat,lon)
                                self.current_ngr = str(g)
                            else:
                                self.current_ngr = ''
     
                        except:
                            self.current_ngr = ''
 
                time.sleep(1)
                
                
                
       except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            print ("\nKilling Thread...")
            self.runFlag = False
            self.join() # wait for the thread to finish what it's doing
            print ("Done.\nExiting.")

gpsl = GpsListener()
print("Starting GPS Listener")
gpsl.start()

