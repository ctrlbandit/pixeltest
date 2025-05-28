import os
import asyncio
from dotenv import load_dotenv
from bot_setup import bot
from data_manager import data_manager
from system_commands import setup_system_commands
from alter_commands import setup_alter_commands
from folder_commands import setup_folder_commands
from admin_commands import setup_admin_commands
from import_export import setup_import_export
from utility_commands import setup_utility_commands
from proxy_handler import setup_proxy_handler


load_dotenv()

@bot.event
async def on_guild_remove(guild):
    """Clean up server data when bot leaves a server"""
    guild_id = str(guild.id)
    
    try:
        # Remove blacklist data for this server
        await data_manager.save_blacklist("channel", guild_id, {})
        await data_manager.save_blacklist("category", guild_id, {})
        
        print(f"🗑️ Cleaned up data for server: {guild.name} (ID: {guild_id})")
    except Exception as e:
        print(f"⚠️ Error cleaning up data for server {guild.name}: {e}")

async def main():
    # Initialize MongoDB connection
    await data_manager.initialize()
    
    # Setup command modules
    setup_system_commands(bot)
    setup_alter_commands(bot)
    setup_folder_commands(bot)
    setup_admin_commands(bot)
    setup_import_export(bot)
    setup_utility_commands(bot)
    setup_proxy_handler(bot)
    
    # Start the bot
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())