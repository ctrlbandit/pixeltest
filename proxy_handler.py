import discord
import aiohttp
from data_manager import data_manager
import re
import asyncio
import io

def setup_proxy_handler(bot):
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        
        # Handle autoproxy commands
        if message.content.startswith("!autoproxy"):
            parts = message.content.split()
            if len(parts) >= 2:
                command = parts[1].lower()
                
                if command == "off":
                    await handle_autoproxy_command(message, "off")
                    
                elif command == "front":
                    if len(parts) >= 3:
                        alter_name = " ".join(parts[2:])
                        await handle_autoproxy_command(message, "front", alter_name)
                    else:
                        await message.channel.send("Usage: `!autoproxy front <alter_name>`")
                        
                elif command == "latch":
                    if len(parts) >= 3:
                        # Traditional latch with specific alter name
                        alter_name = " ".join(parts[2:])
                        await handle_autoproxy_command(message, "latch", alter_name)
                    else:
                        # New latch mode - use last proxied alter
                        await handle_autoproxy_command(message, "latch")
                        
                elif command == "unlatch":
                    await handle_autoproxy_command(message, "off")
                    
                else:
                    await message.channel.send("Invalid autoproxy command. Use: `off`, `front <alter>`, `latch [alter]`, or `unlatch`")
            
            return  # Don't process other commands for autoproxy

        # Process proxy messages
        proxied = await process_proxy_message(message)
        
        # Only process commands if no proxy was triggered
        if not proxied:
            await bot.process_commands(message)

async def handle_autoproxy_command(message, mode, alter_name=None):
    """Handle autoproxy mode changes"""
    user_id = str(message.author.id)
    profile = await data_manager.get_user_profile(user_id)
    
    # Ensure autoproxy settings exist
    if "autoproxy" not in profile:
        profile["autoproxy"] = {"mode": "off", "alter": None, "last_proxied": None}

    if mode == "off":
        profile["autoproxy"]["mode"] = "off"
        profile["autoproxy"]["alter"] = None
        await data_manager.save_user_profile(user_id, profile)
        await message.channel.send("🔴 **Autoproxy disabled.**")
        return

    elif mode == "front":
        user_alters = profile.get("alters", {})
        if alter_name and alter_name in user_alters:
            profile["autoproxy"]["mode"] = "front"
            profile["autoproxy"]["alter"] = alter_name
            await data_manager.save_user_profile(user_id, profile)
            await message.channel.send(f"🟢 **Autoproxy set to FRONT mode** for **{alter_name}**.")
        else:
            await message.channel.send("❌ **Invalid alter name.** Please specify a valid alter for front mode.")

    elif mode == "latch":
        user_alters = profile.get("alters", {})
        if alter_name and alter_name in user_alters:
            profile["autoproxy"]["mode"] = "latch"
            profile["autoproxy"]["alter"] = alter_name
            await data_manager.save_user_profile(user_id, profile)
            await message.channel.send(f"🟡 **Autoproxy set to LATCH mode** for **{alter_name}**.")
        else:
            # Enable latch mode with last proxied alter
            profile["autoproxy"]["mode"] = "latch"
            await data_manager.save_user_profile(user_id, profile)
            if profile["autoproxy"].get("last_proxied"):
                await message.channel.send("🟡 **Autoproxy set to LATCH mode.** Will use the last proxied alter.")
            else:
                await message.channel.send("🟡 **Autoproxy set to LATCH mode.** Send a message with any alter to start latching.")

async def process_proxy_message(message):
    """Process a message for proxy detection and handling"""
    # Check if channel is blacklisted first
    if message.guild:
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        category_id = str(message.channel.category.id) if message.channel.category else None
        
        if await is_blacklisted(guild_id, channel_id, category_id):
            return False  # Don't proxy in blacklisted channels
    
    user_id = str(message.author.id)
    profile = await data_manager.get_user_profile(user_id)
    user_profiles = profile.get("alters", {})
    
    # Get autoproxy settings
    autoproxy_settings = profile.get("autoproxy", {"mode": "off", "alter": None, "last_proxied": None})
    
    # Check for explicit proxy patterns first
    for name, alter_data in user_profiles.items():
        proxy_pattern = alter_data.get('proxy')
        if not proxy_pattern or proxy_pattern == "No proxy set":
            continue
            
        # Handle different proxy formats
        if '...' in proxy_pattern:
            # Format: prefix...suffix
            parts = proxy_pattern.split('...', 1)
            if len(parts) == 2:
                prefix, suffix = parts
                if message.content.startswith(prefix) and message.content.endswith(suffix):
                    content = message.content[len(prefix):-len(suffix)] if suffix else message.content[len(prefix):]
                    if content.strip():
                        return await send_proxy_message(message, name, content.strip(), alter_data)
        else:
            # Simple prefix format
            if message.content.startswith(proxy_pattern):
                content = message.content[len(proxy_pattern):].strip()
                if content:
                    return await send_proxy_message(message, name, content, alter_data)
    
    # Handle autoproxy if no explicit proxy found
    if autoproxy_settings["mode"] != "off":
        target_alter = None
        
        if autoproxy_settings["mode"] == "front" and autoproxy_settings.get("alter"):
            target_alter = autoproxy_settings["alter"]
        elif autoproxy_settings["mode"] == "latch" and autoproxy_settings.get("last_proxied"):
            target_alter = autoproxy_settings["last_proxied"]
        
        if target_alter and target_alter in user_profiles:
            alter_data = user_profiles[target_alter]
            # Update last proxied for latch mode
            profile["autoproxy"]["last_proxied"] = target_alter
            await data_manager.save_user_profile(user_id, profile)
            return await send_proxy_message(message, target_alter, message.content, alter_data)
    
    return False

async def send_proxy_message(message, alter_name, content, alter_data):
    """Send a proxied message"""
    try:
        # Get system info for system tag
        user_id = str(message.author.id)
        profile = await data_manager.get_user_profile(user_id)
        system_info = profile.get("system", {})
        
        # Delete original message
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await message.channel.send("⚠️ I don't have permission to delete messages. Please give me the 'Manage Messages' permission for proxying to work properly.")
            return False
        
        # Prepare message content with system tag if it exists
        final_content = content
        
        # Get alter details
        display_name = alter_data.get('displayname', alter_name)
        avatar_url = alter_data.get('proxy_avatar') or alter_data.get('avatar')
        
        # Add system tag to display name if it exists
        system_tag = system_info.get("tag")
        if system_tag:
            display_name = f"{display_name} {system_tag}"
        
        # Update last proxied for latch mode (only if autoproxy exists)
        if "autoproxy" in profile:
            profile["autoproxy"]["last_proxied"] = alter_name
            await data_manager.save_user_profile(user_id, profile)
        
        # Send as webhook message (the proper way for DID/OSDD systems)
        webhook = None
        try:
            # Try to find existing webhook
            webhooks = await message.channel.webhooks()
            for wh in webhooks:
                if wh.name == "Pixel Proxy":
                    webhook = wh
                    break
            
            # Create webhook if none exists
            if not webhook:
                webhook = await message.channel.create_webhook(name="Pixel Proxy")
            
            # Handle attachments
            files = []
            if message.attachments:
                for attachment in message.attachments:
                    try:
                        file_data = await attachment.read()
                        files.append(discord.File(io.BytesIO(file_data), filename=attachment.filename))
                    except:
                        final_content += f"\n[Attachment: {attachment.filename}]({attachment.url})"
            
            await webhook.send(
                content=final_content,
                username=display_name,
                avatar_url=avatar_url,
                files=files
            )
            
        except discord.Forbidden:
            # Fallback message if webhook fails
            await message.channel.send(f"⚠️ I don't have permission to create webhooks. Proxy message from {display_name}: {final_content}")
        
        return True
        
    except Exception as e:
        print(f"Error sending proxy message: {e}")
        return False

async def is_blacklisted(guild_id, channel_id, category_id):
    """Check if channel or category is blacklisted"""
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    category_id = str(category_id) if category_id else None
    
    # Check channel blacklist
    channel_blacklist = await data_manager.get_blacklist("channel", guild_id)
    if isinstance(channel_blacklist, dict) and channel_id in channel_blacklist:
        return True
    
    # Check category blacklist
    if category_id:
        category_blacklist = await data_manager.get_blacklist("category", guild_id)
        if isinstance(category_blacklist, dict) and category_id in category_blacklist:
            return True
    
    return False
