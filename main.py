import asyncio
import logging
import random
import os
from datetime import datetime, timedelta
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatType

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Get token from environment variable
GAME_DURATION = 30  # seconds to collect participants

# Fun messages for announcing the winner
WINNER_MESSAGES = [
    "🏆 Rock, Paper, Scissors Champion: {username}! 🎉",
    "🎮 Victory! {username} wins this round! 👑",
    "⚡ {username} emerges victorious! ⚡🎯",
    "🎪 Ladies and gentlemen, our winner is... {username}! 🏅",
    "🗿📄✂️ The RPS gods chose {username} as today's champion! 🎊"
]

# Participation messages
PARTICIPATION_MESSAGES = [
    "🎮 I'm in! Let's play!",
    "🔥 Ready for battle!",
    "⚡ Count me in!",
    "🎯 I'm feeling lucky!",
    "🏆 Let's do this!"
]

class RPSBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        # Track active games per chat
        self.active_games: Dict[int, Dict] = {}  # chat_id -> game_info
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command handlers"""
        self.application.add_handler(CommandHandler("rps", self.rps_command))
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        # Handle replies to game messages
        self.application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, self.handle_reply))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if update.effective_chat.type == ChatType.PRIVATE:
            await update.message.reply_text(
                "👋 Hello! I'm a Rock, Paper, Scissors bot for group chats!\n\n"
                "🎮 **How to play:**\n"
                "1. Add me to a group\n"
                "2. Someone uses `/rps` to start a game\n"
                "3. Players reply to my message or click the button\n"
                "4. I'll pick a random winner!\n\n"
                "Let's have some fun! 🎉"
            )
        else:
            await update.message.reply_text(
                "🎮 RPS Bot is ready! Use `/rps` to start a game!"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🎮 **Rock, Paper, Scissors Bot Help**\n\n"
            "**How to Play:**\n"
            "1. Use `/rps` in a group chat\n"
            "2. Players reply to my message or click 'Join Game'\n"
            "3. After 30 seconds, I'll announce the winner!\n\n"
            "**Commands:**\n"
            "• `/rps` - Start a new game (group only)\n"
            "• `/help` - Show this help message\n\n"
            "**Rules:**\n"
            "• Only works in group chats\n"
            "• One game per group at a time\n"
            "• Anyone can participate by replying\n"
            "• Winner is chosen randomly from participants\n\n"
            "Have fun! 🎉"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def rps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rps command - start a new game"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if command is used in a group
        if chat.type == ChatType.PRIVATE:
            await update.message.reply_text(
                "🚫 This command only works in group chats! "
                "Add me to a group and try again. 🎮"
            )
            return
        
        # Check if there's already an active game
        if chat.id in self.active_games:
            time_left = self.active_games[chat.id]['end_time'] - datetime.now()
            if time_left.total_seconds() > 0:
                await update.message.reply_text(
                    f"⏳ Game already in progress! {int(time_left.total_seconds())} seconds left to join."
                )
                return
            else:
                # Clean up expired game
                del self.active_games[chat.id]
        
        # Create join button
        keyboard = [
            [InlineKeyboardButton("🎮 Join Game!", callback_data=f"join_{chat.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send game announcement
        game_message = await update.message.reply_text(
            f"🎮 **Rock, Paper, Scissors Game Started!**\n\n"
            f"🎯 Started by: {user.first_name}\n"
            f"⏰ **{GAME_DURATION} seconds** to join!\n\n"
            f"**How to join:**\n"
            f"• Click the '🎮 Join Game!' button below\n"
            f"• OR reply to this message with anything\n\n"
            f"🏆 Winner will be chosen randomly! Good luck! 🍀",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Store game info
        end_time = datetime.now() + timedelta(seconds=GAME_DURATION)
        self.active_games[chat.id] = {
            'message_id': game_message.message_id,
            'participants': set(),
            'end_time': end_time,
            'starter': user
        }
        
        # Add the game starter as first participant
        self.active_games[chat.id]['participants'].add(user.id)
        
        logger.info(f"RPS game started in chat {chat.id} by {user.full_name}")
        
        # Schedule game end
        await asyncio.sleep(GAME_DURATION)
        await self.end_game(chat.id, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        user = query.from_user
        
        # Always acknowledge the callback query first
        await query.answer()
        
        if query.data.startswith("join_"):
            chat_id = int(query.data.split("_")[1])
            
            # Check if game is still active
            if chat_id not in self.active_games:
                await query.edit_message_text(
                    "❌ This game has ended! Use /rps to start a new game.",
                    parse_mode='Markdown'
                )
                return
            
            # Check if game time is up
            if datetime.now() > self.active_games[chat_id]['end_time']:
                await query.edit_message_text(
                    "⏰ Time's up! This game has ended. Use /rps to start a new game.",
                    parse_mode='Markdown'
                )
                return
            
            # Add participant
            if user.id not in self.active_games[chat_id]['participants']:
                self.active_games[chat_id]['participants'].add(user.id)
                participants_count = len(self.active_games[chat_id]['participants'])
                
                # Send a confirmation message in the chat
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🎮 {user.first_name} joined the game! Total players: {participants_count}"
                )
                logger.info(f"User {user.full_name} joined RPS game in chat {chat_id}")
            else:
                # Send a message that they're already in
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ {user.first_name}, you're already in the game!"
                )
    
    async def handle_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle replies to game messages"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if this is a reply to our game message
        if chat.id not in self.active_games:
            return
        
        replied_message = update.message.reply_to_message
        if not replied_message or replied_message.message_id != self.active_games[chat.id]['message_id']:
            return
        
        # Check if game is still active
        if datetime.now() > self.active_games[chat.id]['end_time']:
            return
        
        # Add participant
        if user.id not in self.active_games[chat.id]['participants']:
            self.active_games[chat.id]['participants'].add(user.id)
            participants_count = len(self.active_games[chat.id]['participants'])
            
            # Send confirmation with random participation message
            confirmation = random.choice(PARTICIPATION_MESSAGES)
            await update.message.reply_text(
                f"{confirmation}\n🎯 Players in game: {participants_count}"
            )
            logger.info(f"User {user.full_name} joined RPS game in chat {chat.id} via reply")
    
    async def end_game(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """End the game and announce winner"""
        if chat_id not in self.active_games:
            return
        
        game_info = self.active_games[chat_id]
        participants = game_info['participants']
        
        try:
            if len(participants) < 2:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="😅 **Game Ended**\n\nNot enough players joined! Need at least 2 players to have a winner.\n\nTry again with `/rps`! 🎮",
                    parse_mode='Markdown'
                )
            else:
                # Get winner
                winner_id = random.choice(list(participants))
                
                try:
                    # Get winner info
                    winner_member = await context.bot.get_chat_member(chat_id, winner_id)
                    winner_user = winner_member.user
                    
                    # Create winner mention
                    if winner_user.username:
                        winner_mention = f"@{winner_user.username}"
                    else:
                        winner_mention = winner_user.mention_html()
                    
                    # Select random winner message
                    winner_message = random.choice(WINNER_MESSAGES).format(username=winner_mention)
                    
                    # Send winner announcement
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎊 **Game Results** 🎊\n\n{winner_message}\n\n🎯 Total players: {len(participants)}\n\nCongratulations! 🏆",
                        parse_mode='HTML' if not winner_user.username else 'Markdown'
                    )
                    
                    logger.info(f"RPS game in chat {chat_id} won by {winner_user.full_name}")
                    
                except Exception as e:
                    logger.error(f"Error getting winner info: {e}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎊 **Game Ended!** 🎊\n\n🏆 We have a winner!\n🎯 Total players: {len(participants)}\n\nCongratulations! 🎉"
                    )
        
        except Exception as e:
            logger.error(f"Error ending game in chat {chat_id}: {e}")
        
        finally:
            # Clean up
            if chat_id in self.active_games:
                del self.active_games[chat_id]
    
    async def run(self):
        """Start the bot with polling"""
        logger.info("Starting RPS Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        # Keep the bot running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

async def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        print("❌ Please set your bot token in the BOT_TOKEN environment variable!")
        print("You can get a token from @BotFather on Telegram")
        print("Set it using: export BOT_TOKEN='your_token_here'")
        return
    
    bot = RPSBot(BOT_TOKEN)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}") 