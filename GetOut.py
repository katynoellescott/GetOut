#Get Out! by Katy Scott, 2017

from urllib2 import urlopen
from json import load 
from time import sleep
import keys


#if no new input, use while loop to repeat calculations and recommendations 
#functions, with default input of PG, every 5 minutes -- use sleep(300)

# import weather API
# pull location-based data on:
# temperature
# precipitation
# wind
# WU can only make 500 calls per day, so only call every 3 minutes (or less frequent, but don't call at night)

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



# import surf API
# pull location-based data on:
# water temperature
# swell
# wave height
# wind direction
# To get worldwide swell info, pull GPS data from WU, and then pull buoy data 
# based on that from: http://www.ndbc.noaa.gov/activestations.xml



# raw_water_temp_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.txt").read()
# print water_temp_data

# swell_data = {'Wave Height': '', 'Swell Height':'','Swell Period':''}

# raw_swell_data = urlopen("http://www.ndbc.noaa.gov/data/realtime2/46240.spec").read()
# swell_rows_list = raw_swell_data.split('\n')
# current_swell = swell_rows_list[2].split(' ')

# swell_data['Wave Height'] = float(current_swell[6])
# swell_data['Swell Height'] = float(current_swell[8])
# swell_data['Swell Period'] = float(current_swell[9])

# print swell_data




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
    #if time, allow user to prioritize activities
    if float(current_temp) < 40 or float(current_rain) > 24:  #or water temperature is really cold:
        return "stay_in_bed" 
#     elif good visibility and calm water:
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
