# TANVIR EXE Admin Panel

A Flask-based admin panel for managing UIDs with Discord bot integration.

## Features

- **Login System**: Secure login with 5 predefined users
- **UID Management**: Add, edit, and delete UIDs with expiry dates
- **Discord Integration**: Automatic notifications when UIDs are added
- **API Integration**: Connects to external server for UID operations
- **Security**: DevTools protection and right-click disabled

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Discord Channel ID:
   - Open `bot.py`
   - Replace `123456789012345678` on line 150 with your actual Discord channel ID
   - To get channel ID: Right click on channel in Discord → Copy Channel ID

3. Run the application:
```bash
python bot.py
```

## Usage

### Login Credentials
- **Username**: TANVIR, NOVA, BENX, LEDGEND, NIBIR
- **Password**: 1 (for all users)

### Adding UIDs
1. Enter UID (9-15 characters)
2. Select expiry date
3. Click "Register"
4. Discord notification will be sent automatically

### Editing UIDs
1. Click the gear icon (⚙) next to any UID
2. Modify UID or expiry date
3. Click "SAVE UPDATES"
4. System will delete old UID and add new one with updated settings

### Deleting UIDs
1. Click the gear icon (⚙) next to any UID
2. Click "DELETE ACCESS"
3. Confirm deletion

## API Endpoints

The application integrates with:
- `http://46.250.239.109:6020/uid?add={uid}&days={days}` - Add UID
- `http://46.250.239.109:6020/remove?uid={uid}` - Remove UID

## Discord Bot Configuration

The bot sends notifications in this format:
```
🚀 PREMIUM ACCESS GRANTED
👤 UID: {uid}
⏳ Time: {days} Days
📅 Status: ✅ Successfully Added
```

## Security Features

- Login required for all operations
- DevTools disabled
- Right-click context menu disabled
- UID length validation (9-15 characters)
- Future date validation for expiry

## Default Configuration

- **Port**: 5000
- **Host**: 0.0.0.0 (accessible from network)
- **Debug Mode**: Enabled

## Important Notes

1. Make sure your Discord bot has the necessary permissions for the target channel
2. The external API server must be accessible from where this application runs
3. All UIDs are stored in memory only (not persistent across restarts)
4. Session management is basic - consider implementing proper session storage for production

## Troubleshooting

- **Discord notifications not working**: Check channel ID and bot permissions
- **API errors**: Verify the external server is accessible and endpoints are correct
- **Login issues**: Ensure credentials match exactly (case-sensitive)
