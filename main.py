import requests
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta # timedelta যোগ করা হয়েছে
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
    
    # Render সার্ভারকে বাংলাদেশের সময়ে (+6 hours) সেট করা
    # এটি না করলে সার্ভার লন্ডনের সময় ধরে সিগন্যাল খুঁজবে
    now_utc = datetime.utcnow()
    now_bd = now_utc + timedelta(hours=6) 
    now_str = now_bd.strftime("%H:%M")
    
    upcoming = [s for s in signals if s['time'] > now_str]
    
    if upcoming:
        upcoming.sort(key=lambda x: x['time'])
        return jsonify(upcoming[0])
    return jsonify({"status": "no_signals"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
