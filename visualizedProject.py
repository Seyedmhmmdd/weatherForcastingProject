import json
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

st.title("Welcome to WeatherWise")
st.subheader("Some Description")
st.write("""
         Please feel free to select your desired city, and within our weather service, 
         you have the flexibility to access a wide range of valuable information. 
         You can check the current weather conditions, get detailed daily and hourly forecasts,
         or even obtain comprehensive air pollution data.
          Whether you're planning your day or need in-depth environmental insights, we've got you covered.
         """)


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
            st.sidebar.write(f"Error fetching location: {e}")
            return "Tehran"
    
    def getUserCity(self) -> str:
        city = st.sidebar.text_input("Search city (press enter for your CURRENT location):")
        return city if city else self.getDefaultCity()

# Preventing unintended execution of code when importing it
if __name__ == "__main__":
    st.sidebar.header("City Selector:")
    
    CitySelectorObj = CitySelector()
    city = CitySelectorObj.getUserCity()
    st.sidebar.write(f"Selected city: {city}")



apiKey: str = "6e7ce66ebb56a74749c7b9938c18bed2"
baseUrl: str = "http://api.openweathermap.org"

def constructUrl(endpoint: str, baseUrl: str = "http://api.openweathermap.org", extraParameters: dict = None) -> dict:
    parameters: dict = {"appId": apiKey, **(extraParameters or {})}
    url: str = f"{baseUrl}/{endpoint}"
    
    try:
        response: requests.Response = requests.get(url, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.sidebar.write(f"Error making API request: {e}")
        return None
    



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
            st.sidebar.write(f"Error getting geolocation data: {e}")
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
        st.sidebar.write(f"Latitude: {latitude}, Longitude: {longitude}")
    else:
        st.sidebar.write(f"Unable to retrieve geolocation data for {city}")
        latitudeInput = st.sidebar.text_input(f"Enter latitude for {city}: ")
        longitudeInput = st.sidebar.text_input(f"Enter longitude for {city}: ")
    
        if not latitudeInput or not longitudeInput:
            st.sidebar.write("Latitude and Longitude are required. Please try again.")
        else:
            try:
                latitude = float(latitudeInput)
                longitude = float(longitudeInput)
                st.sidebar.write("Latitude and Longitude received successfully.")
            except ValueError:
                st.sidebar.write("Invalid latitude or longitude. Please enter valid numeric values.")


class Base:
    def __init__(self):
        pass

    @staticmethod
    def format_datetime(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
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
            st.sidebar.write(f"Error getting current air pollution data: {e}")
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

showData = st.sidebar.toggle("Current Air Pollution Data")
if showData:
    if current_air_pollution:
        df = pd.DataFrame(current_air_pollution)
        df = pd.concat([df.drop(['components'], axis=1), df['components'].apply(pd.Series)], axis=1)
        st.subheader(f"The current air pollution data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.write("Unable to retrieve current air pollution data.")



class AirPollutionForecast(Base):
    
    def __init__(self, latitude: float, longitude: float):
        super().__init__()         
        self.latitude: float = latitude
        self.longitude: float = longitude

    def airPollutionForecast(self, forecast_interval: str) -> list:
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
            
            if forecast_interval == "Hourly":
                airPollutionForcastList: list = airPollutionForecastData["list"]
            elif forecast_interval == "6 Hours":
                airPollutionForcastList: list = airPollutionForecastData["list"][::4]
            elif forecast_interval == "12 Hours":
                airPollutionForcastList: list = airPollutionForecastData["list"][::12]
            else:  # Default to Daily
                airPollutionForcastList: list = airPollutionForecastData["list"][::24]
            
            airPollutionForecastProcessed: list = AirPollutionData.processAirPollution(self, airPollutionForcastList)

            return airPollutionForecastProcessed
        except Exception as e:
            st.sidebar.write(f"Error getting current air pollution data: {e}")
            return None
        

air_pollution_forecast_instance: AirPollutionForecast = AirPollutionForecast(latitude, longitude)
air_pollution_forecasted_data: list = air_pollution_forecast_instance.airPollutionForecast(forecast_interval="Daily")

showData = st.sidebar.toggle("Forecasted Air Pollution Data")

if showData:
    forecast_interval = st.sidebar.selectbox("Select Forecast Interval", ["Daily", "12 Hours", "6 Hours", "Hourly"])
    air_pollution_forecasted_data = air_pollution_forecast_instance.airPollutionForecast(forecast_interval)
    if air_pollution_forecasted_data:
        df = pd.DataFrame(air_pollution_forecasted_data)
        df = pd.concat([df.drop(['components'], axis=1), df['components'].apply(pd.Series)], axis=1)
        st.subheader(f"The forecasted air pollution data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.write("Unable to retrieve forecasted air pollution data.")


startDate = datetime.now() - timedelta(days=7)
stopDate = datetime.now()
showData = st.sidebar.toggle("Historical Air Pollution Data")

if showData:
    startLabel = "Enter start date(press Enter for a week ago from today):"
    stopLabel = "Enter stop date ( press Enter for Today):"

    startDate = st.sidebar.date_input(startLabel, format="YYYY-MM-DD", value=startDate)
    stopDate = st.sidebar.date_input(stopLabel, format="YYYY-MM-DD", value=stopDate)

    
    try:
        startDt = datetime.strptime(str(startDate), '%Y-%m-%d')
    except ValueError:
        st.sidebar.write("Invalid start date format. Using default start date.")
        startDt = startDate

    try:
        stopDt = datetime.strptime(str(stopDate), '%Y-%m-%d')
    except ValueError:
        st.sidebar.write("Invalid stop date format. Using default stop date.")
        stopDt = stopDate
    

    st.sidebar.write(f"Start Date: {startDt}")
    st.sidebar.write(f"Stop Date: {stopDt}")

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
            
        def airPollutionHistory(self , historical_interval: str) -> list:
            
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

                if historical_interval == "Hourly":
                    airPollutionHistoryList: list = airPollutionHistoryData["list"]
                elif historical_interval == "6 Hours":
                    airPollutionHistoryList: list = airPollutionHistoryData["list"][::4]
                elif historical_interval == "12 Hours":
                    airPollutionHistoryList: list = airPollutionHistoryData["list"][::12]
                else:  # Default to Daily
                    airPollutionHistoryList: list = airPollutionHistoryData["list"][::24]

                airPollutionHistoryProcessed: list = self.airPollutionData.processAirPollution(airPollutionHistoryList)

                return airPollutionHistoryProcessed

            except Exception as e:
                st.sidebar.write(f"Error getting historical air pollution data: {e}")
                return None

    air_pollution_history_instance: AirPollutionHistory = AirPollutionHistory(latitude, longitude, startTimestamp, stopTimestamp)
    historical_interval = st.sidebar.selectbox("Select Historical Intervals", ["Daily", "12 Hours", "6 Hours", "Hourly"]) 
    air_pollution_historical_data: list = air_pollution_history_instance.airPollutionHistory(historical_interval) 


    if air_pollution_historical_data:
        df = pd.DataFrame(air_pollution_historical_data)
        df = pd.concat([df.drop(['components'], axis=1), df['components'].apply(pd.Series)], axis=1)
        st.subheader(f"The historical air pollution data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.write("Unable to retrieve historical air pollution data.")