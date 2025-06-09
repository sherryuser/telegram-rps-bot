# 🎮 Telegram Rock, Paper, Scissors Bot

A fun Telegram bot for group chats that plays a simplified version of Rock, Paper, Scissors by randomly selecting a "loser" from group members!

## ✨ Features

- **Group-Only Functionality**: Works exclusively in group chats
- **Random Loser Selection**: Randomly picks one eligible member as the "loser"
- **Smart Member Filtering**: 
  - Excludes bots automatically
  - Excludes users who left the group
  - Optional admin exclusion (configurable)
- **Fun Announcements**: 5 different randomized messages with emojis
- **Error Handling**: Gracefully handles permissions and edge cases
- **Async Support**: Built with python-telegram-bot v20+ async framework

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- A Telegram Bot Token (get one from [@BotFather](https://t.me/botfather))

### 2. Installation

```bash
# Clone or download the files
# Navigate to the project directory

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. Open `main.py`
2. Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
3. Optionally, set `SKIP_ADMINS = True` if you want to exclude admins from selection

### 4. Run the Bot

```bash
python main.py
```

## 🎯 Usage

### Commands

- `/rps` - Start a Rock, Paper, Scissors game (group only)
- `/start` - Get welcome message and instructions
- `/help` - Show help information

### Setup in Telegram

1. **Create a Bot**: Message [@BotFather](https://t.me/botfather) and create a new bot
2. **Add to Group**: Add your bot to a Telegram group
3. **Make Admin** (Recommended): Make the bot an admin to access member list
4. **Play**: Use `/rps` command in the group!

## 🛠 Configuration Options

### Admin Exclusion
```python
SKIP_ADMINS = False  # Set to True to exclude admins from selection
```

### Custom Messages
You can modify the `LOSER_MESSAGES` list to add your own fun messages:

```python
LOSER_MESSAGES = [
    "🎮 Rock, Paper, Scissors time! Today's loser is… {username} 😢",
    "🗿📄✂️ The RPS gods have spoken! {username} loses this round! 🎯",
    # Add your custom messages here...
]
```

## 📋 How It Works

1. **Command Trigger**: Someone types `/rps` in a group chat
2. **Member Detection**: Bot fetches eligible group members
3. **Filtering**: Excludes bots, inactive users, and optionally admins
4. **Random Selection**: Picks one eligible member as the "loser"
5. **Announcement**: Posts a fun message mentioning the selected user

## 🔧 Troubleshooting

### "I couldn't find enough eligible members"
- Make sure the group has active members
- Check if the bot has permission to see group members
- Consider making the bot an admin

### "Something went wrong!"
- Ensure the bot is an admin in the group
- Check your bot token is correct
- Verify the bot has necessary permissions

### Permission Issues
- The bot needs to be able to:
  - Read messages
  - Send messages
  - See group members (admin permission recommended)

## 📝 Technical Details

- **Framework**: python-telegram-bot 20.3+
- **Python Version**: 3.8+
- **Architecture**: Async/await pattern
- **Polling**: Uses long polling (not webhooks)
- **Error Handling**: Comprehensive exception handling
- **Logging**: Detailed logging for debugging

## 🤝 Contributing

Feel free to:
- Add more fun message variations
- Improve member detection logic
- Add new features
- Fix bugs

## 📄 License

This project is open source and available under the MIT License. 