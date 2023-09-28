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

    @st.cache_data(hash_funcs={"__main__.CitySelector": lambda x: hash(x.ip_api_url)})
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
            st.sidebar.warning(f"Error fetching location: {e}")
            return "Tehran"
        
    # @st.cache_data(hash_funcs={"__main__.CitySelector": lambda x: hash(x.ip_api_url)}, experimental_allow_widgets=True)
    def getUserCity(self) -> str:
        city = st.sidebar.text_input("Search city (press enter for your CURRENT location):")
        return city if city else self.getDefaultCity()

# Preventing unintended execution of code when importing it
if __name__ == "__main__":
    st.sidebar.header("City Selector:")
    
    CitySelectorObj = CitySelector()
    city = CitySelectorObj.getUserCity()
    st.sidebar.write(f"Selected city : {city}")



apiKey: str = "Your Development Plan API key"
baseUrl: str = "http://api.openweathermap.org"

@st.cache_data
def constructUrl(endpoint: str, baseUrl: str = "http://api.openweathermap.org", extraParameters: dict = None) -> dict:
    parameters: dict = {"appId": apiKey, **(extraParameters or {})}
    url: str = f"{baseUrl}/{endpoint}"
    
    try:
        response: requests.Response = requests.get(url, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.sidebar.warning(f"Error making API request: {e}")
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
            st.sidebar.warning(f"Error getting geolocation data: {e}")
            return None

        geolocation = getGeolocationData(city)
    
    @st.cache_data(hash_funcs={"__main__.GeolocationDataFetcher": lambda x: hash(x.apiKey, x.baseUrl)})
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
        st.sidebar.warning(f"Unable to retrieve geolocation data for {city}")
        latitudeInput = st.sidebar.text_input(f"Enter latitude for {city}: ")
        longitudeInput = st.sidebar.text_input(f"Enter longitude for {city}: ")
    
        if not latitudeInput or not longitudeInput:
            st.sidebar.warning("Latitude and Longitude are required. Please try again.")
        else:
            try:
                latitude = float(latitudeInput)
                longitude = float(longitudeInput)
                st.sidebar.success("Latitude and Longitude received successfully.")
            except ValueError:
                st.sidebar.warning("Invalid latitude or longitude. Please enter valid numeric values.")


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
            st.sidebar.warning(f"Error getting current air pollution data: {e}")
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
        st.sidebar.warning("Unable to retrieve current air pollution data.")



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
            st.sidebar.warning(f"Error getting current air pollution data: {e}")
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
        st.sidebar.warning("Unable to retrieve forecasted air pollution data.")

startDate = datetime.now() - timedelta(days=6)
stopDate = datetime.now()
showData = st.sidebar.toggle("Historical Air Pollution Data")

if showData:
    startLabel = "Enter start date(press Enter for a week ago from today):"
    stopLabel = "Enter stop date ( press Enter for Today):"

    startDate = st.sidebar.date_input(startLabel, format="YYYY-MM-DD", value=startDate)
    stopDate = st.sidebar.date_input(stopLabel, format="YYYY-MM-DD", value=stopDate)

    
    try:
        startDate = datetime.strptime(str(startDate), '%Y-%m-%d')
    except ValueError:
        st.sidebar.warning("Invalid start date format. Using default start date.")
        startDate = datetime.now() - timedelta(days=6)

    try:
        stopDate = datetime.strptime(str(stopDate), '%Y-%m-%d')
    except ValueError:
        st.sidebar.warning("Invalid stop date format. Using default stop date.")
        stopDate = datetime.now()
    

    st.sidebar.write(f"Start Date: {startDate}")
    st.sidebar.write(f"Stop Date: {stopDate}")

# Time converting to Unix Zone
startTimestamp: int = int(startDate.timestamp())
stopTimestamp: int = int(stopDate.timestamp())

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
            st.sidebar.warning(f"Error getting historical air pollution data: {e}")
            return None

air_pollution_history_instance: AirPollutionHistory = AirPollutionHistory(latitude, longitude, startTimestamp, stopTimestamp)
air_pollution_historical_data: list = air_pollution_history_instance.airPollutionHistory(historical_interval="Daily") 

if showData:
    historical_interval = st.sidebar.selectbox("Select Historical Intervals", ["Daily", "12 Hours", "6 Hours", "Hourly"]) 
    air_pollution_historical_data: list = air_pollution_history_instance.airPollutionHistory(historical_interval) 

    if air_pollution_historical_data:
        df = pd.DataFrame(air_pollution_historical_data)
        df = pd.concat([df.drop(['components'], axis=1), df['components'].apply(pd.Series)], axis=1)
        st.subheader(f"The historical air pollution data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.warning("Unable to retrieve historical air pollution data.")

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

            currentKeys = ["name", "country", "condition", "mainFeatures", "visibility"]

            currentWeatherData = {
                "name": current["name"],
                "country": current["country"]["country"],
                "condition": f"{current['condition'][0]['main']} - {current['condition'][0]['description']}",
                **{key: current[key] for key in currentKeys if key not in ["name", "country", "condition"]}
            }
    
            main_features_mapping: dict = {
            'temp': 'Temperature (°C)',
            'feels_like': 'Feels Like (°C)',
            'temp_min': 'Min Temperature (°C)',
            'temp_max': 'Max Temperature (°C)',
            'pressure': 'Pressure (hPa)',
            'humidity': 'Humidity (%)'
            }

            for key in currentWeatherData.keys():
                mainFeatures = currentWeatherData.get('mainFeatures', {})
                renamed_features: dict = {main_features_mapping.get(key, key): value for key, value in mainFeatures.items()}
                currentWeatherData['mainFeatures'] = renamed_features

            
            return currentWeatherData
        except Exception as e:
            st.sidebar.warning(f"Error getting current weather condition: {e}")
            return None


current_weather_instance: CurrentWeather = CurrentWeather(latitude, longitude)
current_weather_data: dict = current_weather_instance.currentWeather()

showData = st.sidebar.toggle("Current Weather Condition")

if showData:
    if current_weather_data:
        df = pd.DataFrame([current_weather_data])
        df = pd.concat([df.drop(['mainFeatures'], axis=1), df['mainFeatures'].apply(pd.Series)], axis=1)
        st.subheader(f"The current weather condition for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.warning("Unable to retrieve the current weather condition data.")



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
            
            if hourlyForecastData is None:
                st.sidebar.warning("Failed to retrieve hourly weather forecast data.")
                return []

            hourlyForecastList: list = hourlyForecastData.get("list", [])
            hourlyForecastedWeatherData: list = []

            for forecastData in hourlyForecastList:
                weatherInfo: dict = {
                    "dateTime": forecastData.get("dt_txt", ""),
                    "Temperature": forecastData.get("main", {}).get("temp", ""),
                    "Weather Condition": (
                        forecastData.get("weather", [{}])[0].get("main", "") +
                        " - " +
                        forecastData.get("weather", [{}])[0].get("description", "")
                    )
                }
                hourlyForecastedWeatherData.append(weatherInfo)
                
            return hourlyForecastedWeatherData
        except Exception as e:
            st.sidebar.warning(f"Error getting hourly weather forecast: {e}")
            return None

hourly_forecast_instance: HourlyWeatherForecast = HourlyWeatherForecast(latitude, longitude)
hourly_forecast_data: list = hourly_forecast_instance.hourlyForecast()

showData = st.sidebar.toggle("Hourly Forcasted Data")

if showData:
    if hourly_forecast_data:
        df = pd.DataFrame(hourly_forecast_data)
        st.subheader(f"The Hourly Forcasted Data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.warning("Unable to retrieve the hourly forcasted data.")




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
                "units": "metric",
                "cnt": 16
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
                        "Day Temperature": forecast["temp"]["day"],
                        "Night Temperature": forecast["temp"]["night"],
                    },
                    "weatherCondition": {
                        "Main Condition": forecast["weather"][0]["main"],
                        "Description": forecast["weather"][0]["description"],
                    }
                }
                dailyForecastedWeather.append(weatherInfo)

            return dailyForecastedWeather

        except Exception as e:
            st.sidebar.warning(f"Error getting daily weather forecast: {e}")
            return None

daily_forecast_instance: DailyWeatherForecast = DailyWeatherForecast(latitude, longitude)
daily_forecast_data: list = daily_forecast_instance.dailyForecast()


showData = st.sidebar.toggle("Daily Forcasted Data")

if showData:
    if daily_forecast_data:
        df = pd.DataFrame(daily_forecast_data)
        df = pd.concat([df.drop(['temperature'], axis=1), df['temperature'].apply(pd.Series)], axis=1)
        df = pd.concat([df.drop(['weatherCondition'], axis=1), df['weatherCondition'].apply(pd.Series)], axis=1)
        st.subheader(f"The Daily Forcasted Data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.warning("Unable to retrieve the daily forcasted data.")




class FiveDaysThreeHoursWeatherForecast(Base):
    def __init__(self, latitude: float, longitude: float):
        super().__init__()
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

            return fiveDaysThreeHoursForcast.get("list", [])

        except Exception as e:
            st.sidebar.warning(f"Error retrieving 5-days 3-hours weather forecast data: {e}")
            return []
        
    def processForecastedData(self, forecastList: list) -> list:
        processedForecast: list = []

        for forecastData in forecastList:
            forecastData['dt'] = self.format_datetime(forecastData['dt'])

            weatherInfo: dict = {
                'Date Time': forecastData['dt'],
                'Temperature (°C)': forecastData['main']['temp'] if 'temp' in forecastData['main'] else None,
                'Condition': (
                    forecastData.get("weather", [{}])[0].get("main", "") +
                    " - " +
                    forecastData.get("weather", [{}])[0].get("description", "")
                ),
            }

            processedForecast.append(weatherInfo)


        return processedForecast

    def getForecastedData(self) -> list:
        forecastData: list = self.fiveDaysThreeHoursForcast()
        processedForecast: list = self.processForecastedData(forecastData)
        return processedForecast

forecast_instance: FiveDaysThreeHoursWeatherForecast = FiveDaysThreeHoursWeatherForecast(latitude, longitude)
five_days_three_hours_forecast_data: list = forecast_instance.getForecastedData()

showData = st.sidebar.toggle("5-Day-3-Hour Forcasted Data")

if showData:
    if five_days_three_hours_forecast_data:
        df = pd.DataFrame(five_days_three_hours_forecast_data)
        st.subheader(f"The 5-Day-3-Hour Forcasted Data for {city}")
        st.dataframe(df , hide_index=True )
    else:
        st.sidebar.warning("Unable to retrieve the 5-Day-3-hour forcasted data.")



connection= sqlite3.connect('cities.db')
cursor = connection.cursor()

cursor.execute("SELECT cityName FROM asianCities")
cityNames = cursor.fetchall()

connection.close()


def get_selected_cities(selected_region):
    connection = sqlite3.connect('cities.db')
    cursor = connection.cursor()

    if selected_region == "All":
        city_names = []
        continents = ["Asian Cities", "African Cities", "European Cities", "North American Cities", "South American Cities"]
        for continent in continents:
            table_name = continent.replace(" ", "")
            cursor.execute(f"SELECT cityName FROM {table_name}")
            city_names += cursor.fetchall()

    elif selected_region == "US States":
        table_name = selected_region.replace(" ", "")
        cursor.execute(f"SELECT stateName FROM {table_name}")
        city_names = cursor.fetchall()

    else:
        table_name = selected_region.replace(" ", "")
        cursor.execute(f"SELECT cityName FROM {table_name}")
        city_names = cursor.fetchall()

    connection.close()


    city_names = [city[0] for city in city_names]
    selected_cities = st.sidebar.multiselect("Select cities:", city_names)

    if selected_cities:
        return selected_cities
    else:
        st.sidebar.warning("No cities selected")
        return selected_cities


showData = st.sidebar.toggle("Capitals Database Collector")


selected_cities = []
if showData:
    selected_region = st.sidebar.selectbox("Select a continent or region:",
                                            ["All", "Asian Cities", "African Cities", "European Cities", "North American Cities", 
                                                "South American Cities", "US States"])
        
    selected_cities = get_selected_cities(selected_region)


fetcher = GeolocationDataFetcher()
allGeolocationData = []

for cityTuple in selected_cities:
    cityName = cityTuple
    cityParts = cityName.split('-')
    cityName = cityParts[0]
    
    while True:
        geolocationData = fetcher.getGeolocationData(cityName)

        if geolocationData:
            allGeolocationData.append(geolocationData)
            break 
        else:
            st.sidebar.warning(f"Unable to retrieve geolocation data for {cityName}")
            user_input = st.sidebar.selectbox(
                f"What would you like to do for {cityName}?",
                ["Skip", "Enter manually"]
            )

            if user_input == "Skip":
                st.sidebar.write("Skipping this city.")
                break

            elif user_input == "Enter manually":
                latitudeInput = st.sidebar.text_input(f"Enter latitude for {cityName}: ")
                longitudeInput = st.sidebar.text_input(f"Enter longitude for {cityName}: ")

            if latitudeInput and longitudeInput:
                try:
                    latitude = float(latitudeInput)
                    longitude = float(longitudeInput)
                    st.sidebar.success("Latitude and Longitude received successfully.")
                    break 
                except ValueError:
                    st.sidebar.warning("Invalid latitude or longitude. Please enter valid numeric values.")
            else:
                st.sidebar.warning("Latitude and Longitude are required. Please try again.")

if showData:
    if allGeolocationData:
        resultDf = pd.DataFrame(allGeolocationData)
        st.subheader("Selected Cities:")
        st.dataframe(resultDf, hide_index=True)
    else:
        st.sidebar.warning("No geolocation data available.")


resultDf = pd.DataFrame(allGeolocationData)
list_ = []

if showData:

    def fetch_data_from_class(selected_class):
            
            for index, row in resultDf.iterrows():
                cityName = row['name']
                latitude = row['lat']
                longitude = row['lon']

                if selected_class == "Current Air Pollution":
                    air_pollution_instance = AirPollutionData(latitude, longitude)
                    air_pollution_data = air_pollution_instance.currentAirPollution()

                    if air_pollution_data:
                        air_pollution_data_with_index = [{'City': cityName, **entry} for entry in air_pollution_data]
                        list_.extend(air_pollution_data_with_index)

                    else:
                        st.sidebar.warning(f"Unable to retrieve air pollution data for {cityName}")

                elif selected_class == "Air Pollution Forecast":
                    air_pollution_forecast_instance = AirPollutionForecast(latitude, longitude)
                    air_pollution_forecast_data = air_pollution_forecast_instance.airPollutionForecast(forecast_interval=25)

                    if air_pollution_forecast_data:
                        air_pollution_forecast_data_with_index = [{'City': cityName, **entry} for entry in air_pollution_forecast_data]
                        list_.extend(air_pollution_forecast_data_with_index)
                
                    else:
                        st.sidebar.warning(f"Unable to retrieve forcasted air pollution data for {cityName}")
                
                elif selected_class == "Air Pollution History":
                    air_pollution_historical_instance = AirPollutionHistory(latitude, longitude, startTimestamp, stopTimestamp)
                    air_pollution_historical_data = air_pollution_historical_instance.airPollutionHistory(historical_interval="Daily")

                    if air_pollution_historical_data:
                        air_pollution_historical_data_with_index = [{'City': cityName, **entry} for entry in air_pollution_historical_data]
                        list_.extend(air_pollution_historical_data_with_index)
                
                    else:
                        st.sidebar.warning(f"Unable to retrieve historical air pollution data for {cityName}")

                elif selected_class == "Current Weather Condition":
                    current_weather_condition_instance = CurrentWeather(latitude, longitude)
                    current_weather_condition_data = current_weather_condition_instance.currentWeather()

                    if current_weather_condition_data:
                        current_weather_condition_data_with_index = [{'City': cityName, **current_weather_condition_data}]
                        list_.extend(current_weather_condition_data_with_index)
                    else:
                        st.sidebar.warning(f"Unable to retrieve current weather condition data for {cityName}")

                elif selected_class == "Hourly Weather Forecast":
                    hourly_weather_forecast_instance = HourlyWeatherForecast(latitude, longitude)
                    hourly_weather_forecast_data = hourly_weather_forecast_instance.hourlyForecast()

                    if hourly_weather_forecast_data:
                        hourly_weather_forecast_data_with_index = [{'City': cityName, **entry} for entry in hourly_weather_forecast_data]
                        list_.extend(hourly_weather_forecast_data_with_index)
                    else:
                        st.sidebar.warning(f"Unable to retrieve hourly weather forecast data for {cityName}")

                elif selected_class == "Daily Weather Forecast":
                    daily_weather_forecast_instance = DailyWeatherForecast(latitude, longitude)
                    daily_weather_forecast_data = daily_weather_forecast_instance.dailyForecast()

                    if daily_weather_forecast_data:
                        daily_weather_forecast_data_with_index = [{'City': cityName, **entry} for entry in daily_weather_forecast_data]
                        list_.extend(daily_weather_forecast_data_with_index)
                    else:
                        st.sidebar.warning(f"Unable to retrieve daily weather forecast data for {cityName}")

                elif selected_class == "FiveDays-ThreeHours Weather Forecast":
                    weather_forecast_instance = FiveDaysThreeHoursWeatherForecast(latitude, longitude)
                    weather_forecast_data = weather_forecast_instance.getForecastedData()

                    if weather_forecast_data:
                        weather_forecast_data_with_index = [{'City': cityName, **entry} for entry in weather_forecast_data]
                        list_.extend(weather_forecast_data_with_index)
                    else:
                        st.sidebar.warning(f"Unable to retrieve weather forecast data for {cityName}")

                


    selected_class = st.sidebar.selectbox("Select a collector class:", ["Current Air Pollution", "Air Pollution Forecast", "Air Pollution History",
                                                                        "Current Weather Condition", "Hourly Weather Forecast", "Daily Weather Forecast","FiveDays-ThreeHours Weather Forecast"])

    if selected_class:
        data = fetch_data_from_class(selected_class)

        if list_:
            df = pd.DataFrame(list_)
            if 'components' in df.columns:
                df = pd.concat([df.drop(['components'], axis=1), df['components'].apply(pd.Series)], axis=1)

            elif 'mainFeatures' in df.columns:
                df = pd.concat([df.drop(['mainFeatures'], axis=1), df['mainFeatures'].apply(pd.Series)], axis=1)
                columns_to_drop = ['name', 'country']
                df = df.drop(columns=columns_to_drop)

            elif 'temperature' and 'weatherCondition' in df.columns:
                df = pd.concat([df.drop(['temperature'], axis=1), df['temperature'].apply(pd.Series)], axis=1)
                df = pd.concat([df.drop(['weatherCondition'], axis=1), df['weatherCondition'].apply(pd.Series)], axis=1)
 
            st.subheader("Data Preview:")
            st.dataframe(df, hide_index=True)

            if st.button("Export as CSV"):
                st.write("Exporting data to CSV...")
                df.to_csv(f"{selected_class}_data.csv", index=False)
                st.success(f"{selected_class}_data.csv file created successfully!")

        else:
            st.sidebar.warning("No data available for the selected class.")
