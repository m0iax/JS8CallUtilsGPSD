# JS8CallUtilsGPSD

This project is designed for use with JS8Call by Jordan KN4CRD - http://js8call.com

This version will work on a Raspberry Pi (or computers running a unix OS) with the GPSD service configured. If not configured then the GPS features will not be available.

If you have a GPS connected to your computer it will allow you to send your maidenhead grid to JS8Call to set its locator
and/or to transmit to @APRSIS

It also allows you to send messages into the ARRS system, APRS, Email or SMS message types.

To use, download the files, ensure you have python version 3 installed and install the follwoing dependencies
enter the following on the command line:

pip3 install maidenhead
pip3 install serial
pip3 install configparser
pip3 install gps

on unix now enter
chmod +x js8callutilsGPSD.py

you should now be ready to run the app 

./js8callutilsGPSD.py

On first run it will create two new files in its directory.
(note do not change the formatting, only update the value - if you get it wrong just delete the file and the app will re-create
it next time its run)

gps.cfg
js8call.cfg

In gps.cfg you can set the precision of the Maidenhead grid, the higher the number the greater the precision of the grid. 
Typically set this to 4, 5 or 6

in js8call.cfg you can set

autotimeperiod - this is the time in minutes between auto updates to js8call
autoonatstart - when 0 auto is off at start, if 1 then auto is enabled on startup
autoselectedoption - 0 = the first option (Send Grid to JS8Call) is selected at startup, 1 = the second option (Transmit Grid) is selected

there is also a setting for the JS8Call UDP port, this is noramlly 2242, only change this if you have updated it in JS8Call's settings.



