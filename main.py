import requests
from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz # timezone হ্যান্ডেল করার জন্য
import os

app = Flask(__name__)

PASTEBIN_URL = "https://pastebin.com/raw/Vth05avr"

def get_signals():
    try:
        response = requests.get(PASTEBIN_URL, timeout=5)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            signals = []
            for line in lines:
                parts = line.split(';')
                if len(parts) == 4:
                    signals.append({"tf": parts[0], "asset": parts[1], "time": parts[2], "dir": parts[3]})
            return signals
    except: return []
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return "ALIVE", 200

@app.route('/api/fetch')
def api_fetch():
    signals = get_signals()
    if not signals: return jsonify({"status": "error"})
    
    # সরাসরি বাংলাদেশের সময় নেওয়া (Force Asia/Dhaka)
    tz = pytz.timezone('Asia/Dhaka')
    now_bd = datetime.now(tz)
    now_str = now_bd.strftime("%H:%M")
    
    upcoming = [s for s in signals if s['time'] > now_str]
    
    if upcoming:
        upcoming.sort(key=lambda x: x['time'])
        return jsonify(upcoming[0])
    return jsonify({"status": "no_signals"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
