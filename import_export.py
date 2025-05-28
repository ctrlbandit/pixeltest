import discord
from discord.ext import commands
import aiohttp
import aiofiles
import json
import os
from data_manager import data_manager

def setup_import_export(bot):
    @bot.command(name="export_system")
    async def export_system(ctx):
        user_id = str(ctx.author.id)

        profile = await data_manager.get_user_profile(user_id)
        if not profile or not profile.get("system", {}).get("name"):
            await ctx.send("❌ You don't have a system set up yet.")
            return

        export_filename = f"{user_id}_system_backup.json"

        try:
            async with aiofiles.open(export_filename, "w") as f:
                await f.write(json.dumps(profile, indent=4))

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

                            # Ensure the data has the correct structure
                            data["user_id"] = user_id
                            success = await data_manager.save_user_profile(user_id, data)
                            
                            if success:
                                await ctx.send("✅ Your system has been successfully imported.")
                            else:
                                await ctx.send("❌ Failed to import system. Please try again.")
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

        await ctx.send("📂 Please upload your **PluralKit** export JSON file.")

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
                            pk_data = await response.json()

                            # Get existing profile or create new one
                            profile = await data_manager.get_user_profile(user_id)

                            # Import system info
                            if "name" in pk_data:
                                profile["system"] = {
                                    "name": pk_data.get("name", "Imported System"),
                                    "description": pk_data.get("description", "Imported from PluralKit"),
                                    "pronouns": pk_data.get("pronouns", "Not set"),
                                    "avatar": pk_data.get("avatar_url"),
                                    "banner": pk_data.get("banner"),
                                    "color": pk_data.get("color", 0x8A2BE2),
                                    "created_at": pk_data.get("created"),
                                    "front_history": [],
                                    "system_avatar": pk_data.get("avatar_url"),
                                    "system_banner": pk_data.get("banner"),
                                    "privacy_settings": {
                                        "show_front": True,
                                        "show_member_count": True,
                                        "allow_member_list": True
                                    }
                                }

                            # Import members/alters
                            if "members" in pk_data:
                                for member in pk_data["members"]:
                                    name = member.get("name", "Unknown")
                                    
                                    # Skip if alter already exists
                                    if name in profile.get("alters", {}):
                                        continue

                                    # Convert PluralKit proxy tags to simple format
                                    proxy_tags = member.get("proxy_tags", [])
                                    proxy = None
                                    if proxy_tags:
                                        prefix = proxy_tags[0].get("prefix", "")
                                        suffix = proxy_tags[0].get("suffix", "")
                                        proxy = f"{prefix}text{suffix}"

                                    alter_data = {
                                        "displayname": member.get("display_name") or name,
                                        "pronouns": member.get("pronouns", "Not set"),
                                        "description": member.get("description", "Imported from PluralKit"),
                                        "avatar": member.get("avatar_url"),
                                        "proxy_avatar": member.get("avatar_url"),
                                        "banner": member.get("banner"),
                                        "proxy": proxy,
                                        "aliases": [],
                                        "color": member.get("color", 0x8A2BE2),
                                        "use_embed": True,
                                        "created_at": member.get("created"),
                                        "role": None,
                                        "age": None,
                                        "birthday": member.get("birthday"),
                                        "front_time": 0,
                                        "last_front": None,
                                        "privacy": {
                                            "show_in_list": member.get("visibility", "public") == "public",
                                            "allow_proxy": True
                                        }
                                    }

                                    profile["alters"][name] = alter_data

                            # Import groups as folders
                            if "groups" in pk_data:
                                for group in pk_data["groups"]:
                                    group_name = group.get("name", "Unknown Group")
                                    
                                    # Skip if folder already exists
                                    if group_name in profile.get("folders", {}):
                                        continue

                                    profile["folders"][group_name] = {
                                        "name": group_name,
                                        "description": group.get("description", "Imported from PluralKit"),
                                        "color": group.get("color", 0x8A2BE2),
                                        "alters": []
                                    }

                                    # Add members to the folder
                                    for member_uuid in group.get("members", []):
                                        # Find member by UUID and add to folder
                                        for member in pk_data.get("members", []):
                                            if member.get("uuid") == member_uuid:
                                                member_name = member.get("name")
                                                if member_name and member_name not in profile["folders"][group_name]["alters"]:
                                                    profile["folders"][group_name]["alters"].append(member_name)

                            success = await data_manager.save_user_profile(user_id, profile)
                            
                            if success:
                                system_count = 1 if profile.get("system", {}).get("name") else 0
                                alter_count = len(profile.get("alters", {}))
                                folder_count = len(profile.get("folders", {}))
                                
                                await ctx.send(f"✅ **PluralKit import completed!**\n"
                                             f"📊 **Imported:** {system_count} system, {alter_count} alters, {folder_count} folders")
                            else:
                                await ctx.send("❌ Failed to save imported data. Please try again.")
                        else:
                            await ctx.send("❌ Failed to download the file. Please try again.")

        except TimeoutError:
            await ctx.send("❌ You took too long to upload the file. Please try again.")

        except Exception as e:
            print(f"⚠️ Error importing PluralKit data for {ctx.author}: {e}")
            await ctx.send("❌ An error occurred while importing your PluralKit data. Please try again.")
