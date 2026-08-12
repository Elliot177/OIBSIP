# Weather App 
An asynchronous desktop GUI weather dashboard built with Python and Tkinter. The application provides real-time atmospheric conditions, short-term 6-hour forecasts, and 5-day daily weather projections with automatic zero-key API failover and IP-based auto-geolocation.

-----


 # Key Features

|Real-Time Conditions & Multi-Day Forecasts: Displays current weather metrics along with 6-hour detailed forecasts and 5-day daily projections|

|Dual-API Resiliency & Failover: Automatically fails over to the zero-key Open-Meteo service if an OpenWeatherMap API key is missing or invalid|






+--------------------------------+
| User Enters City / Clicks Auto |[cite: 1]
+---------------+----------------+
                |           
Does OPENWEATHER_API_KEY Exist?[cite: 1]
              /   \
      YES    /     \    NO / FAILED[cite: 1]
            v       v
+------------------+   +-------------------+
| OpenWeatherMap   |   | Open-Meteo REST   |[cite: 1]
| Geocoding & API  |   | & OSM Nominatim   |[cite: 1]
+--------+---------+   +---------+---------+
       |                       |
        +-----------+-----------+
                    |
                    v
Render GUI Dashboard & Icons[cite: 1]