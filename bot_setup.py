
import discord
from discord.ext import commands, tasks
import random
import os

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)
bot.remove_command("help")

# Set up status options
status_options = [
    "Managing systems",
    "Proxying messages",
    "Organizing folders",
    "Handling proxies",
    "!pixelhelp for all commands",
    "Connecting systems",
    "Serving multiple servers"
]

# Update the bot's status every 60 seconds
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    await update_status()
    change_status.start()

@tasks.loop(seconds=60)
async def change_status():
    await update_status()

async def update_status():
    new_status = random.choice(status_options)
    await bot.change_presence(activity=discord.Game(name=new_status))
