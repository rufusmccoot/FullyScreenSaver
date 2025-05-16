from flask import Flask, render_template_string
from datetime import datetime

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
        function moveClock() {
            const clock = document.getElementById('time');
            // Get current position
            const prevLeft = parseFloat(clock.style.left) || 0;
            const prevTop = parseFloat(clock.style.top) || 0;
            // Temporarily set left/top to 0 to get accurate dimensions
            clock.style.left = '0px';
            clock.style.top = '0px';
            const clockRect = clock.getBoundingClientRect();
            const pad = 20; // px padding from edge
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            const maxLeft = vw - clockRect.width - pad;
            const maxTop = vh - clockRect.height - pad;
            const minLeft = pad;
            const minTop = pad;
            const newLeft = Math.random() * (maxLeft - minLeft) + minLeft;
            const newTop = Math.random() * (maxTop - minTop) + minTop;
            // Calculate distance and set transition duration for constant speed
            const dx = newLeft - prevLeft;
            const dy = newTop - prevTop;
            const distance = Math.sqrt(dx*dx + dy*dy);
            const speed = 10; // pixels per second (very slow for final use)
            const duration = distance / speed;
            clock.style.transition = `left ${duration}s cubic-bezier(0.4,0,0.2,1), top ${duration}s cubic-bezier(0.4,0,0.2,1)`;
            clock.style.left = `${newLeft}px`;
            clock.style.top = `${newTop}px`;
        }
        setInterval(updateTime, 1000);
        // Continuous random floating
        function startRandomFloat() {
            const clock = document.getElementById('time');
            function nextMove() {
                // Get current position
                const prevLeft = parseFloat(clock.style.left) || 0;
                const prevTop = parseFloat(clock.style.top) || 0;
                // Temporarily set left/top to 0 to get accurate dimensions
                clock.style.left = '0px';
                clock.style.top = '0px';
                const clockRect = clock.getBoundingClientRect();
                const pad = 20; // px padding from edge
                const vw = window.innerWidth;
                const vh = window.innerHeight;
                const maxLeft = vw - clockRect.width - pad;
                const maxTop = vh - clockRect.height - pad;
                const minLeft = pad;
                const minTop = pad;
                const newLeft = Math.random() * (maxLeft - minLeft) + minLeft;
                const newTop = Math.random() * (maxTop - minTop) + minTop;
                // Calculate distance and set transition duration for constant speed
                const dx = newLeft - prevLeft;
                const dy = newTop - prevTop;
                const distance = Math.sqrt(dx*dx + dy*dy);
                const speed = 10; // px/sec
                const duration = distance / speed;
                clock.style.transition = `left ${duration}s cubic-bezier(0.4,0,0.2,1), top ${duration}s cubic-bezier(0.4,0,0.2,1)`;
                clock.style.left = `${newLeft}px`;
                clock.style.top = `${newTop}px`;
                // When transition ends, move again
                clock.ontransitionend = function(e) {
                    if (e.propertyName === 'left' || e.propertyName === 'top') {
                        clock.ontransitionend = null;
                        setTimeout(nextMove, 100); // slight pause before next move
                    }
                };
            }
            setTimeout(nextMove, 500); // start floating after initial layout
        }

        // Color transition
        function randomColor() {
            let r, g, b, luminance;
            do {
                r = Math.floor(Math.random()*256);
                g = Math.floor(Math.random()*256);
                b = Math.floor(Math.random()*256);
                luminance = 0.2126*r + 0.7152*g + 0.0722*b;
            } while (luminance < 140);
            return `rgb(${r},${g},${b})`;
        }
        function startColorTransition() {
            const clock = document.getElementById('time');
            let currentColor = window.getComputedStyle(clock).color;
            function nextColor() {
                const newColor = randomColor();
                clock.style.transition = (clock.style.transition ? clock.style.transition + ', ' : '') + 'color 300s linear';
                clock.style.color = newColor;
                setTimeout(() => {
                    // After transition, set up for next
                    currentColor = newColor;
                    nextColor();
                }, 300000);
            }
            nextColor();
        }

        window.onload = function() {
            updateTime();
            // Wait for browser to paint the updated time
            requestAnimationFrame(() => {
                startRandomFloat();
                startColorTransition();
            });
        };




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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8282, debug=True)
