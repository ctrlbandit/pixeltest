import os
from dotenv import load_dotenv
from bot_setup import bot
from data_manager import global_profiles, category_blacklist, channel_blacklist
from system_commands import setup_system_commands
from alter_commands import setup_alter_commands
from folder_commands import setup_folder_commands
from admin_commands import setup_admin_commands
from import_export import setup_import_export
from utility_commands import setup_utility_commands
from proxy_handler import setup_proxy_handler

# Set up all command modules
setup_system_commands(bot)
setup_alter_commands(bot)
setup_folder_commands(bot)
setup_admin_commands(bot)
setup_import_export(bot)
setup_utility_commands(bot)
setup_proxy_handler(bot)

# Load environment variables from .env file
load_dotenv()

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv("NEW_BOT_TOKEN"))