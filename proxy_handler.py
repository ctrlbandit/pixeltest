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
                global_profiles[user_id] = {"alters": {}, "autoproxy": {"mode": "off", "alter": None, "last_proxied": None}}
            
            if "autoproxy" not in global_profiles[user_id]:
                global_profiles[user_id]["autoproxy"] = {"mode": "off", "alter": None, "last_proxied": None}
            
            if command == "off":
                global_profiles[user_id]["autoproxy"]["mode"] = "off"
                global_profiles[user_id]["autoproxy"]["alter"] = None
                await message.channel.send("Autoproxy disabled.")
                
            elif command == "front":
                if len(parts) >= 3:
                    alter_name = " ".join(parts[2:])
                    user_alters = global_profiles[user_id].get("alters", {})
                    if alter_name in user_alters:
                        global_profiles[user_id]["autoproxy"]["mode"] = "front"
                        global_profiles[user_id]["autoproxy"]["alter"] = alter_name
                        await message.channel.send(f"✅ Autoproxy now set to front mode for {alter_name}!")
                    else:
                        await message.channel.send(f"Alter '{alter_name}' not found.")
                else:
                    await message.channel.send("Usage: `!autoproxy front <alter_name>`")
                
            elif command == "latch":
                if len(parts) >= 3:
                    # Traditional latch with specific alter name
                    alter_name = " ".join(parts[2:])
                    user_alters = global_profiles[user_id].get("alters", {})
                    if alter_name in user_alters:
                        global_profiles[user_id]["autoproxy"]["mode"] = "latch"
                        global_profiles[user_id]["autoproxy"]["alter"] = alter_name
                        await message.channel.send(f"✅ Autoproxy latched to {alter_name}.")
                    else:
                        await message.channel.send(f"Alter '{alter_name}' not found.")
                else:
                    # New latch mode - use last proxied alter
                    global_profiles[user_id]["autoproxy"]["mode"] = "latch"
                    await message.channel.send("✅ Last proxied alter will be in latch mode in this server!\n**Tip:** To turn off latch mode do `!autoproxy unlatch`, you can also switch to front mode with `!autoproxy front <name>` if you'd like!")
                    
            elif command == "unlatch":
                global_profiles[user_id]["autoproxy"]["mode"] = "front"
                global_profiles[user_id]["autoproxy"]["alter"] = None
                await message.channel.send("Autoproxy unlatched, switched to front mode.")
                
            else:
                await message.channel.send("Invalid autoproxy command. Use: `latch`, `unlatch`, `front`, or `off`.")
            
            return  # Don't process other commands for autoproxy

        user_profiles = global_profiles.get(user_id, {}).get("alters", {})

        # Check for autoproxy
        autoproxy_settings = global_profiles.get(user_id, {}).get("autoproxy", {"mode": "off", "alter": None, "last_proxied": None})
        
        # Check if message matches any existing proxy format
        message_matches_proxy = False
        for profile in user_profiles.values():
            proxy = profile.get("proxy", "")
            if proxy and proxy != "No proxy set":
                # Check {prefix}...{suffix} format
                if "..." in proxy:
                    parts = proxy.split("...")
                    if len(parts) == 2:
                        prefix, suffix = parts
                        if message.content.startswith(prefix) and message.content.endswith(suffix):
                            message_matches_proxy = True
                            break
                # Check suffix-only format
                elif proxy.startswith(('-', '~', '/', '\\', '|', '+', '=', '*', '&', '%', '$', '#', '@', '!', '?', '<', '>', '^')):
                    if message.content.endswith(proxy):
                        message_matches_proxy = True
                        break
                # Check prefix format
                elif message.content.startswith(proxy):
                    message_matches_proxy = True
                    break
        
        if autoproxy_settings["mode"] != "off" and not message_matches_proxy:
            target_alter = None
            
            if autoproxy_settings["mode"] == "latch":
                if autoproxy_settings["alter"]:
                    # Use specifically set alter
                    target_alter = autoproxy_settings["alter"]
                elif autoproxy_settings.get("last_proxied"):
                    # Use last proxied alter
                    target_alter = autoproxy_settings["last_proxied"]
            elif autoproxy_settings["mode"] == "front":
                # For front mode, use the first alter or implement your front logic
                if user_profiles:
                    target_alter = list(user_profiles.keys())[0]
            
            if target_alter and target_alter in user_profiles:
                profile = user_profiles[target_alter]
                displayname = profile.get("displayname") or target_alter
                proxy_avatar = profile.get("proxy_avatar") or profile.get("proxyavatar") or profile.get("avatar")
                
                # Get system tag for display name
                system_info = global_profiles.get(user_id, {}).get("system", {})
                system_tag = system_info.get("tag", "")
                webhook_name = f"{displayname} {system_tag}" if system_tag else displayname
                
                # Update last proxied alter
                global_profiles[user_id]["autoproxy"]["last_proxied"] = target_alter
                
                if message.guild:
                    webhook = await message.channel.create_webhook(name=webhook_name)

                    # ALWAYS try to set proxy avatar - NO EXCEPTIONS
                    if proxy_avatar:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(proxy_avatar) as response:
                                    if response.status == 200:
                                        avatar_bytes = await response.read()
                                        await webhook.edit(avatar=avatar_bytes)
                                        print(f"✅ Successfully set autoproxy avatar for {displayname}")
                                    else:
                                        print(f"⚠️ Failed to fetch autoproxy avatar for {displayname}: HTTP {response.status}")
                        except Exception as e:
                            print(f"⚠️ Error setting autoproxy avatar for {displayname}: {e}")
                            # Continue anyway - don't let avatar errors stop the proxy
                    else:
                        print(f"⚠️ No proxy avatar set for {displayname}")

                    await webhook.send(
                        content=message.content,
                        username=webhook_name,
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

            if proxy and proxy != "No proxy set":
                # Handle {prefix}...{suffix} format
                if "..." in proxy:
                    parts = proxy.split("...")
                    if len(parts) == 2:
                        prefix, suffix = parts
                        if message.content.startswith(prefix) and message.content.endswith(suffix):
                            # Remove prefix and suffix to get clean message
                            clean_message = message.content[len(prefix):-len(suffix) if suffix else len(message.content)].strip()
                            if not clean_message:  # Don't proxy empty messages
                                continue
                        else:
                            continue
                    else:
                        continue
                # Handle suffix-only format (like -aj, ~name, etc.)
                elif proxy.startswith(('-', '~', '/', '\\', '|', '+', '=', '*', '&', '%', '$', '#', '@', '!', '?', '<', '>', '^')):
                    if message.content.endswith(proxy):
                        # Remove suffix to get clean message
                        clean_message = message.content[:-len(proxy)].strip()
                        if not clean_message:  # Don't proxy empty messages
                            continue
                    else:
                        continue
                # Handle simple prefix format - but require text after prefix
                elif message.content.startswith(proxy):
                    clean_message = message.content[len(proxy):].strip()
                    if not clean_message:  # Don't proxy if no text after prefix
                        continue
                else:
                    continue

                # Update last proxied alter for latch mode
                if user_id in global_profiles and "autoproxy" in global_profiles[user_id]:
                    global_profiles[user_id]["autoproxy"]["last_proxied"] = name

                # Get system tag for display name
                system_info = global_profiles.get(user_id, {}).get("system", {})
                system_tag = system_info.get("tag", "")
                webhook_name = f"{displayname} {system_tag}" if system_tag else displayname

                if message.guild:
                    webhook = await message.channel.create_webhook(name=webhook_name)

                    # ALWAYS try to set proxy avatar - NO EXCEPTIONS
                    if proxy_avatar:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(proxy_avatar) as response:
                                    if response.status == 200:
                                        avatar_bytes = await response.read()
                                        await webhook.edit(avatar=avatar_bytes)
                                        print(f"✅ Successfully set autoproxy avatar for {displayname}")
                                    else:
                                        print(f"⚠️ Failed to fetch autoproxy avatar for {displayname}: HTTP {response.status}")
                        except Exception as e:
                            print(f"⚠️ Error setting autoproxy avatar for {displayname}: {e}")
                            # Continue anyway - don't let avatar errors stop the proxy
                    else:
                        print(f"⚠️ No proxy avatar set for {displayname}")

                    await webhook.send(
                        content=clean_message,
                        username=webhook_name,
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
                        username=webhook_name,
                        allowed_mentions=discord.AllowedMentions.none()
                    )

                return

        # Only process commands if no proxy was triggered
        await bot.process_commands(message)
