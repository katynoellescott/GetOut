# Get Out! by Katy Scott, 2017
# Prompts user to input any city in the world. Recommends outdoor activity based
# on weather and ocean data for that location.

from urllib2 import urlopen
from json import load 
import xml.etree.ElementTree as ET
import csv
from time import sleep, strftime
from datetime import datetime, timedelta, time
import keys


# def input_location():
#     '''Prompts user to input location'''
#     location_dict = {'City': '', 'State': ''}
#     user_city = raw_input("City: ")
#     location_dict['City'] = user_city.replace(" ","_")
#     user_state = raw_input("State: ")
#     location_dict['State'] = user_state.replace(" ","_")
#     return location_dict


def access_weather(location):
    '''Pulls current temperature, wind speed, rain probability of user-input
    location, from Weather Underground API.'''

    current_weather = {'Temperature': '', "Wind Speed": '', "Chance of Rain": ''}

    WU_apiUrl = "http://api.wunderground.com/api/%s/hourly/q/%s/%s.json" %(keys.WU_api_key, location['State'], location['City'])
    WU_response = urlopen(WU_apiUrl)
    weather_data = load(WU_response)
    #data returned as JSON dictionary

    current_temp = weather_data["hourly_forecast"][0]["temp"]["english"]
    current_wind = weather_data["hourly_forecast"][0]["wspd"]["english"]
    current_rain = weather_data["hourly_forecast"][0]["pop"]

    current_weather["Temperature"] = float(current_temp)
    current_weather["Wind Speed"] = float(current_wind)
    current_weather["Chance of Rain"] = float(current_rain)

    return current_weather


def access_weather_conditions(location):
    '''Current weather returned as JSON from Weather Underground'''
    WU_conditionsUrl = "http://api.wunderground.com/api/%s/conditions/q/%s/%s.json" % (keys.WU_api_key, location['State'], location['City'])
    WU_conditions_response = urlopen(WU_conditionsUrl)
    conditions_data = load(WU_conditions_response)
    return conditions_data


def access_rain_history(location, conditions):
    '''Pulls precipitation totals in Pacific Grove for past 48 hours from
    Weather Underground API'''

    yesterday = (datetime.now() - timedelta(1)).strftime('%Y%m%d')

    # data returned as JSON 
    WU_historyUrl = "http://api.wunderground.com/api/%s/history_%s/q/%s/%s.json" % (keys.WU_api_key, yesterday, location['State'], location['City'])
    WU_history_response = urlopen(WU_historyUrl)
    weather_history = load(WU_history_response)


    rain_yesterday = weather_history["history"]["observations"][0]["precipi"]
    rain_yesterday = float(rain_yesterday)
    if rain_yesterday < 0:
        rain_yesterday = 0

    #pull total precipitation today from conditions API
    rain_today = conditions["current_observation"]["precip_today_in"]
    rain_today = float(rain_today)
    if rain_today < 0:
        rain_today = 0

    rain_total = rain_yesterday + rain_today
    return rain_total


def get_GPS(conditions):
    location_GPS = {'Latitude': '', 'Longitude': ''}
    latitude = conditions["current_observation"]["observation_location"]["latitude"]
    latitude = float(latitude)
    latitude = round(latitude, 1)
    location_GPS["Latitude"]= latitude
    longitude = conditions["current_observation"]["observation_location"]["longitude"]
    longitude = float(longitude)
    longitude = round(longitude, 1)
    location_GPS["Longitude"]= longitude
    return location_GPS


def locate_buoy(GPS):
    buoy_id = None #if no buoy at location, returns none
    buoyUrl = "http://www.ndbc.noaa.gov/activestations.xml"
    buoy_response = urlopen(buoyUrl)
    tree = ET.parse(buoy_response)
    root = tree.getroot()
    for child in root:
        buoy_dict = child.attrib
        buoy_lat = float(buoy_dict['lat'])
        buoy_lat = round(buoy_lat, 1)
        buoy_long = float(buoy_dict['lon'])
        buoy_long = round(buoy_long, 1)
        if buoy_lat == GPS['Latitude'] and buoy_long == GPS['Longitude']:
            buoy_id = buoy_dict['id']
            buoy_id = buoy_id.upper()
            break
    return buoy_id


def access_wave_data(buoy):
    '''Pulls wave data from NOAA buoy'''

    ocean_data = {'Water Temperature': '','Wave Height': '','Swell Height':'','Swell Period':'', 'Wave Direction': '', 'Yesterday Swell': ''}
    raw_waveUrl = "http://www.ndbc.noaa.gov/data/realtime2/%s.txt" % buoy

    try:
        raw_wave_data = urlopen(raw_waveUrl)

    except:
        return ocean_data
    
    wave_list = csv.DictReader(raw_wave_data, delimiter=' ', skipinitialspace=True)
    for row in wave_list:
        try:
            current_temp_C = float(row['WTMP'])
            ocean_data['Wave Height'] = float(row['WVHT'])
            ocean_data['Wave Direction'] = float(row['MWD'])
            break
        except: #Google python exceptions, can be more specific to a certain error
            # probably wasn't a float stored there
            pass
    ocean_data['Water Temperature'] = (current_temp_C * 1.8) + 32 #convert to Fahrenheit
    return ocean_data


def access_swell_data(buoy):
    '''Pulls swell data from NOAA buoy'''
    ocean_data = access_wave_data(buoy)
    raw_swellUrl = "http://www.ndbc.noaa.gov/data/realtime2/%s.spec" % buoy
    try:
        raw_swell_data = urlopen(raw_swellUrl)
    except:
        return ocean_data

    latest_hr = None
    latest_min = None
    swell_list = csv.DictReader(raw_swell_data, delimiter=' ', skipinitialspace=True)
    for row in swell_list:
        if latest_hr == None and latest_min == None:
            try:   
                ocean_data['Swell Height'] = float(row['SwH'])
                ocean_data['Swell Period'] = float(row['SwP'])  
                latest_hr = row['hh']
                latest_min = row['mm']
            except:
                # probably wasn't a float stored there
                pass
        elif latest_hr == row['hh'] and latest_min == row['mm']:
            ocean_data['Yesterday Swell'] = float(row['SwH'])
            break

    return ocean_data


def calculate_visibility(rain, weather_data, ocean_data):
    '''use rain, swell and wind info from past days to predict underwater visibility'''
    
    if ocean_data['Swell Height'] == "":
        return "poor"
    elif rain >= 0.3: #any rain is bad for visibility, but WU occassionally records 0.1-0.2 precipitation just from fog
        return "poor"
    elif ocean_data['Swell Height'] > 5 or ocean_data['Yesterday Swell'] > 5: #in Monterey Bay, most divers on forums agree that best vis happens around this threshold
        return "poor"
    #add swell data from 24 hours ago here
    elif weather_data['Wind Speed'] > 15: #faster winds means more waves, but it's always a little windy in Monterey Bay
        return "poor"
    else:
        return "good"


def calculate_chop(ocean_data):
     """use swell period and wind direction to predict chopiness"""
     period = ocean_data['Swell Period']
     direction = ocean_data['Wave Direction']
     height = ocean_data ['Wave Height']
     if period == "":
        return "average"
     elif direction >= 191.25 and direction <= 258.75 and height <= 3: #in Monterey Bay, winds from SW are totally blocked, meaning fewer waves
        return "low" 
     elif direction > 303.75 and direction <326.25 and height > 3: #in Monterey Bay, direct NW winds aren't blocks, so lots of waves
        return "high"
     elif period > 10 and height <= 3: #numbers come from research on dive forums about Monterey Bay
        return "low"
     elif period < 8 and height > 3: #numbers come from research on dive forums about Monterey Bay
        return "high"
     else:
        return "average"



def recommend_sport(user_location):
    """uses weather and surf data to calculate activity recommendation, if/then 
    order is based on personal preference for activities, so if there's a tie,
    the most preferred 
    wins"""

    #user_location = input_location()  #returns user-input city, state
    conditions = access_weather_conditions(user_location) #returns raw data from WU
    GPS = get_GPS(conditions) #returns GPS as dict
    weather_dict = access_weather(user_location) #returns current weather by city, state
    rain_history = access_rain_history (user_location, conditions)
    buoy_id = locate_buoy(GPS) #returns buoy station id or none, if no buoys

    if buoy_id != None: #change this to check for empty swell data?

        ocean_dict = access_swell_data(buoy_id) #returns ocean conditions as dict
        chop = calculate_chop(ocean_dict)
        visibility = calculate_visibility(rain_history, weather_dict, ocean_dict)
        
        if weather_dict["Temperature"] < 40 or weather_dict["Chance of Rain"] > 24:
            return "stay_in_bed" 
        elif ocean_dict["Water Temperature"] > 49 and rain_history <= 0.3:
            if chop == "low" and visibility == "good":
                return "snorkel"
            elif chop == "high":
                return "boogie_board"
            elif chop == "low": 
                return "swim"
            elif weather_dict["Wind Speed"] < 10:
                return "ride_bike"
            else:
                return "stay_in_bed"
        elif weather_dict["Wind Speed"] < 10:
            return "ride_bike"
        else:
            return "stay_in_bed"
 
    elif buoy_id == None:
        if weather_dict["Temperature"] < 40 or weather_dict["Chance of Rain"] > 24:
            return "stay_in_bed" 
        elif weather_dict["Wind Speed"] < 10:
                return "ride_bike"
        else:
            return "stay_in_bed"


def send_to_bit(location):
    """sends recommended sport to IFTTT.com, which translates it to a percentage
    turn of the servo motor, and sends that action to the Cloud Bit to implement"""
    recommendation = recommend_sport(location)
    cloud_bit_call = "https://maker.ifttt.com/trigger/%s/with/key/%s" %(recommendation, keys.ifttt_key)
    urlopen(cloud_bit_call).read()
    return recommendation


