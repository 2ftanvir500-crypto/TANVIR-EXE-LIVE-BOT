from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import discord
import aiohttp
import asyncio
import requests
from datetime import datetime, timedelta
import os
import threading
import time
import json
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'tanvir-exe-admin-panel-secret-key-2024'

# Fetch configuration from pastebin
PASTEBIN_RAW_URL = "https://pastebin.com/raw/iaMqqsEk"

def fetch_config_from_pastebin():
    try:
        response = requests.get(PASTEBIN_RAW_URL, timeout=10)
        if response.status_code == 200:
            content = response.text
            users = {}
            discord_token = None
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('USER ') and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        user_part = parts[0].strip()
                        pass_part = parts[1].strip()
                        # Extract username from USER X: USERNAME format
                        if ':' in user_part:
                            username = user_part.split(':')[1].strip()
                            password = pass_part.split()[1] if 'PASS' in pass_part else pass_part
                            users[username] = password
                elif line.startswith('MTQ5') or line.startswith('M') and len(line) > 50:
                    discord_token = line.strip()
            
            return users, discord_token
        else:
            print(f"Failed to fetch from pastebin: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error fetching from pastebin: {e}")
        return None, None

# Fetch configuration
USERS, DISCORD_TOKEN = fetch_config_from_pastebin()

# Fallback configuration if pastebin fails
if not USERS:
    USERS = {
        'TANVIR': '1',
        'NOVA': '1',
        'BENX': '1',
        'LEDGEND': '1',
        'NIBIR': '1'
    }
    print("Using fallback user credentials")

if not DISCORD_TOKEN:
    print("ERROR: Discord token not found in Pastebin!")
    print("Please add Discord token to Pastebin configuration")
    DISCORD_TOKEN = None  # No fallback - must come from Pastebin

API_BASE_URL = "http://46.250.239.109:6020"

# Discord bot intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in USERS and USERS[username] == password:
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('index'))
    else:
        return "Invalid credentials", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/get_existing_uids', methods=['GET'])
def get_existing_uids():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Fetch existing UIDs from server (you may need to adjust this endpoint)
        # This is a placeholder - you might need to check your server API documentation
        # for the correct endpoint to list existing UIDs
        response = requests.get(f"{API_BASE_URL}/list", timeout=15)
        print(f"Fetch existing UIDs Response Status: {response.status_code}")
        print(f"Fetch existing UIDs Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                server_response = response.json()
                return jsonify({'success': True, 'data': server_response})
            except:
                return jsonify({'success': True, 'data': []})  # Empty list if can't parse
        else:
            return jsonify({'success': True, 'data': []})  # Empty list on error
            
    except Exception as e:
        print(f"Error fetching existing UIDs: {str(e)}")
        return jsonify({'success': True, 'data': []})  # Empty list on error

@app.route('/add_uid', methods=['POST'])
def add_uid():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    uid = data.get('uid')
    days = data.get('days')
    
    if not uid or not days:
        return jsonify({'error': 'UID and days are required'}), 400
    
    # Validate UID length
    if len(uid) < 9 or len(uid) > 15:
        return jsonify({'error': 'UID must be 9-15 characters long'}), 400
    
    try:
        # Add UID to server
        add_url = f"{API_BASE_URL}/uid?add={uid}&days={days}"
        print(f"Attempting to add UID: {add_url}")  # Debug log
        
        response = requests.get(add_url, timeout=15)
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                # Parse JSON response from server
                server_response = response.json()
                if server_response.get('success'):
                    # Send Discord notification
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(send_discord_notification(uid, days))
                        else:
                            loop.run_until_complete(send_discord_notification(uid, days))
                    except:
                        pass  # Discord notification failed but main functionality works
                    
                    # Add admin user tracking
                    admin_user = session.get('username', 'Unknown')
                    
                    return jsonify({
                        'success': True, 
                        'message': server_response.get('message', 'UID added successfully'),
                        'admin_user': admin_user,
                        'server_data': server_response
                    })
                else:
                    return jsonify({'error': server_response.get('message', 'Server returned error')}), 500
            except:
                # Fallback for non-JSON response
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(send_discord_notification(uid, days))
                    else:
                        loop.run_until_complete(send_discord_notification(uid, days))
                except:
                    pass  # Discord notification failed but main functionality works
                return jsonify({'success': True, 'message': 'UID added successfully'})
        else:
            return jsonify({'error': f'Server error: {response.status_code} - {response.text}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Connection timeout - Server not responding'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection failed - Server unreachable'}), 500
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/remove_uid', methods=['POST'])
def remove_uid():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    uid = data.get('uid')
    
    if not uid:
        return jsonify({'error': 'UID is required'}), 400
    
    try:
        # Remove UID from server
        remove_url = f"{API_BASE_URL}/remove?uid={uid}"
        print(f"Attempting to remove UID: {remove_url}")  # Debug log
        
        response = requests.get(remove_url, timeout=15)
        print(f"Remove API Response Status: {response.status_code}")
        print(f"Remove API Response Text: {response.text}")
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'UID removed successfully'})
        else:
            return jsonify({'error': f'Server error: {response.status_code} - {response.text}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Connection timeout - Server not responding'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection failed - Server unreachable'}), 500
    except Exception as e:
        print(f"Detailed remove error: {str(e)}")
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/edit_uid', methods=['POST'])
def edit_uid():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    uid = data.get('uid')
    new_days = data.get('days')
    
    if not uid or not new_days:
        return jsonify({'error': 'UID and days are required'}), 400
    
    try:
        # First remove old UID
        remove_url = f"{API_BASE_URL}/remove?uid={uid}"
        print(f"Attempting to edit UID - remove: {remove_url}")  # Debug log
        remove_response = requests.get(remove_url, timeout=15)
        print(f"Edit Remove Response Status: {remove_response.status_code}")
        print(f"Edit Remove Response Text: {remove_response.text}")
        
        if remove_response.status_code == 200:
            # Then add UID with new days
            add_url = f"{API_BASE_URL}/uid?add={uid}&days={new_days}"
            print(f"Attempting to edit UID - add: {add_url}")  # Debug log
            add_response = requests.get(add_url, timeout=15)
            print(f"Edit Add Response Status: {add_response.status_code}")
            print(f"Edit Add Response Text: {add_response.text}")
            
            if add_response.status_code == 200:
                return jsonify({'success': True, 'message': 'UID edited successfully'})
            else:
                return jsonify({'error': f'Failed to add updated UID: {add_response.status_code} - {add_response.text}'}), 500
        else:
            return jsonify({'error': f'Failed to remove old UID: {remove_response.status_code} - {remove_response.text}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Connection timeout - Server not responding'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection failed - Server unreachable'}), 500
    except Exception as e:
        print(f"Detailed edit error: {str(e)}")
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

async def send_discord_notification(uid, days):
    try:
        # You need to replace this with your actual Discord channel ID
        # To get channel ID: Right click on channel in Discord -> Copy Channel ID
        channel_id = 1482836987873591426  # Discord channel ID
        
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="🚀 PREMIUM ACCESS GRANTED", color=0x00FF00)
            embed.add_field(name="👤 UID", value=f"`{uid}`", inline=True)
            embed.add_field(name="⏳ Time", value=f"`{days} Days`", inline=True)
            embed.add_field(name="📅 Status", value="✅ Successfully Added", inline=False)
            
            if bot.user.avatar:
                embed.set_thumbnail(url=bot.user.avatar.url)
            
            await channel.send(embed=embed)
        else:
            print(f"Channel not found. Make sure the bot has access to the channel ID: {channel_id}")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')

# Uptime Robot Monitoring Endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for uptime monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'TANVIR EXE ADMIN PANEL',
        'uptime': time.time() - start_time
    })

@app.route('/status')
def status():
    """Detailed status endpoint for monitoring"""
    try:
        # Test API connectivity
        api_status = "connected"
        try:
            response = requests.get(f"{API_BASE_URL}/list", timeout=5)
            if response.status_code != 200:
                api_status = "error"
        except:
            api_status = "disconnected"
        
        # Test Discord bot status
        discord_status = "connected" if bot.is_ready() else "disconnected"
        
        return jsonify({
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - start_time,
            'api_status': api_status,
            'discord_status': discord_status,
            'active_sessions': len([s for s in session.keys() if 'logged_in' in str(s)]),
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/robots.txt')
def robots_txt():
    """Robots.txt for SEO and crawling"""
    return """User-agent: *
Disallow: /admin_login
Disallow: /add_uid
Disallow: /remove_uid
Disallow: /edit_uid
Allow: /
"""

# Start Discord bot in a separate thread
def run_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.start(DISCORD_TOKEN))

# Hosting Configuration
start_time = time.time()

if __name__ == '__main__':
    print("=" * 50)
    print("TANVIR EXE ADMIN PANEL - STARTING")
    print("=" * 50)
    print(f"Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Discord Bot: {'Connected' if bot.is_ready() else 'Connecting...'}")
    print(f"Health Check: http://localhost:5000/health")
    print(f"Status Page: http://localhost:5000/status")
    print("=" * 50)
    
    # Start Discord bot in a separate thread
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask app with production settings
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        threaded=True
    )