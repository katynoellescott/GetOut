# Get Out! by Katy Scott, 2017
# Pulls weather and ocean data for Pacific Grove, CA, and feeds it to an activity
# clock that recommends an outdoor activity.
# On web server, add cron job to run every 30 minutes, to update data

from urllib2 import urlopen
from json import load 
import csv
from time import sleep, strftime
from datetime import datetime, timedelta, time
import keys

def access_weather():
    '''Pulls Pacific Grove current temperature, wind speed, rain probability 
    from Weather Underground API.'''

    current_weather = {'Temperature': '', "Wind Speed": '', "Chance of Rain": ''}

    WU_apiUrl = "http://api.wunderground.com/api/%s/hourly/q/CA/Pacific_Grove.json" % keys.WU_api_key
    WU_response = urlopen(WU_apiUrl)
    weather_data = load(WU_response)
    # data returned as JSON dictionary

    current_temp = weather_data["hourly_forecast"][0]["temp"]["english"]
    current_wind = weather_data["hourly_forecast"][0]["wspd"]["english"]
    current_rain = weather_data["hourly_forecast"][0]["pop"]

    current_weather["Temperature"] = float(current_temp)
    current_weather["Wind Speed"] = float(current_wind)
    current_weather["Chance of Rain"] = float(current_rain)

    return current_weather


def access_rain_history():
    '''Pulls precipitation totals in Pacific Grove for past 48 hours from
    Weather Underground API'''

    yesterday = (datetime.now() - timedelta(1)).strftime('%Y%m%d')

    WU_historyUrl = "http://api.wunderground.com/api/%s/history_%s/q/CA/Pacific_Grove.json" % (keys.WU_api_key, yesterday)
    WU_history_response = urlopen(WU_historyUrl)
    weather_history = load(WU_history_response)
    # data returned as JSON dictionary

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

    ocean_data = {'Water Temperature': '','Wave Height': '','Swell Height':'','Swell Period':'', 'Wave Direction': '', 'Yesterday Swell': ''}

    raw_temp_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.txt")
    r = csv.DictReader(raw_temp_data, delimiter=' ', skipinitialspace=True)
    for row in r:
        try:
            current_temp_C = float(row['WTMP'])
            break
        except: #Google python exceptions, can be more specific to a certain error
            # probably wasn't a float stored there
            pass
    ocean_data['Water Temperature'] = (current_temp_C * 1.8) + 32 #convert to Fahrenheit

    latest_hr = None
    latest_min = None
    raw_swell_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.spec")
    r = csv.DictReader(raw_swell_data, delimiter=' ', skipinitialspace=True)
    for row in r:
        if latest_hr == None and latest_min == None:
            try:
                ocean_data['Wave Height'] = float(row['WVHT'])
                ocean_data['Swell Height'] = float(row['SwH'])
                ocean_data['Swell Period'] = float(row['SwP'])
                ocean_data['Wave Direction'] = float(row['MWD'])
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
    
    if rain >= 0.3: #any rain is bad for visibility, but WU occassionally records 0.1-0.2 precipitation just from fog
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
     if direction >= 191.25 and direction <= 258.75 and height <= 3: #in Monterey Bay, winds from SW are totally blocked, meaning fewer waves
        return "low" 
     elif direction > 303.75 and direction <326.25 and height > 3: #in Monterey Bay, direct NW winds aren't blocks, so lots of waves
        return "high"
     elif period > 10 and height <= 3: #numbers come from research on dive forums about Monterey Bay
        return "low"
     elif period < 8 and height > 3: #numbers come from research on dive forums about Monterey Bay
        return "high"
     else:
        return "average"


def check_time():
    now = datetime.now()
    now_time = now.time()
    if time(7,00) <= now_time <= time(22,00): 
        return False
    else:
        return True


def recommend_sport():
    """uses weather and surf data to calculate activity recommendation, if/then 
    order is based on personal preference for activities, so if there's a tie,
    the most preferred 
    wins"""

    weather_dict = access_weather()
    ocean_dict = access_ocean_data()
    rain_history = access_rain_history()
    chop = calculate_chop(ocean_dict)
    visibility = calculate_visibility(rain_history, weather_dict, ocean_dict)
    bedtime = check_time()

    
    if weather_dict["Temperature"] < 40 or weather_dict["Chance of Rain"] > 24 or bedtime == True:
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

def send_to_bit():
    """sends recommended sport to IFTTT.com, which translates it to a percentage
    turn of the servo motor, and sends that action to the Cloud Bit to implement"""
    recommendation = recommend_sport()
    cloud_bit_call = "https://maker.ifttt.com/trigger/%s/with/key/%s" %(recommendation, keys.ifttt_key)
    urlopen(cloud_bit_call).read()


def main():
    send_to_bit()


if __name__ == '__main__':
    main()
