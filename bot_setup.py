import discord
from discord.ext import commands, tasks
import random
import os
import logging

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

# Update the bot's status every 60 seconds
@bot.event
async def on_ready():
    print(f"✅ Pixel DID/OSDD Bot is online as {bot.user}")
    
    # Initialize MongoDB connection
    from data_manager import data_manager
    await data_manager.initialize()
    
    await update_status()
    change_status.start()

@tasks.loop(seconds=60)
async def change_status():
    await update_status()

async def update_status():
    new_status = random.choice(status_options)
    await bot.change_presence(activity=discord.Game(name=new_status))

@bot.event
async def on_disconnect():
    """Clean up MongoDB connection when bot disconnects"""
    from data_manager import data_manager
    await data_manager.close_connection()
