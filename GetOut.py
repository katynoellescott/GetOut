# Get Out! by Katy Scott, 2017
# Pulls weather and ocean data for Pacific Grove, CA, and feeds it to an activity
# clock that recommends an outdoor activity.

from urllib2 import urlopen
from json import load 
from time import sleep, strftime
from datetime import datetime, timedelta
import keys


def access_weather():
    '''Pulls Pacific Grove current temperature, wind speed, rain probability 
    from Weather Underground API.'''

    current_weather = {'Temperature': '', "Wind Speed": '', "Chance of Rain": ''}

    WU_apiUrl = "http://api.wunderground.com/api/%s/hourly/q/CA/Pacific_Grove.json" % keys.WU_api_key
    WU_response = urlopen(WU_apiUrl)
    weather_data = load(WU_response)

    current_temp = weather_data["hourly_forecast"][0]["temp"]["english"]
    current_wind = weather_data["hourly_forecast"][0]["wspd"]["english"]
    current_rain = weather_data["hourly_forecast"][0]["pop"]

    current_weather["Temperature"] = float(current_temp)
    current_weather["Wind Speed"] = float(current_wind)
    current_weather["Chance of Rain"] = float(current_rain)

    return current_weather


# def access_tide(current_tide):
#     '''Pulls Pacific Grove current tide height from Weather Underground API'''



def access_rain_history():
    '''Pulls precipitation totals in Pacific Grove for past 48 hours from
    Weather Underground API'''

    yesterday = (datetime.now() - timedelta(1)).strftime('%Y%m%d')

    WU_historyUrl = "http://api.wunderground.com/api/%s/history_%s/q/CA/Pacific_Grove.json" % (keys.WU_api_key, yesterday)
    WU_history_response = urlopen(WU_historyUrl)
    weather_history = load(WU_history_response)

    rain_yesterday = weather_history["history"]["observations"][0]["precipi"]
    rain_yesterday = float(rain_yesterday)
    if rain_yesterday < 0:
        rain_yesterday = 0

    WU_conditionsUrl = "http://api.wunderground.com/api/%s/conditions/q/CA/Pacific_Grove.json" % keys.WU_api_key
    WU_conditions_response = urlopen(WU_conditionsUrl)
    conditions = load(WU_conditions_response)

    rain_today = conditions["current_observation"]["precip_today_in"]
    rain_today = float(rain_today)
    if rain_today < 0:
        rain_today = 0

    rain_total = rain_yesterday + rain_today
    return rain_total



def access_ocean_data():
    '''Pulls Pacific Grove ocean data from NOAA buoy, updated every 30 minutes.'''

    ocean_data = {'Water Temperature': '','Wave Height': '','Swell Height':'','Swell Period':''}

    raw_temp_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.txt")
    raw_temp_data.readline()  # Throw away line 1
    raw_temp_data.readline()  # Throw away line 2
    current_temp_data = raw_temp_data.readline().strip().split(' ')
    current_temp_C = float(current_temp_data[35])
    current_temp = (current_temp_C * 1.8) + 32 #convert to Fahrenheit

    raw_swell_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.spec")
    raw_swell_data.readline()  # Throw away line 1
    raw_swell_data.readline()  # Throw away line 2
    current_swell = raw_swell_data.readline().strip().split(' ')

    ocean_data['Water Temperature'] = current_temp
    ocean_data['Wave Height'] = float(current_swell[6])
    ocean_data['Swell Height'] = float(current_swell[8])
    ocean_data['Swell Period'] = float(current_swell[9])

    return ocean_data




# def calculate_visibility():
#     use rain, swell and wind info from past days to predict visibility:
        # if rain in past 48 hours, BAD visibility
        # if large swell (> 5), BAD visibility 
        # if strong winds, BAD visibility
        # if tides...


# def calculate_chop():
#     use swell, wind and wave height to predict chopiness



def recommend_sport():
    """uses weather and surf data to calculate activity recommendation, puts 
    recommendations in order of preference, so if there's a tie the most preferred 
    wins"""
    
    if float(current_temp) < 40 or float(current_rain) > 24:  #or water temperature is really cold:
        return "stay_in_bed" 
#     elif good visibility and calm water:
#           Swell height: 3 feet or less
#           Wave height: 2 feet or less
#           Fewer waves = good
#           Less wind = good
#         return snorkel
#     elif blown-out waves and lots of wind:
#         return boogie_board
#     elif calm water (but none of the above are good):
#         return swim
    elif float(current_wind) < 10:
        return "ride_bike"
    else:
        return "stay_in_bed"
    

def send_to_bit():
    """sends recommended sport to IFTTT.com, which translates it to a percentage
    turn of the servo motor, and sends that action to the Cloud Bit to implement"""
    recommendation = recommend_sport()
    cloud_bit_call = "https://maker.ifttt.com/trigger/%s/with/key/%s" %(recommendation, keys.ifttt_key)
    urlopen(cloud_bit_call).read()
