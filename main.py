import os
import asyncio
import discord
from discord.ext import commands, tasks
import random
from dotenv import load_dotenv

from data_manager import data_manager         # db 

# ─── command‑group setup helpers ──────────────────────────────────── #
from system_commands  import setup_system_commands
from alter_commands   import setup_alter_commands
from folder_commands  import setup_folder_commands
from admin_commands   import setup_admin_commands
from utility_commands import setup_utility_commands
from proxy_handler    import setup_proxy_handler
import import_export                           

# ─── load environment variables  ──────────────────────── #
load_dotenv()

# ─── Discord Bot Setup ─────────────────────────────────── #

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)
bot.remove_command("help")

# Set up status options optimized for DID/OSDD systems
status_options = [
    "Supporting DID/OSDD systems",
    "Managing alters and proxies", 
    "Helping systems stay organized",
    "Fronting assistance available",
    "System proxy management",
    "!pixelhelp for all commands",
    "Connecting plural communities",
    "Alter creation and editing",
    "System folder organization",
    "Proxy avatar management"
]

# ─── Bot Events ────────────────────────────────────────── #

@bot.event
async def on_ready():
    print(f"✅ Pixel DID/OSDD Bot is online as {bot.user}")
    
    await update_status()
    change_status.start()

@bot.event
async def on_guild_remove(guild):
    """Clean up server data when the bot leaves a guild."""
    gid = str(guild.id)
    try:
        # Clear any blacklist docs that reference the guild
        await data_manager.save_blacklist("channel",  gid, {})
        await data_manager.save_blacklist("category", gid, {})
        print(f"🗑️  Cleaned up data for server: {guild.name} ({gid})")
    except Exception as e:
        print(f"⚠️  Error cleaning up data for {guild.name}: {e}")

# ─── Status Management ─────────────────────────────────── #

@tasks.loop(seconds=60)
async def change_status():
    await update_status()

async def update_status():
    new_status = random.choice(status_options)
    await bot.change_presence(activity=discord.Game(name=new_status))

# ─── Main Function ─────────────────────────────────────── #

async def main():
    """Initialize database, register commands, and start the bot."""
    await data_manager.initialize()               # connect to MongoDB 

    # Register every command group once
    setup_system_commands(bot)
    setup_alter_commands(bot)
    setup_folder_commands(bot)
    setup_admin_commands(bot)
    import_export.setup_import_export(bot)       
    setup_utility_commands(bot)
    setup_proxy_handler(bot)

    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        print("🛑 Bot shutdown requested...")
    except Exception as e:
        print(f"❌ Bot encountered an error: {e}")
    finally:
        # Clean up MongoDB connection only on actual shutdown
        print("🔌 Closing MongoDB connection...")
        await data_manager.close_connection()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Program interrupted")
