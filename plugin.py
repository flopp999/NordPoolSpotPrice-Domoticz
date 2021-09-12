# NordPoolSpotPrice Python Plugin
#
# Author: flopp999
#
"""
<plugin key="NordPoolSpotPrice" name="NordPoolSpotPrice 0.21" author="flopp999" version="0.21" wikilink="https://github.com/flopp999/NordPoolSpotPrice-Domoticz" externallink="https://www.nordpoolgroup.com/api/marketdata/page/10">
    <description>
        <h2>NordPoolSpotPrice is used to read data from https://www.nordpoolgroup.com/api/marketdata/page/10</h2><br/>
        <h2>Support me with a coffee &<a href="https://www.buymeacoffee.com/flopp999">https://www.buymeacoffee.com/flopp999</a></h2><br/>
        <h3>Features</h3>
        <h2>Presentation of data is in kWh and nothing is added eg. TAX, VAT</h2>
        <ul style="list-style-type:square">
            <li>..</li>
        </ul>
        <h3>Configuration</h3>
    </description>
    <params>
        <param field="Mode1" label="Area" width="320px" required="true" default="Identifier">
            <options>
                <option label="AT" value="AT" />
                <option label="BE" value="BE" />
                <option label="DE-LU" value="DE-LU" />
                <option label="DK1" value="DK1" />
                <option label="DK2" value="DK2" />
                <option label="EE" value="EE" />
                <option label="FI" value="FI" />
                <option label="FR" value="FR" />
                <option label="LT" value="LT" />
                <option label="LV" value="LV" />
                <option label="NL" value="NL" />
                <option label="NO Bergen" value="Bergen" />
                <option label="NO Kr.sand" value="Kr.sand" />
                <option label="NO Molde" value="Molde" />
                <option label="NO Oslo" value="Oslo" />
                <option label="NO Tr.heim" value="Tr.heim" />
                <option label="NO Tromsø" value="Tromsø" />
                <option label="SE1" value="SE1" />
                <option label="SE2" value="SE2" />
                <option label="SE3" value="SE3" />
                <option label="SE4" value="SE4" />
            </options>
        </param>
        <param field="Mode2" label="Divide values by 10(/10) so it will be presented in Öre/Øre/Cent" width="70px">
            <options>
                <option label="Yes" value="Yes" />
                <option label="No" value="No" />
            </options>
        </param>
        <param field="Mode6" label="Debug to file (NordPoolSpotPrice.log)" width="70px">
            <options>
                <option label="Yes" value="Yes" />
                <option label="No" value="No" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
from nordpool import elspot

Package = True

try:
    import requests, json, os, logging
except ImportError as e:
    Package = False

try:
    from logging.handlers import RotatingFileHandler
except ImportError as e:
    Package = False

try:
    from datetime import datetime
except ImportError as e:
    Package = False

dir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger("NordPoolSpotPrice")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(dir+'/NordPoolSpotPrice.log', maxBytes=1000000, backupCount=5)
logger.addHandler(handler)


class BasePlugin:
    enabled = False

    def __init__(self):
        self.hour = 0
        self.CurrentPriceUpdated = False
        self.TodayPriceUpdated = False
        return

    def onStart(self):
        WriteDebug("===onStart===")
        self.Area = Parameters["Mode1"]
        self.Divide = Parameters["Mode2"]

        if len(self.Area) < 3:
            Domoticz.Log("Area too short")
            WriteDebug("Area too short")

        if os.path.isfile(dir+'/NordPoolSpotPrice.zip'):
            if 'NordPoolSpotPrice' not in Images:
                Domoticz.Image('NordPoolSpotPrice.zip').Create()
            self.ImageID = Images["NordPoolSpotPrice"].ID

        if self.Area == "SE1" or "SE2" or "SE3" or "SE4":
            self.currency = "SEK"
            if self.Divide == "Yes":
                self.Unit = "öre"
            else:
                self.Unit = "kronor"
        elif self.Area == "DK1" or "DK2":
            self.currency = "DKK"
            if self.Divide == "Yes":
                self.Unit = "øre"
            else:
                self.Unit = "kroner"
        elif self.Area == "Oslo" or "Kr.sand" or "Bergen" or "Molde" or "Tr.heim" or "Tromsø":
            self.currency = "NOK"
            if self.Divide == "Yes":
                self.Unit = "øre"
            else:
                self.Unit = "kroner"
        else:
            self.curency = "EUR"
            if self.Divide == "Yes":
                self.Unit = "cents"
            else:
                self.Unit = "euro"


    def onHeartbeat(self):
        if CheckInternet() == True:
            HourNow = (datetime.now().hour)
            MinuteNow = (datetime.now().minute)

            if MinuteNow < 59 and self.CurrentPriceUpdated is False:
                WriteDebug("onHeartbeatGetCurrentPrice")
                CurrentPrice(HourNow)
            if MinuteNow == 59 and self.CurrentPriceUpdated is True:
                self.CurrentPriceUpdated = False

            if HourNow >= 0 and MinuteNow >= 2 and MinuteNow < 59 and self.TodayPriceUpdated is False:
                TodayPrice()

            if HourNow == 23 and MinuteNow == 59 and self.TodayPriceUpdated is True:
                self.TodayPriceUpdated = False

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def TodayPrice():
    hour = 0
    prices_spot = elspot.Prices(_plugin.currency)
    price=prices_spot.hourly(end_date=datetime.now().date(),areas=[_plugin.Area])
#    Domoticz.Log(str(price))
    for each,b in price["areas"][_plugin.Area].items():
        if each == "values":
            for each in price["areas"][_plugin.Area]["values"]:
                Domoticz.Log("Hour "+str(hour)+" "+str(round(each["value"]/10.0,1)))
                UpdateDevice(int(hour), each["value"], str("Hour"+" "+str(hour)))
                hour += 1
        elif each == "Min":
            Domoticz.Log(str(each+" "+str(round(b/10.0,1))))
            UpdateDevice(int(24), b, str("Min"))
        elif each == "Max":
            Domoticz.Log(each+" "+str(round(b/10.0,1)))
            UpdateDevice(int(25), b, str("Max"))
        elif each == "Average":
            Domoticz.Log(each+" "+str(round(b/10.0,1)))
            UpdateDevice(int(26), b, str("Average"))
    _plugin.TodayPriceUpdated = True
    Domoticz.Log("Today Price Updated")

def CurrentPrice(CurrentHour):
    hour = 0
    prices_spot = elspot.Prices(_plugin.currency)
    price=prices_spot.hourly(end_date=datetime.now().date(),areas=[_plugin.Area])
    for each,b in price["areas"][_plugin.Area].items():
        if each == "values":
            for each in price["areas"][_plugin.Area]["values"]:
                if hour == CurrentHour:
                    UpdateDevice(int(27), each["value"], str("CurrentPrice"))
                hour += 1
    _plugin.CurrentPriceUpdated = True
    Domoticz.Log("Current Price Updated")

def UpdateDevice(PID, sValue, Name):
    Design="a"
    if PID == 0:
        ID = 1
    if PID == 1:
        ID = 2
    if PID == 2:
        ID = 3
    if PID == 3:
        ID = 4
    if PID == 4:
        ID = 5
    if PID == 5:
        ID = 6
    if PID == 6:
        ID = 7
    if PID == 7:
        ID = 8
    if PID == 8:
        ID = 9
    if PID == 9:
        ID = 10
    if PID == 10:
        ID = 11
    if PID == 11:
        ID = 12
    if PID == 12:
        ID = 13
    if PID == 13:
        ID = 14
    if PID == 14:
        ID = 15
    if PID == 15:
        ID = 16
    if PID == 16:
        ID = 17
    if PID == 17:
        ID = 18
    if PID == 18:
        ID = 19
    if PID == 19:
        ID = 20
    if PID == 20:
        ID = 21
    if PID == 21:
        ID = 22
    if PID == 22:
        ID = 23
    if PID == 23:
        ID = 24
    if PID == 24:
        ID = 25
    if PID == 25:
        ID = 26
    if PID == 26:
        ID = 27
    if PID == 27:
        ID = 28

    if (ID not in Devices):
        if sValue == "-32768":
            Used = 0
        else:
            Used = 1
        Domoticz.Device(Name=Name, Unit=ID, TypeName="Custom", Options={"Custom": "0;"+_plugin.Unit}, Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()

    if (ID in Devices):
        if Devices[ID].sValue != sValue:
            if _plugin.Divide == "Yes":
                Devices[ID].Update(0, str(round(sValue/10.0,1)))
            else:
                Devices[ID].Update(0, str(round(sValue/1000,2)))


def CheckInternet():
    WriteDebug("Entered CheckInternet")
    try:
        WriteDebug("Ping")
        requests.get(url='https://8.8.8.8', timeout=2)
        WriteDebug("Internet is OK")
        return True
    except:
        WriteDebug("Internet is not available")
        return False

def WriteDebug(text):
    if Parameters["Mode6"] == "Yes":
        timenow = (datetime.now())
        logger.info(str(timenow)+" "+text)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
