# FullyScreenSaver

A Flask-based HTTP server that displays a fullscreen digital clock, designed for use as a screensaver on kiosk-style tablets (e.g., Amazon Fire tablets running Fully Kiosk Browser).

## Features
- Large, readable 12-hour digital clock with a 7-segment display font
- Smooth, continuous floating movement to prevent screen burn-in
- Clock color gently transitions every 5 minutes for visual interest
- Designed for use on dark backgrounds (living room, next to a TV, etc.)
- Easily extendable for additional info (date, weather, etc.)

## Usage
1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the server:**
   ```bash
   python app.py
   ```
3. **Point your tablet or browser to:**
   ```
   http://<your-pc-ip>:8282
   ```

## Notes
- Designed for use in Fully Kiosk Browser or similar tablet kiosk environments.
- The clock is highly visible, non-distracting, and burn-in safe.
- To add weather or other info, see the `app.py` and extend as needed.

## License
MIT (or specify your preferred license)
