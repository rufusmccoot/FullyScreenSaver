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

@app.route('/weather')
def weather():
    url = f"{HA_URL}/api/states/{WEATHER_ENTITY}"
    headers = {
        'Authorization': f'Bearer {HA_TOKEN}',
        'Content-Type': 'application/json',
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    temp = data['attributes']['temperature']
    condition = data['state']
    return jsonify({'temp': temp, 'condition': condition})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8282, debug=True)
