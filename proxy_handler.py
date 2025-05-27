
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
                return

            if guild_id in channel_blacklist and message.channel.id in channel_blacklist[guild_id]:
                return

        user_id = str(message.author.id)
        user_profiles = global_profiles.get(user_id, {}).get("alters", {})

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

        await bot.process_commands(message)
