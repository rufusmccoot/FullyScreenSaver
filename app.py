from flask import Flask, render_template, jsonify
from datetime import datetime
import os
import requests

# Read secrets.txt
SECRETS = {}
with open(os.path.join(os.path.dirname(__file__), 'secrets.txt')) as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            SECRETS[k.strip()] = v.strip()

HA_URL = SECRETS['HA_URL']
WEATHER_ENTITY = SECRETS['WEATHER_ENTITY']
HA_TOKEN = SECRETS['HA_TOKEN']

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('clock.html')

import threading
import time
from datetime import datetime

weather_cache = None
weather_cache_lock = threading.Lock()

# The function that fetches and builds the weather JSON (reuse your weather logic here)
def fetch_weather_data():
    url = f"{HA_URL}/api/states/{WEATHER_ENTITY}"
    headers = {
        'Authorization': f'Bearer {HA_TOKEN}',
        'Content-Type': 'application/json',
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    # Get current temperature from sensor.pirateweather_temperature
    sensor_temp_url = f"{HA_URL}/api/states/sensor.pirateweather_temperature"
    resp_temp = requests.get(sensor_temp_url, headers=headers)
    if resp_temp.status_code == 200:
        sensor_temp_data = resp_temp.json()
        try:
            temp = float(sensor_temp_data.get('state'))
        except (TypeError, ValueError):
            temp = None
    else:
        temp = None
    condition = data.get('state')

    # Grab next 5 hours of forecasted temperature from sensors
    temp_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_temperature_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        temp_hourly.append(value)

    # Grab next 5 days of forecasted high and low temperatures
    daily_highs = []
    daily_lows = []
    for i in range(5):
        # Highs
        sensor_high = f'sensor.pirateweather_daytime_high_temperature_{i}d'
        sensor_high_url = f"{HA_URL}/api/states/{sensor_high}"
        resp_high = requests.get(sensor_high_url, headers=headers)
        if resp_high.status_code == 200:
            sensor_data_high = resp_high.json()
            value_high = sensor_data_high.get('state')
            try:
                value_high = float(value_high)
            except (TypeError, ValueError):
                value_high = None
        else:
            value_high = None
        daily_highs.append(value_high)
        # Lows
        sensor_low = f'sensor.pirateweather_overnight_low_temperature_{i}d'
        sensor_low_url = f"{HA_URL}/api/states/{sensor_low}"
        resp_low = requests.get(sensor_low_url, headers=headers)
        if resp_low.status_code == 200:
            sensor_data_low = resp_low.json()
            value_low = sensor_data_low.get('state')
            try:
                value_low = float(value_low)
            except (TypeError, ValueError):
                value_low = None
        else:
            value_low = None
        daily_lows.append(value_low)

    # Fetch daily summary and convert C to F if present
    daily_summary = None
    sensor_summary_url = f"{HA_URL}/api/states/sensor.pirateweather_daily_summary"
    resp_summary = requests.get(sensor_summary_url, headers=headers)
    if resp_summary.status_code == 200:
        sensor_summary_data = resp_summary.json()
        summary = sensor_summary_data.get('state')
        import re
        def c_to_f(match):
            c = float(match.group(1))
            f = round(c * 9 / 5 + 32)
            return f"{f}°F"
        # Replace all XXC or XX°C with XXF
        summary = re.sub(r"(\-?\d+(?:\.\d+)?)[°]?C", c_to_f, summary)
        daily_summary = summary

    # Grab next 5 hours of precip intensity from sensors
    precip_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_intensity_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_hourly.append({'hour': i, 'precip': value})

    # Grab next 5 days of precip intensity from sensors
    precip_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_intensity_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_daily.append({'day': i, 'precip': value})

    # Grab next 5 hours of precip probability from sensors
    precip_prob_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_probability_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_prob_hourly.append({'hour': i, 'prob': value})

    # Grab next 5 days of precip probability from sensors
    precip_prob_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_probability_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_prob_daily.append({'day': i, 'prob': value})

    # Fetch current icon
    icon = None
    sensor_icon_url = f"{HA_URL}/api/states/sensor.pirateweather_icon"
    resp_icon = requests.get(sensor_icon_url, headers=headers)
    if resp_icon.status_code == 200:
        sensor_icon_data = resp_icon.json()
        icon = sensor_icon_data.get('state')

    # Fetch next 5 hours of icon
    icon_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_icon_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
        else:
            value = None
        icon_hourly.append({'hour': i, 'icon': value})

    # Fetch next 5 days of icon
    icon_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_icon_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
        else:
            value = None
        icon_daily.append({'day': i, 'icon': value})

    # Fetch moon phase for today
    moon_phase = None
    moon_phase_url = f"{HA_URL}/api/states/sensor.pirateweather_moon_phase_0d"
    resp_moon = requests.get(moon_phase_url, headers=headers)
    if resp_moon.status_code == 200:
        moon_phase_data = resp_moon.json()
        moon_phase = moon_phase_data.get('state')

    # Build new structured output
    current = {
        'condition': condition,
        'daily_summary': daily_summary,
        'icon': icon,
        'moon_phase': moon_phase,
        'temp': temp
    }
    hourly = {}
    for i in range(5):
        hourly[f'hour{i}'] = {
            'icon': icon_hourly[i]['icon'] if i < len(icon_hourly) else None,
            'precip': precip_hourly[i]['precip'] if i < len(precip_hourly) else None,
            'precip_prob': precip_prob_hourly[i]['prob'] if i < len(precip_prob_hourly) else None,
            'temp': temp_hourly[i] if i < len(temp_hourly) else None
        }
    daily = {}
    for i in range(5):
        daily[f'day{i}'] = {
            'icon': icon_daily[i]['icon'] if i < len(icon_daily) else None,
            'precip': precip_daily[i]['precip'] if i < len(precip_daily) else None,
            'precip_prob': precip_prob_daily[i]['prob'] if i < len(precip_prob_daily) else None,
            'temp_high': daily_highs[i] if i < len(daily_highs) else None,
            'temp_low': daily_lows[i] if i < len(daily_lows) else None
        }
    return {
        'current': current,
        'hourly': hourly,
        'daily': daily
    }

def refresh_weather_cache():
    global weather_cache
    try:
        data = fetch_weather_data()

        with weather_cache_lock:
            weather_cache = data

        print("Weather cache refreshed.")

    except Exception as e:
        print(f"Weather refresh failed: {e}")

def weather_cache_updater():
    while True:
        now = datetime.now()
        if 6 <= now.hour < 21:  # 6am to 9pm
            refresh_weather_cache()
        time.sleep(20 * 60)  # 20 minutes

# On Flask launch, refresh weather cache
# Try every N seconds in case hass or adguard dns isn't up yet after reboot
# refresh_weather_cache() defines its own update time, 20 min probably
while weather_cache is None:
    refresh_weather_cache()

    if weather_cache is None:
        print("Waiting 60 seconds before retry...")
        time.sleep(60)

threading.Thread(target=weather_cache_updater, daemon=True).start()

@app.route('/weather_ui')
def weather_ui():
    return render_template('weather_ui.html', ha_url=HA_URL)

@app.route('/weather')
def weather():
    with weather_cache_lock:
        return jsonify(weather_cache)
    url = f"{HA_URL}/api/states/{WEATHER_ENTITY}"
    headers = {
        'Authorization': f'Bearer {HA_TOKEN}',
        'Content-Type': 'application/json',
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    # Get current temperature from sensor.pirateweather_temperature
    sensor_temp_url = f"{HA_URL}/api/states/sensor.pirateweather_temperature"
    resp_temp = requests.get(sensor_temp_url, headers=headers)
    if resp_temp.status_code == 200:
        sensor_temp_data = resp_temp.json()
        try:
            temp = float(sensor_temp_data.get('state'))
        except (TypeError, ValueError):
            temp = None
    else:
        temp = None
    condition = data['state']
    forecast = data['attributes'].get('forecast', [])
    hourly = []
    daily = []
    # Split forecast entries into hourly and daily based on datetime granularity
    for entry in forecast:
        dt = entry.get('datetime')
        if dt:
            # Heuristic: if time is 00:00, treat as daily; else hourly
            if 'T00:00' in dt or 'T00:00:00' in dt:
                daily.append(entry)
            else:
                hourly.append(entry)
    # Only take next 6 hours and next 3 days
    hourly_out = hourly[:6]
    daily_out = daily[:3]

    # Grab next 5 hours of forecasted temperature from sensors
    temp_hourly = []

    for i in range(5):
        sensor_name = f'sensor.pirateweather_temperature_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        temp_hourly.append({'hour': i, 'temperature': value})

    # Grab next 6 days of high and low temperatures from sensors
    daily_highs = []
    daily_lows = []
    for i in range(6):
        # Highs
        sensor_high = f'sensor.pirateweather_daytime_high_temperature_{i}d'
        sensor_high_url = f"{HA_URL}/api/states/{sensor_high}"
        resp_high = requests.get(sensor_high_url, headers=headers)
        if resp_high.status_code == 200:
            sensor_data_high = resp_high.json()
            value_high = sensor_data_high.get('state')
            try:
                value_high = float(value_high)
            except (TypeError, ValueError):
                value_high = None
        else:
            value_high = None
        daily_highs.append({'day': i, 'high': value_high})
        # Lows
        sensor_low = f'sensor.pirateweather_daytime_low_temperature_{i}d'
        sensor_low_url = f"{HA_URL}/api/states/{sensor_low}"
        resp_low = requests.get(sensor_low_url, headers=headers)
        if resp_low.status_code == 200:
            sensor_data_low = resp_low.json()
            value_low = sensor_data_low.get('state')
            try:
                value_low = float(value_low)
            except (TypeError, ValueError):
                value_low = None
        else:
            value_low = None
        daily_lows.append({'day': i, 'low': value_low})

    # Fetch daily summary and convert C to F if present
    daily_summary = None
    sensor_summary_url = f"{HA_URL}/api/states/sensor.pirateweather_daily_summary"
    resp_summary = requests.get(sensor_summary_url, headers=headers)
    if resp_summary.status_code == 200:
        sensor_summary_data = resp_summary.json()
        summary = sensor_summary_data.get('state')
        import re
        def c_to_f(match):
            c = float(match.group(1))
            f = round(c * 9/5 + 32)
            return f"{f}°F"
        if summary:
            # Replace all XXC with XXF
            summary = re.sub(r"(\-?\d+(?:\.\d+)?)C", c_to_f, summary)
        daily_summary = summary
    # Grab next 5 hours of precip intensity from sensors
    precip_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_intensity_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_hourly.append({'hour': i, 'precip': value})

    # Grab next 5 days of precip intensity from sensors
    precip_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_intensity_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_daily.append({'day': i, 'precip': value})

    # Grab next 5 hours of precip probability from sensors
    precip_prob_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_probability_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_prob_hourly.append({'hour': i, 'prob': value})

    # Grab next 5 days of precip probability from sensors
    precip_prob_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_precip_probability_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        else:
            value = None
        precip_prob_daily.append({'day': i, 'prob': value})

    # Fetch current icon
    icon = None
    sensor_icon_url = f"{HA_URL}/api/states/sensor.pirateweather_icon"
    resp_icon = requests.get(sensor_icon_url, headers=headers)
    if resp_icon.status_code == 200:
        sensor_icon_data = resp_icon.json()
        icon = sensor_icon_data.get('state')

    # Fetch next 5 hours of icon
    icon_hourly = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_icon_{i}h'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
        else:
            value = None
        icon_hourly.append({'hour': i, 'icon': value})

    # Fetch next 5 days of icon
    icon_daily = []
    for i in range(5):
        sensor_name = f'sensor.pirateweather_icon_{i}d'
        sensor_url = f"{HA_URL}/api/states/{sensor_name}"
        resp = requests.get(sensor_url, headers=headers)
        if resp.status_code == 200:
            sensor_data = resp.json()
            value = sensor_data.get('state')
        else:
            value = None
        icon_daily.append({'day': i, 'icon': value})

    # Fetch moon phase for today
    moon_phase = None
    moon_phase_url = f"{HA_URL}/api/states/sensor.pirateweather_moon_phase_0d"
    resp_moon = requests.get(moon_phase_url, headers=headers)
    if resp_moon.status_code == 200:
        moon_phase_data = resp_moon.json()
        moon_phase = moon_phase_data.get('state')

    return jsonify({'temp': temp, 'condition': condition, 'hourly': hourly_out, 'daily': daily_out, 'temp_hourly': temp_hourly, 'daily_highs': daily_highs, 'daily_lows': daily_lows, 'daily_summary': daily_summary, 'precip_hourly': precip_hourly, 'precip_daily': precip_daily, 'precip_prob_hourly': precip_prob_hourly, 'precip_prob_daily': precip_prob_daily, 'icon': icon, 'icon_hourly': icon_hourly, 'icon_daily': icon_daily, 'moon_phase': moon_phase})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8282, debug=True)
