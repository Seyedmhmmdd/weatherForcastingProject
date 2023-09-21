#!/usr/bin/env python
# coding: utf-8

# ### Python Code Imports

# In[1]:


import requests
from datetime import datetime, timedelta
import sqlite3
import json


# ## Guide for Using the City Selector Class
# 
# The `CitySelector` class is a utility for selecting a city. It offers two methods for this purpose: `getDefaultCity` and `getUserCity`.
# 
# ### `getDefaultCity()`
# 
# - This method automatically fetches the default city based on your access token.
# - If you encounter any issues or errors, it will default to "Tehran."
# 
# ### `getUserCity()`
# 
# - To manually select a city, use this method.
# - When prompted, enter the desired city's name.
# - If you provide a city name, it will be selected; otherwise, it will default to "Tehran."
# 

# In[2]:


class CitySelector:
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json/"

    def getDefaultCity(self) -> str:
        try:
            # Use the ip-api.com API to fetch location information
            response = requests.get(f"{self.ip_api_url}")
            data = response.json()
            city = data.get("city")
            if city:
                return city
            else:
                return "Tehran"  # Default city if no location information is available
        except Exception as e:
            print(f"Error fetching location: {e}")
            return "Tehran"

    def getUserCity(self) -> str:
        city = input("Search city: ").strip()
        return city if city else self.getDefaultCity()

# Preventing unintended execution of code when importing it
if __name__ == "__main__":
    CitySelectorObj = CitySelector()
    city = CitySelectorObj.getUserCity()
    print(f"Selected city: {city}")


# ## Guide for API URL Construction
# 
# The provided code offers a function `constructUrl` for constructing URLs for making API requests. This function takes an `endpoint`, a `baseUrl`, and optional `extraParameters` to build the final URL.
# 

# In[13]:


apiKey: str = "Developer Plan API Key"
baseUrl: str = "http://api.openweathermap.org"

def constructUrl(endpoint: str, baseUrl: str = "http://api.openweathermap.org", extraParameters: dict = None) -> dict:
    parameters: dict = {"appId": apiKey, **(extraParameters or {})}
    url: str = f"{baseUrl}/{endpoint}"
    
    try:
        response: requests.Response = requests.get(url, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None


# ## Guide for Geolocation Data Fetching
# 
# The provided code defines a `GeolocationDataFetcher` class that allows you to fetch geolocation data for a specified city using the OpenWeather API.
# 
# ##### `getGeolocationData`
# 
# - This method retrieves geolocation data for the specified `city` using the OpenWeather API.
# - It constructs the API endpoint and parameters, sends a request, and returns the geolocation data as a dictionary.
# 
# ##### `fetchGeoLocation`
# 
# - This method fetches geolocation data for a given `city` and does not return any data. It's intended for internal use.
# 

# In[4]:


class GeolocationDataFetcher:
    
    def __init__(self):
        self.apiKey: str = apiKey
        self.baseUrl: str = baseUrl
    
    def getGeolocationData(self, city: str) -> dict:
        try:
            geoEndpoint: str = "/geo/1.0/direct"
            geoParameters: dict = {
                 "q": city,
                "limit": "1"
             }
            geoData: dict = constructUrl(endpoint=geoEndpoint, extraParameters=geoParameters)

            if not geoData:
                return None

            geoKeys: list = ["name", "country", "lat", "lon"]
            geoFinalData: dict = {key: geoData[0][key] for key in geoKeys}
            return geoFinalData
        except Exception as e:
            print(f"Error getting geolocation data: {e}")
            return None

        geolocation = getGeolocationData(city)
    
    def fetchGeoLocation(self, city: str) -> None:
        geolocation: dict = self.getGeolocationData(city)
            
fetcher: GeolocationDataFetcher = GeolocationDataFetcher()
geolocationData: dict = fetcher.getGeolocationData(city)

latitude = None
longitude = None

while not (latitude and longitude):
    if geolocationData:
        latitude = geolocationData["lat"]
        longitude = geolocationData["lon"]
        print(f"Latitude: {latitude}, Longitude: {longitude}")
    else:
        print(f"Unable to retrieve geolocation data for {city}")
        latitudeInput = input(f"Enter latitude for {city}: ")
        longitudeInput = input(f"Enter longitude for {city}: ")
    
        if not latitudeInput or not longitudeInput:
            print("Latitude and Longitude are required. Please try again.")
        else:
            try:
                latitude = float(latitudeInput)
                longitude = float(longitudeInput)
                print("Latitude and Longitude received successfully.")
            except ValueError:
                print("Invalid latitude or longitude. Please enter valid numeric values.")


# ## Guide for Air Pollution Data Retrieval and Processing
# 
# The provided code defines a `AirPollutionData` class that retrieves and processes air pollution data based on the provided latitude and longitude coordinates.
# 
# ##### `format_datetime`
# 
# - A static method that formats a Unix timestamp into a human-readable date and time string.
# 
# ##### `currentAirPollution`
# 
# - This method retrieves the current air pollution data for the specified location.
# 
# ##### `processAirPollution`
# 
# - This method processes the raw air pollution data.
# - It also provides a description for the air quality index (AQI) based on predefined thresholds.

# In[5]:


class Base:
    def __init__(self):
        pass

    @staticmethod
    def format_datetime(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


# In[6]:


class AirPollutionData(Base):
    
    def __init__(self, latitude: float, longitude: float):
        super().__init__()
        self.latitude: float = latitude
        self.longitude: float = longitude

    def currentAirPollution(self) -> list:
        try:
            currentAirPollutionEndpoint: str = "/data/2.5/air_pollution"
            currentAirPollutionExtraParameters: dict = {
                "lat": self.latitude,
                "lon": self.longitude
            }

            currentAirPollutionData: dict = constructUrl(
                endpoint=currentAirPollutionEndpoint,
                extraParameters=currentAirPollutionExtraParameters
            )

            if not currentAirPollutionData:
                return None

            currentAirPollutionList: list = currentAirPollutionData["list"]
            currentAirPollutionProcessed: list = self.processAirPollution(currentAirPollutionList)

            return currentAirPollutionProcessed
        
        except Exception as e:
            print(f"Error getting current air pollution data: {e}")
            return None
        
    def processAirPollution(self, currentAirPollutionProcessed: list) -> list:
        for entry in currentAirPollutionProcessed:
            entry["airQualityIndex"] = entry["main"]
            entry["dateTime"] = entry["dt"]

        airPollutionKeys: list = ["airQualityIndex", "components", "dateTime"]
        processedCurrentAirpollution: list = []

        for entry in currentAirPollutionProcessed:
            airQualityInfo: dict = {
                key: (
                    entry.get("airQualityIndex", {}).get("aqi") if key == "airQualityIndex" else
                    entry.get("components", {}) if key == "components" else
                    entry["dateTime"]
                )
                for key in airPollutionKeys
            }

            airQualityInfo["dateTime"] = self.format_datetime(airQualityInfo["dateTime"])

            processedCurrentAirpollution.append(airQualityInfo)


        component_mapping: dict = {
            'co': 'Carbon Monoxide (CO)',
            'no': 'Nitric oxide (NO)',
            'no2': 'Nitrogen dioxide (NO2)',
            'o3': 'Ozone (O3)',
            'so2': 'Sulfur dioxide (SO2)',
            'pm2_5': 'Particulate Matter (PM2.5)',
            'pm10': 'Particulate Matter (PM10)',
            'nh3': 'Ammonia (NH3)'
        }

        def airQualityIndex(aqi: int) -> str:
            if aqi <= 1:
                return "Good"
            elif 1 < aqi <= 2:
                return "Fair"
            elif 2 < aqi <= 3:
                return "Moderate"
            elif 3 < aqi <= 4:
                return "Poor"
            elif aqi >= 5:
                return "Very Poor"
            else:
                return "Unknown"

        for entry in processedCurrentAirpollution:
            aqi: int = entry['airQualityIndex']
            description: str = airQualityIndex(aqi)
            entry['airQualityDescription'] = description

        for entry in processedCurrentAirpollution:
            components: dict = entry['components']
            renamed_components: dict = {component_mapping.get(key, key): value for key, value in components.items()}
            entry['components'] = renamed_components

        return processedCurrentAirpollution

currentAirPollution = AirPollutionData(latitude, longitude)
current_air_pollution: list = currentAirPollution.currentAirPollution()


# ## Guide for Air Pollution Forecast Data Retrieval
# 
# The provided code defines an `AirPollutionForecast` class, allowing you to retrieve air pollution forecast data based on specified latitude and longitude coordinates.
# 
# ##### `airPollutionForecast`
# 
# - This method retrieves air pollution forecast data for the specified location.
# - The forecast data is processed using the `processAirPollution` method from the `AirPollutionData` class.

# In[7]:


class AirPollutionForecast(Base):
    
    def __init__(self, latitude: float, longitude: float):
        super().__init__()         
        self.latitude: float = latitude
        self.longitude: float = longitude

    def airPollutionForecast(self) -> list:
        try:
            airPollutionForecastEndpoint: str = "/data/2.5/air_pollution/forecast"
            airPollutionForecastExtraParameters: dict = {
                "lat": self.latitude,
                "lon": self.longitude
            }
            airPollutionForecastData: dict = constructUrl(
                endpoint=airPollutionForecastEndpoint,
                extraParameters=airPollutionForecastExtraParameters
            )

            if not airPollutionForecastData:
                return None

            airPollutionForcastList: list = airPollutionForecastData["list"][::24]
            airPollutionForecastProcessed: list = AirPollutionData.processAirPollution(self, airPollutionForcastList)

            return airPollutionForecastProcessed
        except Exception as e:
            print(f"Error getting current air pollution data: {e}")
            return None
        

air_pollution_forecast_instance: AirPollutionForecast = AirPollutionForecast(latitude, longitude)
air_pollution_forecast_data: list = air_pollution_forecast_instance.airPollutionForecast()


# ## Guide for Historical Air Pollution Data Retrieval
# 
# The provided code allows you to retrieve historical air pollution data for a specified time range. It prompts the user for start and stop dates and then fetches the relevant data.
# 
# ### User Input (Please Use Correctly)
# 
# - The code first prompts for user input to specify the start and stop dates in the format 'YYYY-MM-DD HH:MM:SS.' Please ensure that you provide valid date and time formats.
# - It's crucial to ensure that the stop date is *after* the start date. The code does not check for this, so please provide the dates in the correct order.
# 
# - If you don't provide a start date, it defaults to a week ago from today.
# - If you don't provide a stop date, it defaults to the current date and time.
# 
# ##### `airPollutionHistory`
# 
# - This method retrieves historical air pollution data for the specified location and time range.
# - The retrieved data is processed using the `processAirPollution` method from the `AirPollutionData` class and returned as a list.
# - Historical data is typically available for every 24 hours within the specified range.
# 

# In[8]:


startDate = input("Enter start date (YYYY-MM-DD HH:MM:SS) or press Enter for default (a week ago from today): ")
if startDate:
    try:
        startDt = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("Invalid date format. Using default start date.")
        startDt = datetime.now() - timedelta(days=7)
else:
    startDt = datetime.now() - timedelta(days=7)

stopDate = input("Enter stop date (YYYY-MM-DD HH:MM:SS) or press Enter for Today: ")
if stopDate:
    try:
        stopDt = datetime.strptime(stopDate, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print("Invalid date format. Using default stop date.")
        stopDt = datetime.now()
else:
    stopDt = datetime.now()

print(f"Start Date: {startDt}")
print(f"Stop Date: {stopDt}")

# Time converting to Unix Zone
startTimestamp: int = int(startDt.timestamp())
stopTimestamp: int = int(stopDt.timestamp())

class AirPollutionHistory:
    def __init__(self, latitude: float, longitude: float, startTimestamp: int, stopTimestamp: int):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.startTimestamp: int = startTimestamp
        self.stopTimestamp: int = stopTimestamp
        self.airPollutionData: AirPollutionData = AirPollutionData(self.latitude, self.longitude) 
        
    def airPollutionHistory(self) -> list:
        
        try:
            airPollutionHistoryEndpoint: str = "/data/2.5/air_pollution/history"
            airPollutionHistoryExtraParameters: dict = {
                    "lat": self.latitude,
                    "lon": self.longitude,
                    "start": self.startTimestamp,
                    "end": self.stopTimestamp
            }

            airPollutionHistoryData: dict = constructUrl(
                airPollutionHistoryEndpoint,
                extraParameters=airPollutionHistoryExtraParameters
            )

            if not airPollutionHistoryData:
                return None

            airPollutionHistoryList: list = airPollutionHistoryData["list"][::24]
            airPollutionHistoryProcessed: list = self.airPollutionData.processAirPollution(airPollutionHistoryList)

            return airPollutionHistoryProcessed

        except Exception as e:
            print(f"Error getting historical air pollution data: {e}")
            return None

air_pollution_history_instance: AirPollutionHistory = AirPollutionHistory(latitude, longitude, startTimestamp, stopTimestamp) 
air_pollution_history_data: list = air_pollution_history_instance.airPollutionHistory() 


# ## Guide for Current Weather Data Retrieval
# 
# The provided code fetches current weather data for a specified location based on latitude and longitude coordinates.
# 
# #### Common Parameters
# 
# The code changes common parameters used for weather data retrieval, including latitude, longitude, units, mode, and the API key.
# 
# ##### `currentWeather`
# 
# - This method retrieves the current weather data for the specified location.
# - The retrieved data is processed and returned as a dictionary containing weather details.
# - The processed data includes information on location, country, weather condition, main features, visibility, wind, and clouds.

# In[9]:


commonParameters: dict = {
    "lat": latitude,
    "lon": longitude,
    "units": "metric",
    "mode": "json",
    "appId": apiKey
}

class CurrentWeather:
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude
        
    def currentWeather(self) -> dict:
        try:
            currentEndpoint: str = "/data/2.5/weather"
            currentExtraParameters: dict = commonParameters

            current: dict = constructUrl(
                currentEndpoint,
                baseUrl="http://pro.openweathermap.org",
                extraParameters=currentExtraParameters
            )

            current["country"] = current["sys"]
            current["condition"] = current["weather"]
            current["mainFeatures"] = current["main"]

            currentKeys: list = ["name", "country", "condition",
                           "mainFeatures", "visibility", "wind", "clouds"]

            currentWeatherData: dict = {
                key: current[key] if key != "country" and key != "condition" else
                (current["condition"][0]["main"] + " - " + current["condition"][0]["description"] if key == "condition"
                 else current["country"]["country"])
                for key in currentKeys
            }
            
            return currentWeatherData
        except Exception as e:
            print(f"Error getting current weather condition: {e}")
            return None


current_weather_instance: CurrentWeather = CurrentWeather(latitude, longitude)
current_weather_data: dict = current_weather_instance.currentWeather()


# ## Guide for Hourly Weather Forecast Data Retrieval
# 
# The provided code fetches hourly weather forecast data for a specified location based on latitude and longitude coordinates.
# 
# ##### `hourlyForecast`
# 
# - This method retrieves hourly weather forecast data for the specified location.
# - Each dictionary includes information on date and time, temperature, and weather condition.
# - The code limits the forecast to the next 25 hours.

# In[10]:


class HourlyWeatherForecast:
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude
        
    def hourlyForecast(self) -> list:
        try:
            hourlyForecastEndpoint: str = "/data/2.5/forecast/hourly"
            hourlyForecastExtraParameters: dict = commonParameters
            hourlyForecastData: dict = constructUrl(
                hourlyForecastEndpoint,
                baseUrl="http://pro.openweathermap.org",
                extraParameters=hourlyForecastExtraParameters
            )

            hourlyForecastList: list = hourlyForecastData["list"][:25]
            hourlyForecastList[0]["Temperature"]: dict = hourlyForecastList[0]["main"]
            hourlyForecastList[0]["weatherCondition"]: dict = hourlyForecastList[0]["weather"]

            hourlyForecastKeys: list = ["dt_txt", "Temperature", "weatherCondition"]
            hourlyForecastedWeatherData: list = []

            for forecastData in hourlyForecastList:
                weatherInfo: dict = {
                    key: (
                        forecastData.get("Temperature", {}).get("temp") if key == "Temperature" else
                        (
                            forecastData.get("weatherCondition", [{}])[0].get("main", "") +
                            " - " +
                            forecastData.get("weatherCondition", [{}])[0].get("description", "")
                        ) if key == "weatherCondition" else
                        forecastData.get(key)
                    )
                    for key in hourlyForecastKeys
                }
                hourlyForecastedWeatherData.append(weatherInfo)
                
            return hourlyForecastedWeatherData
        except Exception as e:
            print(f"Error getting hourly weather forecast: {e}")
            return None

hourly_forecast_instance: HourlyWeatherForecast = HourlyWeatherForecast(latitude, longitude)
hourly_forecast_data: list = hourly_forecast_instance.hourlyForecast()


# ## Guide for Daily Weather Forecast Data Retrieval
# 
# The provided code fetches daily weather forecast data for a specified location based on latitude and longitude coordinates.
# 
# ##### `dailyForecast`
# 
# - This method retrieves daily weather forecast data for the specified location.
# - Each dictionary includes information on the date, daytime and nighttime temperatures, and weather condition.
# - The code fetches forecasts for the next 7 days.

# In[11]:


class DailyWeatherForecast:
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude

    def dailyForecast(self) -> list:
        try:
            dailyForecastEndpoint: str = "/data/2.5/forecast/daily"
            dailyForecastExtraParameters: dict = {
                "lat": self.latitude,
                "lon": self.longitude,
                "cnt": 7
            }

            dailyForecastData: dict = constructUrl(
                endpoint=dailyForecastEndpoint,
                baseUrl="http://pro.openweathermap.org",
                extraParameters=dailyForecastExtraParameters
            )

            if not dailyForecastData:
                return None

            dailyForecasts: list = dailyForecastData["list"]
            dailyForecastedWeather: list = []

            for forecast in dailyForecasts:
                weatherInfo: dict = {
                    "date": datetime.utcfromtimestamp(forecast["dt"]).strftime('%Y-%m-%d'),
                    "temperature": {
                        "day": forecast["temp"]["day"],
                        "night": forecast["temp"]["night"],
                    },
                    "weather": {
                        "main": forecast["weather"][0]["main"],
                        "description": forecast["weather"][0]["description"],
                    }
                }
                dailyForecastedWeather.append(weatherInfo)

            return dailyForecastedWeather

        except Exception as e:
            print(f"Error getting daily weather forecast: {e}")
            return None

daily_forecast_instance: DailyWeatherForecast = DailyWeatherForecast(latitude, longitude)
daily_forecast_data: list = daily_forecast_instance.dailyForecast()


# ## Guide for 5-Days 3-Hours Weather Forecast Data Retrieval
# 
# The provided code fetches 5-days 3-hours weather forecast data for a specified location based on latitude and longitude coordinates.
# 
# ##### `fiveDaysThreeHoursForcast`
# 
# - This method retrieves the 5-days 3-hours weather forecast data for the specified location.
# - The retrieved data is returned as a list of forecasted weather details.
# 
# ##### `processForecastedData`
# 
# - This method processes the raw forecast data obtained from the API.
# - It also renames dictionary keys for clarity.
# 
# ##### `getForecastedData`
# 
# - This method retrieves and processes the 5-days 3-hours weather forecast data.

# In[12]:


class FiveDaysThreeHoursWeatherForecast:
    def __init__(self, latitude: float, longitude: float):
        self.latitude: float = latitude
        self.longitude: float = longitude
        
    def fiveDaysThreeHoursForcast(self) -> list:
        try:
            fiveDaysThreeHoursForcastEndpoint: str = "/data/2.5/forecast"
            fiveDaysThreeHoursForcastExtraParameters: dict = commonParameters
            fiveDaysThreeHoursForcast: dict = constructUrl(
                endpoint=fiveDaysThreeHoursForcastEndpoint,
                baseUrl="http://pro.openweathermap.org",
                extraParameters=fiveDaysThreeHoursForcastExtraParameters
            )

            return fiveDaysThreeHoursForcast["list"] if fiveDaysThreeHoursForcast else []

        except Exception as e:
            print(f"Error retrieving 5-days 3-hours weather forecast data: {e}")
            return []
        
    def processForecastedData(self, forecastList: list) -> list:
        processedForecast: list = []

        for forecastData in forecastList:
            forecastData['dt'] = datetime.utcfromtimestamp(forecastData['dt']).strftime('%Y-%m-%d %H:%M:%S')

            forecastKeys: list = ["dt", "main", "weather"]
            weatherInfo: dict = {}

            for key in forecastKeys:
                if key == "main" and 'temp' in forecastData['main']:
                    weatherInfo[key] = forecastData['main']['temp']
                elif key == "weather":
                    weatherInfo[key] = (
                        forecastData.get("weather", [{}])[0].get("main", "") +
                        " - " +
                        forecastData.get("weather", [{}])[0].get("description", "")
                    )
                else:
                    weatherInfo[key] = forecastData.get(key)

            processedForecast.append(weatherInfo)

        for entry in processedForecast:
            dtString: str = entry['dt']
            dtObject: datetime = datetime.strptime(dtString, '%Y-%m-%d %H:%M:%S')
            entry['dt'] = dtObject.strftime('%Y-%m-%d %H:%M:%S')

            keyMapping: dict = {
                'dt': 'dateTime',
                'main': 'temperature',
                'weather': 'condition'
            }
        
        processedForecast: list = [
            {keyMapping.get(key, key): value for key, value in entry.items()}
            for entry in processedForecast
        ]

        return processedForecast

    def getForecastedData(self) -> list:
        forecastData: list = self.fiveDaysThreeHoursForcast()
        processedForecast: list = self.processForecastedData(forecastData)
        return processedForecast

forecast_instance: FiveDaysThreeHoursWeatherForecast = FiveDaysThreeHoursWeatherForecast(latitude, longitude)
five_days_three_hours_forecast_data: list = forecast_instance.getForecastedData()


# In[ ]:




