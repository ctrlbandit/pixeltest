
import discord
from discord.ext import commands
import aiohttp
import aiofiles
import json
import os
from data_manager import global_profiles, save_profiles

def setup_import_export(bot):
    @bot.command(name="export_system")
    async def export_system(ctx):
        user_id = str(ctx.author.id)

        if user_id not in global_profiles or not global_profiles[user_id]:
            await ctx.send("❌ You don't have a system set up yet.")
            return

        user_data = global_profiles[user_id]
        export_filename = f"{user_id}_system_backup.json"

        try:
            async with aiofiles.open(export_filename, "w") as f:
                await f.write(json.dumps(user_data, indent=4))

            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                "📂 Here is your **Pixel** system export file. You can use this to **re-import** your system anytime:",
                file=discord.File(export_filename)
            )

            await ctx.send("✅ Your system has been exported and sent to your DMs.")

        except Exception as e:
            print(f"⚠️ Error exporting system for {ctx.author}: {e}")
            await ctx.send("❌ An error occurred while exporting your system. Please try again.")

    @bot.command(name="import_system")
    async def import_system(ctx):
        user_id = str(ctx.author.id)

        await ctx.send("📂 Please upload your **PixelBot** system backup JSON file.")

        try:
            message = await bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments
            )

            file_url = message.attachments[0].url

            async with message.channel.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        if response.status == 200:
                            data = await response.json()

                            global_profiles[user_id] = data
                            save_profiles(global_profiles)

                            await ctx.send("✅ Your system has been successfully imported.")
                        else:
                            await ctx.send("❌ Failed to download the file. Please try again.")

        except TimeoutError:
            await ctx.send("❌ You took too long to upload the file. Please try again.")

        except Exception as e:
            print(f"⚠️ Error importing system for {ctx.author}: {e}")
            await ctx.send("❌ An error occurred while importing your system. Please try again.")

    @bot.command(name="import_pluralkit")
    async def import_pluralkit(ctx):
        user_id = str(ctx.author.id)

        await ctx.send("📂 Please upload your **PluralKit** JSON export file.")

        try:
            message = await bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments
            )

            file_url = message.attachments[0].url

            async with message.channel.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        if response.status == 200:
                            data = await response.json()

                            if user_id not in global_profiles:
                                global_profiles[user_id] = {"system": {}, "alters": {}, "folders": {}}

                            system_data = data.get("system", {})
                            if system_data:
                                system_name = system_data.get("name", "Imported System")
                                system_description = system_data.get("description", "Imported from PluralKit")
                                system_pronouns = system_data.get("pronouns", "Not set")
                                system_avatar = system_data.get("avatar_url", None)
                                system_banner = system_data.get("banner", None)
                                system_color = system_data.get("color", "#8A2BE2")
                                
                                try:
                                    if not system_color or system_color.strip() == "":
                                        color_int = 0x8A2BE2
                                    else:
                                        color_int = int(system_color.lstrip("#"), 16)
                                except (ValueError, AttributeError):
                                    color_int = 0x8A2BE2

                                global_profiles[user_id]["system"] = {
                                    "name": system_name,
                                    "description": system_description,
                                    "pronouns": system_pronouns,
                                    "avatar": system_avatar,
                                    "banner": system_banner,
                                    "color": color_int
                                }

                            if "alters" not in global_profiles[user_id]:
                                global_profiles[user_id]["alters"] = {}
                            if "folders" not in global_profiles[user_id]:
                                global_profiles[user_id]["folders"] = {}

                            for member in data.get("members", []):
                                name = member.get("name", "Unnamed Alter")
                                display_name = member.get("display_name", name)
                                pronouns = member.get("pronouns", "Not set")
                                description = member.get("description", "No description provided.")
                                avatar = member.get("avatar_url", None)
                                proxy_avatar = member.get("proxy_avatar_url", avatar)
                                banner = member.get("banner", None)
                                color = member.get("color", "#8A2BE2")
                                proxy_tags = member.get("proxy_tags", [])

                                try:
                                    if not color or color.strip() == "":
                                        color_int = 0x8A2BE2
                                    else:
                                        color_int = int(color.lstrip("#"), 16)
                                except (ValueError, AttributeError):
                                    color_int = 0x8A2BE2

                                proxies = []
                                for tag in proxy_tags:
                                    prefix = tag.get("prefix", "") or ""
                                    suffix = tag.get("suffix", "") or ""

                                    if prefix and suffix:
                                        proxies.append(f"{prefix}...{suffix}")
                                    elif prefix:
                                        proxies.append(prefix)
                                    elif suffix:
                                        proxies.append(suffix)

                                main_proxy = proxies[0] if proxies else "No proxy set"

                                global_profiles[user_id]["alters"][name] = {
                                    "displayname": display_name if display_name else name,
                                    "pronouns": pronouns,
                                    "description": description,
                                    "avatar": avatar,
                                    "proxy_avatar": proxy_avatar,
                                    "banner": banner,
                                    "proxy": main_proxy,
                                    "aliases": [name],
                                    "color": color_int,
                                    "use_embed": True
                                }

                            save_profiles(global_profiles)
                            
                            member_count = len(data.get("members", []))
                            system_imported = "system and " if data.get("system") else ""
                            
                            await ctx.send(f"✅ Your PluralKit {system_imported}{member_count} profiles have been imported successfully!")
                        else:
                            await ctx.send("❌ Failed to download the file. Please try again.")

        except TimeoutError:
            await ctx.send("❌ You took too long to upload the file. Please try again.")

        except Exception as e:
            print(f"⚠️ Error importing PluralKit system for {ctx.author}: {e}")
            await ctx.send("❌ An error occurred while importing your system. Please try again.")
