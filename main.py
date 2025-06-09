import asyncio
import logging
import random
import os
from typing import List, Optional

from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ChatType, ChatMemberStatus

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8149948815:AAHH2uQksdYKnBGMqe-GnAm7a9mKV0P4TV8")  # Use environment variable in production
SKIP_ADMINS = False  # Set to True if you want to exclude admins from selection

# Fun messages for announcing the loser
LOSER_MESSAGES = [
    "🎮 Rock, Paper, Scissors time! Today's loser is… {username} 😢",
    "🗿📄✂️ The RPS gods have spoken! {username} loses this round! 🎯",
    "🎲 Fate has decided... {username} is the unlucky one today! 😅",
    "⚡ Lightning round! {username} got zapped by the RPS curse! ⚡😵",
    "🎪 Ladies and gentlemen, our loser of the day is... {username}! 🎭💔"
]

class RPSBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command handlers"""
        self.application.add_handler(CommandHandler("rps", self.rps_command))
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if update.effective_chat.type == ChatType.PRIVATE:
            await update.message.reply_text(
                "👋 Hello! I'm a Rock, Paper, Scissors bot for group chats!\n\n"
                "Add me to a group and use /rps to play! 🎮\n"
                "I'll randomly select a \"loser\" from the group members."
            )
        else:
            await update.message.reply_text(
                "🎮 RPS Bot is ready! Use /rps to start a game!"
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🎮 **Rock, Paper, Scissors Bot Help**\n\n"
            "**Commands:**\n"
            "• `/rps` - Start a Rock, Paper, Scissors game (group only)\n"
            "• `/help` - Show this help message\n\n"
            "**How it works:**\n"
            "1. Use `/rps` in a group chat\n"
            "2. I'll randomly select a \"loser\" from eligible members\n"
            "3. Have fun with the results! 😄\n\n"
            "**Note:** This bot only works in group chats, not private messages."
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def rps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rps command - main game logic"""
        chat = update.effective_chat
        
        # Check if command is used in a group
        if chat.type == ChatType.PRIVATE:
            await update.message.reply_text(
                "🚫 This command only works in group chats! "
                "Add me to a group and try again. 🎮"
            )
            return
        
        try:
            # Get eligible members
            eligible_members = await self.get_eligible_members(chat.id, context)
            
            if not eligible_members:
                await update.message.reply_text(
                    "😅 Oops! I couldn't find enough eligible members to play. "
                    "Make sure there are active members in the group!"
                )
                return
            
            # Select random loser
            loser = random.choice(eligible_members)
            
            # Create username mention
            if loser.user.username:
                username_mention = f"@{loser.user.username}"
            else:
                username_mention = loser.user.mention_html()
            
            # Select random message
            message = random.choice(LOSER_MESSAGES).format(username=username_mention)
            
            # Send the result
            await update.message.reply_text(
                message,
                parse_mode='HTML' if not loser.user.username else None
            )
            
            logger.info(f"RPS game in chat {chat.id}: {loser.user.full_name} was selected as loser")
            
        except Exception as e:
            logger.error(f"Error in rps_command: {e}")
            await update.message.reply_text(
                "😰 Something went wrong! I might not have permission to see group members, "
                "or there was another issue. Please make sure I'm an admin in the group."
            )
    
    async def get_eligible_members(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> List[ChatMember]:
        """Get list of eligible members for the game"""
        try:
            # Get chat administrators first to check bot permissions
            admins = await context.bot.get_chat_administrators(chat_id)
            
            # Check if bot is admin (needed to get member list)
            bot_is_admin = any(admin.user.id == context.bot.id for admin in admins)
            if not bot_is_admin:
                logger.warning(f"Bot is not admin in chat {chat_id}")
                # Try to get members anyway, might still work in some cases
            
            # Get chat member count
            member_count = await context.bot.get_chat_member_count(chat_id)
            
            if member_count < 3:  # Bot + at least 2 users
                return []
            
            eligible_members = []
            admin_ids = {admin.user.id for admin in admins} if SKIP_ADMINS else set()
            
            # For small groups, we can try to get all members
            # For larger groups, we'll work with administrators and recent active members
            if member_count <= 200:
                # Try to get all members (this might not work in all cases)
                try:
                    # This approach works for smaller groups where bot has access
                    for user_id in range(1, member_count + 100):  # Some buffer for deleted users
                        try:
                            member = await context.bot.get_chat_member(chat_id, user_id)
                            if self.is_eligible_member(member, admin_ids):
                                eligible_members.append(member)
                        except:
                            continue  # User doesn't exist or other error
                    
                    if eligible_members:
                        return eligible_members
                        
                except Exception as e:
                    logger.debug(f"Couldn't iterate through all members: {e}")
            
            # Fallback: Use administrators as the pool (excluding bot and optionally other admins)
            for admin in admins:
                if self.is_eligible_member(admin, admin_ids):
                    eligible_members.append(admin)
            
            return eligible_members
            
        except Exception as e:
            logger.error(f"Error getting eligible members: {e}")
            return []
    
    def is_eligible_member(self, member: ChatMember, admin_ids: set) -> bool:
        """Check if a member is eligible for the game"""
        # Skip if it's the bot itself
        if member.user.is_bot:
            return False
        
        # Skip if user is not in eligible status
        eligible_statuses = {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        }
        if member.status not in eligible_statuses:
            return False
        
        # Skip admins if configured to do so
        if SKIP_ADMINS and member.user.id in admin_ids:
            return False
        
        return True
    
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
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in the BOT_TOKEN variable!")
        print("You can get a token from @BotFather on Telegram")
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