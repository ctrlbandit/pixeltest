import discord
import aiohttp
from data_manager import global_profiles, category_blacklist, channel_blacklist

def setup_proxy_handler(bot):
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.guild:
            guild_id = str(message.guild.id)
            category_id = message.channel.category_id

            if guild_id in category_blacklist and category_id in category_blacklist[guild_id]:
                await bot.process_commands(message)
                return

            if guild_id in channel_blacklist and message.channel.id in channel_blacklist[guild_id]:
                await bot.process_commands(message)
                return

        user_id = str(message.author.id)
        
        # Handle autoproxy commands
        if message.content.startswith('!autoproxy'):
            parts = message.content.split()
            if len(parts) < 2:
                await message.channel.send("Usage: `!autoproxy <latch|unlatch|front|off> [alter_name]`")
                return
                
            command = parts[1].lower()
            
            if user_id not in global_profiles:
                global_profiles[user_id] = {"alters": {}, "autoproxy": {"mode": "off", "alter": None}}
            
            if "autoproxy" not in global_profiles[user_id]:
                global_profiles[user_id]["autoproxy"] = {"mode": "off", "alter": None}
            
            if command == "off":
                global_profiles[user_id]["autoproxy"]["mode"] = "off"
                global_profiles[user_id]["autoproxy"]["alter"] = None
                await message.channel.send("Autoproxy disabled.")
                
            elif command == "front":
                global_profiles[user_id]["autoproxy"]["mode"] = "front"
                global_profiles[user_id]["autoproxy"]["alter"] = None
                await message.channel.send("Autoproxy set to front mode.")
                
            elif command == "latch":
                if len(parts) >= 3:
                    alter_name = " ".join(parts[2:])
                    user_alters = global_profiles[user_id].get("alters", {})
                    if alter_name in user_alters:
                        global_profiles[user_id]["autoproxy"]["mode"] = "latch"
                        global_profiles[user_id]["autoproxy"]["alter"] = alter_name
                        await message.channel.send(f"Autoproxy latched to {alter_name}.")
                    else:
                        await message.channel.send(f"Alter '{alter_name}' not found.")
                else:
                    await message.channel.send("Please specify an alter name for latch mode.")
                    
            elif command == "unlatch":
                global_profiles[user_id]["autoproxy"]["mode"] = "front"
                global_profiles[user_id]["autoproxy"]["alter"] = None
                await message.channel.send("Autoproxy unlatched, switched to front mode.")
                
            else:
                await message.channel.send("Invalid autoproxy command. Use: `latch`, `unlatch`, `front`, or `off`.")
            
            return  # Don't process other commands for autoproxy

        user_profiles = global_profiles.get(user_id, {}).get("alters", {})

        # Check for autoproxy
        autoproxy_settings = global_profiles.get(user_id, {}).get("autoproxy", {"mode": "off", "alter": None})
        
        if autoproxy_settings["mode"] != "off" and not any(message.content.startswith(proxy) for proxy in [profile.get("proxy", "") for profile in user_profiles.values() if profile.get("proxy")]):
            target_alter = None
            
            if autoproxy_settings["mode"] == "latch" and autoproxy_settings["alter"]:
                target_alter = autoproxy_settings["alter"]
            elif autoproxy_settings["mode"] == "front":
                # For front mode, use the first alter or implement your front logic
                if user_profiles:
                    target_alter = list(user_profiles.keys())[0]
            
            if target_alter and target_alter in user_profiles:
                profile = user_profiles[target_alter]
                displayname = profile.get("displayname") or target_alter
                proxy_avatar = profile.get("proxy_avatar") or profile.get("proxyavatar") or profile.get("avatar")
                
                if message.guild:
                    webhook = await message.channel.create_webhook(name=displayname)

                    if proxy_avatar:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(proxy_avatar) as response:
                                    if response.status == 200:
                                        content_type = response.headers.get('content-type', '').lower()
                                        if any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']):
                                            avatar_bytes = await response.read()
                                            await webhook.edit(avatar=avatar_bytes)
                                        else:
                                            print(f"Unsupported image type for {displayname}: {content_type}")
                                            try:
                                                avatar_bytes = await response.read()
                                                await webhook.edit(avatar=avatar_bytes)
                                            except:
                                                pass
                                    else:
                                        print(f"Failed to fetch avatar for {displayname}: {response.status}")
                        except Exception as e:
                            print(f"Error setting avatar for {displayname}: {e}")

                    await webhook.send(
                        content=message.content,
                        username=displayname,
                        allowed_mentions=discord.AllowedMentions.none()
                    )

                    try:
                        await message.delete()
                    except discord.Forbidden:
                        print(f"⚠️ Missing permissions to delete message in {message.channel.name}")

                    await webhook.delete()
                    return

        # Regular proxy detection
        for name, profile in user_profiles.items():
            proxy = profile.get("proxy")
            displayname = profile.get("displayname") or name

            proxy_avatar = profile.get("proxy_avatar") or profile.get("proxyavatar") or profile.get("avatar")

            if proxy and proxy != "No proxy set" and message.content.startswith(proxy):
                clean_message = message.content[len(proxy):].strip()

                if message.guild:
                    webhook = await message.channel.create_webhook(name=displayname)

                    if proxy_avatar:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(proxy_avatar) as response:
                                    if response.status == 200:
                                        content_type = response.headers.get('content-type', '').lower()
                                        if any(img_type in content_type for img_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']):
                                            avatar_bytes = await response.read()
                                            await webhook.edit(avatar=avatar_bytes)
                                        else:
                                            print(f"Unsupported image type for {displayname}: {content_type}")
                                            try:
                                                avatar_bytes = await response.read()
                                                await webhook.edit(avatar=avatar_bytes)
                                            except:
                                                pass
                                    else:
                                        print(f"Failed to fetch avatar for {displayname}: {response.status}")
                        except Exception as e:
                            print(f"Error setting avatar for {displayname}: {e}")

                    await webhook.send(
                        content=clean_message,
                        username=displayname,
                        allowed_mentions=discord.AllowedMentions.none()
                    )

                    try:
                        await message.delete()
                    except discord.Forbidden:
                        print(f"⚠️ Missing permissions to delete message in {message.channel.name}")

                    await webhook.delete()

                else:
                    await message.channel.send(
                        content=clean_message,
                        username=displayname,
                        allowed_mentions=discord.AllowedMentions.none()
                    )

                return

        # Only process commands if no proxy was triggered
        await bot.process_commands(message)
