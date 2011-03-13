#!/usr/bin/env python
import os
import sys
import serial
import twitter
import time
import datetime

from optparse import OptionParser

#--- Set up the twitter api to receive information
def TwitterIt(u, p, message):
    postUpdated = False
    count = 0

    #--- Attempt to post up to 5 times
    while not postUpdated and count < 5:
        api = twitter.Api(username=u, password=p)
        try:
            status = api.PostUpdate(message)
            print "\n%s just posted (%s):\n%s\n" % (status.user.name, len(status.text), status.text)
            postUpdated = True
        except UnicodeDecodeError:
            print "\nYour message could not be encoded.  Perhaps it contains non-ASCII characters? "
            print "\nTry explicitly specifying the encoding with the  it with the --encoding flag\n"
        except:
            print "\nCouldn't connect, check network, username and password!\n"
        count += 1

#--- Declare the main program
if __name__ == '__main__':
    
    #--- Get the options from the command line
    usage = "usage: garduino_twitter [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--file",
                      dest="filename",
                      type="string",
                      help="write data to csv FILE",
                      metavar="FILE")
    parser.add_option("-u", "--username",
                      dest="username",
                      type="string",
                      help="the USERNAME to supply to Twitter",
                      metavar="USERNAME")
    parser.add_option("-p", "--password",
                      dest="password",
                      type="string",
                      help="the PASSWORD to supply to Twitter",
                      metavar="PASSWORD")
    parser.add_option("-c", "--com",
                      dest="com",
                      default = "COM5",
                      type="string",
                      help="the COM port for the serial connection",
                      metavar="COM")
    parser.add_option("-b", "--baud",
                      dest="baud",
                      default=19200,
                      type="int",
                      help="the BAUD rate for the serial connection",
                      metavar="BAUD")
    parser.add_option("-t", "--timeout",
                      dest="timeout",
                      default=15,
                      type="int",
                      help="the TIMEOUT for the serial connection in seconds",
                      metavar="TIMEOUT")
    parser.add_option("-d", "--debug",
                      action="store_true",
                      dest="debug",
                      default=False,
                      help="turn on debug to print more information")
    (options, args) = parser.parse_args()

    #--- Declare a file where the data will be saved
    saveToFile = False
    LOGFILENAME = ""
    if options.filename != None:
        saveToFile = True
        LOGFILENAME = options.filename # where we will store our flatfile data

    #--- Twitter username & password
    sendTwitterUpdates = False
    twitterusername = "username"
    twitterpassword = "password"
    if options.username != None and options.password != None:
        sendTwitterUpdates = True
        twitterusername = options.username
        twitterpassword = options.password
    elif options.username != None and options.password == None:
        print "No password supplied!"
    elif options.username == None and options.password != None:
        print "No username supplied!"

    DEBUG = False
    if options.debug:
        DEBUG = True

    #--- Set up the serial port to read from the Xbee
    SERIALPORT = options.com    # the com/serial port the XBee is connected to
    BAUDRATE = options.baud     # the baud rate we talk to the xbee
    TIMEOUT = options.timeout   # the timeout after which the readline will stop  

    #--- A timer for twitter
    twittertimer = 0

    #--- Open the datalogging file
    if saveToFile:
        logfile = open(LOGFILENAME, 'a')
        if not os.path.isfile(LOGFILENAME):
            logfile.write("#light, temp, moisture, time\n");
            logfile.flush()
        
    #--- open up the FTDI serial port to get data transmitted to xbee
    ser = serial.Serial(SERIALPORT, BAUDRATE, timeout=TIMEOUT)
    ser.open()

    #--- Print the serial information once
    if DEBUG:
        print "PORT:\t\t%s\nBAUD:\t\t%s\nBYTESIZE:\t%s\nPARITY:\t\t%s\nSTOPBITS:\t%s\n" \
              %(ser.port, ser.baudrate, ser.bytesize, ser.parity, ser.stopbits)

    #--- Set up a boolean to track reseting the water pump
    waterReset = True

    #--- Loop the program indefinitely
    while True:
        #--- Send the current hour to the arduino
        # Determine the hour of the day (ie 6:42 -> '6')
        currHour = datetime.datetime.now().hour

        lightChar = 'l' # This is off
        if (currHour >=  0  and currHour <= 12) or (currHour >= 22 and currHour <= 23):
            lightChar = 'L' # This is on

        waterChar = 'w' # This does nothing
        if (currHour % 2 == 0) and waterReset:
            waterChar = 'W'
            waterReset = False
        elif (currHour % 2 != 0):
            waterReset = True;
            
        #--- Create the command to send to the arduino
        command = "+++%s%s" % (lightChar,waterChar)
        if DEBUG:
            print "Sending: %s, Current Hour: %s" % (command, currHour)
        if command:
            ser.write(command)
        
        #--- Read in the data and split the line into words
        data = ser.readline()
        words = data.split(';')

        #--- If at least nine fields exists then parse the data
        if data != '\n' and len(words) == 4:
            
            #--- Declare values to set
            light_sensor = 0
            temp_sensor = 0
            moisture_sensor = 0

            #--- For each word set the value
            for pair in words:
                keyAndValue = pair.split(':')
                if len(keyAndValue) >= 2:
                    #--- Get the key and value
                    key = keyAndValue[0]
                    value = keyAndValue[1].strip()
                    
                    #--- Integer numbers should only contain digits
                    if value.isdigit():
                        if key == "light_sensor":
                            light_sensor = int(value)
                        elif key == "temp_sensor":
                            temp_sensor = int(value)
                        elif key == "moisture_sensor":
                            moisture_sensor = int(value)

            #--- Get the difference in time between tweets
            currentTime = time.time()
            diffTime = currentTime - twittertimer
            
            #--- Set up the minimum time difference
            secondsPerMinute = 60.0
            minutesBetweenTweets = 60.0
            minTime = minutesBetweenTweets*secondsPerMinute

            #--- Write a message for twitter
            message = "My Garden: LightSensor: %d, Temp Sensor: %d, Moisture Sensor: %d, Time: %s" \
            % (light_sensor,temp_sensor,moisture_sensor,datetime.datetime.now())

            if DEBUG:
                print "\nDEBUG: %s\n" % (message)

            #--- Tweet if the diff time exceeds the min time
            if (diffTime >= minTime):
                #--- Set the twitter time to the current time
                twittertimer = currentTime;

                #--- Save the data to a file
                if saveToFile:
                    logfile.write("%d,%d,%d,%s\n" \
                        % (light_sensor,temp_sensor,moisture_sensor,datetime.datetime.now()));
                    logfile.flush()
                
                #--- Send the message to twitter
                if sendTwitterUpdates:
                    TwitterIt(twitterusername, twitterpassword, message)
            
