import discord
from discord.ext import commands
from data_manager import global_profiles, save_profiles

def ensure_folders_exist(user_id):
    if user_id not in global_profiles:
        global_profiles[user_id] = {"system": {}, "alters": {}, "folders": {}}
    elif "folders" not in global_profiles[user_id]:
        global_profiles[user_id]["folders"] = {}

def setup_folder_commands(bot):
    @bot.command(name="create_folder")
    async def create_folder(ctx):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        await ctx.send("📁 What would you like to name this folder?")
        try:
            folder_name_msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            folder_name = folder_name_msg.content.strip()

            folders = global_profiles[user_id]["folders"]
            if folder_name in folders:
                await ctx.send(f"⚠️ Folder **{folder_name}** already exists. Use **!edit_folder** to modify it.")
                return

            folders[folder_name] = {
                "name": folder_name,
                "color": 0x8A2BE2,
                "banner": None,
                "icon": None,
                "alters": []
            }

            save_profiles(global_profiles)
            await ctx.send(f"✅ Folder **{folder_name}** created successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="edit_folder")
    async def edit_folder(ctx, folder_name: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name not in folders:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist. Use **!create_folder** to create it first.")
            return

        folder = folders[folder_name]

        try:
            await ctx.send(f"📝 Would you like to **rename** the folder **{folder_name}**? (yes/no)")
            rename_msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            if rename_msg.content.strip().lower() == "yes":
                await ctx.send("📁 What should the new **name** of this folder be?")
                new_name_msg = await bot.wait_for(
                    "message",
                    timeout=120,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                )
                new_name = new_name_msg.content.strip()
                if new_name != folder_name and new_name not in folders:
                    folders[new_name] = folder
                    del folders[folder_name]
                    folder["name"] = new_name
                    folder_name = new_name
                    await ctx.send(f"✅ Folder renamed to **{new_name}**.")

            await ctx.send("🎨 Please enter a **hex color code** for this folder (e.g., #8A2BE2), or type skip to keep the current color.")
            color_msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            color_code = color_msg.content.strip()

            if color_code.lower() != "skip":
                if not color_code.startswith("#") or len(color_code) != 7:
                    await ctx.send("❌ Invalid color code. Using the previous color.")
                else:
                    try:
                        folder["color"] = int(color_code.lstrip("#"), 16)
                        await ctx.send(f"🎨 Color updated to **{color_code}**.")
                    except ValueError:
                        await ctx.send("❌ Invalid color code. Using the previous color.")

            await ctx.send("🖼️ Please upload a **banner** image or provide a **direct image URL** (or type skip to keep the current banner).")
            banner_msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            if banner_msg.content.strip().lower() != "skip":
                if banner_msg.attachments:
                    folder["banner"] = banner_msg.attachments[0].url
                    await ctx.send("🖼️ Banner updated successfully.")
                elif banner_msg.content.startswith("http"):
                    folder["banner"] = banner_msg.content.strip()
                    await ctx.send("🖼️ Banner updated successfully.")
                else:
                    await ctx.send("❌ Invalid banner input. Keeping the previous banner.")

            await ctx.send("📌 Please upload an **icon** image or provide a **direct image URL** (or type skip to keep the current icon).")
            icon_msg = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            if icon_msg.content.strip().lower() != "skip":
                if icon_msg.attachments:
                    folder["icon"] = icon_msg.attachments[0].url
                    await ctx.send("📌 Icon updated successfully.")
                elif icon_msg.content.startswith("http"):
                    folder["icon"] = icon_msg.content.strip()
                    await ctx.send("📌 Icon updated successfully.")
                else:
                    await ctx.send("❌ Invalid icon input. Keeping the previous icon.")

            save_profiles(global_profiles)
            await ctx.send(f"✅ Folder **{folder_name}** updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="show_folder")
    async def show_folder(ctx, folder_name: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name not in folders:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist.")
            return

        folder = folders[folder_name]
        alters = folder["alters"]

        embed = discord.Embed(
            title=f"📁 Folder: {folder_name}",
            color=folder["color"],
            description="No alters in this folder." if not alters else ""
        )

        if alters:
            alter_list = "\n".join([f"- **{alter}**" for alter in alters])
            embed.add_field(name="👥 Alters", value=alter_list, inline=False)

        if folder["icon"]:
            embed.set_thumbnail(url=folder["icon"])

        if folder["banner"]:
            embed.set_image(url=folder["banner"])

        embed.set_footer(text=f"Folder: {folder_name}")

        await ctx.send(embed=embed)

    @bot.command(name="add_alters")
    async def add_alters(ctx, folder_name: str, *, alters: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name not in folders:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist. Use **!create_folder** to create it first.")
            return

        folder = folders[folder_name]
        alter_names = [name.strip() for name in alters.split(",")]

        added_alters = []
        skipped_alters = []

        for alter_name in alter_names:
            if alter_name in global_profiles[user_id]["alters"]:
                if alter_name not in folder["alters"]:
                    folder["alters"].append(alter_name)
                    added_alters.append(alter_name)
                else:
                    skipped_alters.append(alter_name)
            else:
                skipped_alters.append(alter_name)

        save_profiles(global_profiles)

        added_msg = f"✅ Added: {', '.join(added_alters)}" if added_alters else "No alters were added."
        skipped_msg = f"⚠️ Skipped: {', '.join(skipped_alters)}" if skipped_alters else ""
        await ctx.send(f"🗂️ Folder **{folder_name}** updated.\n{added_msg}\n{skipped_msg}")

    @bot.command(name="remove_alters")
    async def remove_alters(ctx, folder_name: str, *, alters: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name not in folders:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist.")
            return

        folder = folders[folder_name]
        alter_names = [name.strip() for name in alters.split(",")]

        removed_alters = []
        skipped_alters = []

        for alter_name in alter_names:
            if alter_name in folder["alters"]:
                folder["alters"].remove(alter_name)
                removed_alters.append(alter_name)
            else:
                skipped_alters.append(alter_name)

        save_profiles(global_profiles)

        removed_msg = f"🗑️ Removed: {', '.join(removed_alters)}" if removed_alters else "No alters were removed."
        skipped_msg = f"⚠️ Not in folder: {', '.join(skipped_alters)}" if skipped_alters else ""
        await ctx.send(f"🗂️ Folder **{folder_name}** updated.\n{removed_msg}\n{skipped_msg}")

    @bot.command(name="delete_folder")
    async def delete_folder(ctx, folder_name: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name in folders:
            del folders[folder_name]
            save_profiles(global_profiles)
            await ctx.send(f"🗑️ Folder **{folder_name}** has been deleted successfully.")
        else:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist.")

    @bot.command(name="wipe_folder_alters")
    async def wipe_folder_alters(ctx, folder_name: str):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        if folder_name in folders:
            folders[folder_name]["alters"] = []
            save_profiles(global_profiles)
            await ctx.send(f"🗑️ All alters have been removed from the folder **{folder_name}**.")
        else:
            await ctx.send(f"❌ Folder **{folder_name}** does not exist.")

    @bot.command(name="list_folders")
    async def list_folders(ctx):
        user_id = str(ctx.author.id)
        ensure_folders_exist(user_id)

        folders = global_profiles[user_id]["folders"]
        
        if not folders:
            await ctx.send("📁 You don't have any folders yet. Use `!create_folder` to create one!")
            return

        embed = discord.Embed(
            title="📁 Your Folders",
            color=0x8A2BE2,
            description=f"You have **{len(folders)}** folder(s):"
        )

        for folder_name, folder_data in folders.items():
            alter_count = len(folder_data.get("alters", []))
            alter_text = f"{alter_count} alter(s)"
            
            embed.add_field(
                name=f"📁 {folder_name}",
                value=f"**Alters:** {alter_text}",
                inline=True
            )

        embed.set_footer(text="Use !show_folder <name> to view a specific folder")
        await ctx.send(embed=embed)
