from flask import Flask, render_template_string, jsonify
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

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Current Time</title>
    <style>
        @font-face {
            font-family: 'segment7';
            src: url("/static/7segment.woff") format("woff");
        }
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            background: #222;
            color: #fff;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }
        .time {
            position: absolute;
            font-size: 15em;
            user-select: none;
            white-space: nowrap;
            font-family: 'segment7', monospace;
            letter-spacing: 0.04em;
            width: 6ch;
            text-align: center;
        }
    </style>
    <script>
        function updateTime() {
            const now = new Date();
            let hours = now.getHours();
            let minutes = now.getMinutes().toString().padStart(2, '0');
            hours = hours % 12;
            hours = hours ? hours : 12; // the hour '0' should be '12'
            let display = `${hours.toString().padStart(2, '0')}:${minutes}`;
            document.getElementById('time').textContent = display;
        }
        // Floating logic for the clock only
        function startRandomFloat() {
            const clock = document.getElementById('time');
            clock.style.position = 'absolute';
            function nextMove() {
                const vw = window.innerWidth;
                const vh = window.innerHeight;
                const rect = clock.getBoundingClientRect();
                const pad = 20;
                const maxLeft = vw - rect.width - pad;
                const maxTop = vh - rect.height - pad;
                const minLeft = pad;
                const minTop = pad;
                // Clamp to valid range (in case window is smaller than clock)
                const safeMaxLeft = Math.max(minLeft, maxLeft);
                const safeMaxTop = Math.max(minTop, maxTop);
                let newLeft, newTop, prevLeft, prevTop, dx, dy, distance, duration;
                do {
                    newLeft = Math.random() * (safeMaxLeft - minLeft) + minLeft;
                    newTop = Math.random() * (safeMaxTop - minTop) + minTop;
                    prevLeft = parseFloat(clock.style.left) || 0;
                    prevTop = parseFloat(clock.style.top) || 0;
                    dx = newLeft - prevLeft;
                    dy = newTop - prevTop;
                    distance = Math.sqrt(dx * dx + dy * dy);
                } while (distance < 10); // avoid picking the same spot
                const speed = 10; // px per second
                duration = distance / speed;
                clock.style.transition = `left ${duration}s cubic-bezier(0.4,0,0.2,1), top ${duration}s cubic-bezier(0.4,0,0.2,1)`;
                clock.style.left = `${newLeft}px`;
                clock.style.top = `${newTop}px`;
                // Always schedule next move after duration (minimum 1s)
                setTimeout(nextMove, Math.max(duration * 1000, 1000));
            }
            setTimeout(nextMove, 500);
        }

        // Weather fetch and update
        function updateWeather() {
            fetch('/weather').then(r => r.json()).then(data => {
                const weatherDiv = document.getElementById('weather');
                weatherDiv.textContent = `${data.temp}°  ${data.condition}`;
            }).catch(() => {
                document.getElementById('weather').textContent = '--';
            });
        }
        setInterval(updateWeather, 600000); // every 10 minutes

        // On load, update weather and time
        window.onload = function() {
            updateTime();
            const clock = document.getElementById('time');
            clock.style.position = 'absolute';
            setTimeout(() => {
                const vw = window.innerWidth;
                const vh = window.innerHeight;
                const rect = clock.getBoundingClientRect();
                clock.style.left = `${(vw - rect.width) / 2}px`;
                clock.style.top = `${(vh - rect.height) / 2}px`;
                startRandomFloat();
                startColorTransition();
            }, 50);
        };


        setInterval(updateTime, 1000);
        setInterval(updateWeather, 600000);
        // Color transition
        function randomColor() {
            // HSL: h=0-360, s=90-100, l=23-60
            const h = Math.floor(Math.random() * 361); // 0-360
            const s = 90 + Math.random() * 10;         // 90-100
            const l = 23 + Math.random() * 37;         // 23-60
            return `hsl(${h}, ${s}%, ${l}%)`;
        }
        function startColorTransition() {
            const clock = document.getElementById('time');
            let currentColor = window.getComputedStyle(clock).color;
            function nextColor() {
                const newColor = randomColor();
                clock.style.transition = (clock.style.transition ? clock.style.transition + ', ' : '') + 'color 60s linear';
                clock.style.color = newColor;
                setTimeout(() => {
                    // After transition, set up for next
                    currentColor = newColor;
                    nextColor();
                }, 60000);
            }
            nextColor();
        }






    </script>
</head>
<body>

    <div class="time" id="time">--:--</div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

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
    with weather_cache_lock:
        weather_cache = fetch_weather_data()

def weather_cache_updater():
    while True:
        now = datetime.now()
        if 6 <= now.hour < 21:  # 6am to 9pm
            refresh_weather_cache()
        time.sleep(20 * 60)  # 20 minutes

# On Flask launch, refresh cache and start background updater
refresh_weather_cache()
threading.Thread(target=weather_cache_updater, daemon=True).start()

@app.route('/weather_ui')
def weather_ui():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #181c23; color: #fff; margin: 0; padding: 0; }
        .container { max-width: 900px; margin: 30px auto; background: #232733; border-radius: 12px; box-shadow: 0 2px 16px #000a; padding: 32px; }
        h1 { margin-top: 0; font-size: 2.3em; letter-spacing: 0.04em; }
        .current { display: flex; align-items: center; gap: 32px; margin-bottom: 32px; }
        .current-icon { font-size: 4em; }
        .current-details { font-size: 1.3em; }
        .section-title { margin: 20px 0 8px 0; font-size: 1.2em; color: #aee; letter-spacing: 0.04em; }
        .hourly, .daily { display: flex; gap: 18px; }
        .hour, .day { background: #23293a; border-radius: 8px; padding: 12px 10px; min-width: 90px; text-align: center; box-shadow: 0 1px 4px #0005; }
        .hour .icon, .day .icon { font-size: 2em; }
        .label { font-size: 0.9em; color: #a9b; margin-top: 2px; }
        .value { font-size: 1.1em; margin: 2px 0; }
        .moon { font-size: 1.6em; margin-left: 10px; }
        .summary { margin-top: 10px; color: #eee; font-size: 1.1em; }
        @media (max-width: 900px) { .container { padding: 10px; } .hourly, .daily { flex-wrap: wrap; } }
    </style>
    <script>
        const ha_url = "{{ ha_url }}";
        function iconUrl(icon) {
            if (!icon) return '';
            return `${ha_url}/hacsfiles/weather-chart-card/icons2/${icon}.svg`;
        }
        function moonToEmoji(phase) {
            if (!phase) return '';
            const map = {
                'New Moon': '🌑', 'Waxing Crescent': '🌒', 'First Quarter': '🌓', 'Waxing Gibbous': '🌔',
                'Full Moon': '🌕', 'Waning Gibbous': '🌖', 'Last Quarter': '🌗', 'Waning Crescent': '🌘'
            };
            return map[phase] || '🌙';
        }
        function updateWeatherUI() {
            fetch('/weather').then(r => r.json()).then(data => {
                const c = data.current;
                document.getElementById('current-temp').textContent = c.temp !== null ? c.temp + '°' : '--';
                document.getElementById('current-icon').innerHTML = c.icon ? `<img src="${iconUrl(c.icon)}" alt="${c.icon}" style="height:2.5em;">` : '';
                document.getElementById('current-cond').textContent = c.condition || '--';
                document.getElementById('current-moon').textContent = moonToEmoji(c.moon_phase);
                document.getElementById('current-moon-label').textContent = c.moon_phase || '';
                document.getElementById('current-summary').textContent = c.daily_summary || '';

                // Hourly
                const hourlyDiv = document.getElementById('hourly');
                hourlyDiv.innerHTML = '';
                for (let i = 0; i < 5; i++) {
                    const h = data.hourly['hour'+i];
                    const el = document.createElement('div');
                    el.className = 'hour';
                    el.innerHTML = `
                        <div class="icon">${h.icon ? `<img src="${iconUrl(h.icon)}" alt="${h.icon}" style="height:1.5em;">` : ''}</div>
                        <div class="value">${h.temp !== null ? h.temp + '°' : '--'}</div>
                        <div class="label">Temp</div>
                        <div class="value">${h.precip !== null ? h.precip : '--'}</div>
                        <div class="label">Precip</div>
                        <div class="value">${h.precip_prob !== null ? (h.precip_prob*100).toFixed(0) + '%' : '--'}</div>
                        <div class="label">Chance</div>
                    `;
                    hourlyDiv.appendChild(el);
                }
                // Daily
                const dailyDiv = document.getElementById('daily');
                dailyDiv.innerHTML = '';
                for (let i = 0; i < 5; i++) {
                    const d = data.daily['day'+i];
                    const el = document.createElement('div');
                    el.className = 'day';
                    el.innerHTML = `
                        <div class="icon">${d.icon ? `<img src="${iconUrl(d.icon)}" alt="${d.icon}" style="height:1.5em;">` : ''}</div>
                        <div class="value">${d.temp_high !== null ? d.temp_high + '°' : '--'} / ${d.temp_low !== null ? d.temp_low + '°' : '--'}</div>
                        <div class="label">High / Low</div>
                        <div class="value">${d.precip !== null ? d.precip : '--'}</div>
                        <div class="label">Precip</div>
                        <div class="value">${d.precip_prob !== null ? (d.precip_prob*100).toFixed(0) + '%' : '--'}</div>
                        <div class="label">Chance</div>
                    `;
                    dailyDiv.appendChild(el);
                }
            });
        }
        window.onload = updateWeatherUI;
    </script>
</head>
<body>
    <div class="container">
        <h1>Weather Dashboard</h1>
        <div class="current">
            <div class="current-icon" id="current-icon"></div>
            <div class="current-details">
                <div><span id="current-temp">--</span> <span id="current-cond"></span></div>
                <div><span class="moon" id="current-moon"></span> <span id="current-moon-label"></span></div>
                <div class="summary" id="current-summary"></div>
            </div>
        </div>
        <div class="section-title">Next 5 Hours</div>
        <div class="hourly" id="hourly"></div>
        <div class="section-title">Next 5 Days</div>
        <div class="daily" id="daily"></div>
    </div>
</body>
</html>
''', ha_url=HA_URL)

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
