# Get Out! by Katy Scott, 2017
# Prompts user to input any city in the world. Recommends outdoor activity based
# on weather and ocean data for that location.

from urllib2 import urlopen
from json import load 
from time import sleep, strftime
from datetime import datetime, timedelta
import keys


user_city = raw_input("City: ")
user_city = user_city.replace(" ","_")
user_state = raw_input("State (or country, if outside U.S.): ")
user_state = user_state.replace(" ","_")

WU_apiUrl = "http://api.wunderground.com/api/%s/hourly/q/%s/%s.json" %(keys.WU_api_key, user_state, user_city)
WU_response = urlopen(WU_apiUrl)
weather_data = load(WU_response)

current_temp = weather_data["hourly_forecast"][0]["temp"]["english"]
current_wind = weather_data["hourly_forecast"][0]["wspd"]["english"]
current_rain = weather_data["hourly_forecast"][0]["pop"]
#pull tide data from WU as well


print "Temperature: %s F" % current_temp 
print "Wind speed: %s mph" % current_wind
print "Chance of rain: %s percent" % current_rain


# To get worldwide swell info, pull GPS data from WU, and then pull buoy data 
# based on that from: http://www.ndbc.noaa.gov/activestations.xml

#recommend activity: allow user to prioritize activities