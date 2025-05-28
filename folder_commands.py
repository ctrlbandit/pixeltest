import discord
from discord.ext import commands
from data_manager import data_manager

async def ensure_folders_exist(user_id):
    profile = await data_manager.get_user_profile(user_id)
    if "folders" not in profile:
        profile["folders"] = {}
        await data_manager.save_user_profile(user_id, profile)
    return profile

def setup_folder_commands(bot):
    @bot.command(name="create_folder")
    async def create_folder(ctx, *, folder_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name in folders:
            await ctx.send(f"❌ Folder '{folder_name}' already exists.")
            return

        folders[folder_name] = {
            "name": folder_name,
            "description": "No description provided.",
            "color": 0x8A2BE2,
            "alters": []
        }

        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Folder '{folder_name}' created successfully!")

    @bot.command(name="edit_folder")
    async def edit_folder(ctx, folder_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name not in folders:
            await ctx.send(f"❌ Folder '{folder_name}' does not exist.")
            return

        folder = folders[folder_name]

        await ctx.send("What would you like to edit? (name, description, color)")

        try:
            field_msg = await bot.wait_for("message", timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            field = field_msg.content.strip().lower()

            if field not in ["name", "description", "color"]:
                await ctx.send(f"❌ Invalid field '{field}'. Use 'name', 'description', or 'color'.")
                return

            if field == "color":
                await ctx.send("🎨 Please enter the new embed color as a **hex code** (e.g., `#8A2BE2`).")
                color_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                color_code = color_msg.content.strip()

                if not color_code.startswith("#") or len(color_code) != 7:
                    await ctx.send("❌ Invalid color code. Please provide a **hex code** like `#8A2BE2`.")
                    return

                try:
                    color_int = int(color_code[1:], 16)
                except ValueError:
                    await ctx.send("❌ Invalid hex code. Please try again.")
                    return

                folder["color"] = color_int
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Color for folder '{folder_name}' updated successfully!")
                return

            if field == "name":
                await ctx.send(f"💬 Please enter the new name for folder '{folder_name}'.")
                name_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                new_name = name_msg.content.strip()

                if new_name in folders and new_name != folder_name:
                    await ctx.send(f"❌ A folder with the name '{new_name}' already exists.")
                    return

                # Update folder name
                folder["name"] = new_name
                if new_name != folder_name:
                    folders[new_name] = folders.pop(folder_name)

                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Folder renamed from '{folder_name}' to '{new_name}' successfully!")
                return

            await ctx.send(f"💬 Please enter the new value for **{field}**.")
            value_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            folder[field] = value_msg.content.strip()

            await data_manager.save_user_profile(user_id, profile)
            await ctx.send(f"✅ Folder **{folder.get('name', folder_name)}** updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="delete_folder")
    async def delete_folder(ctx, *, folder_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name not in folders:
            await ctx.send(f"❌ Folder '{folder_name}' does not exist.")
            return

        await ctx.send(f"⚠️ **Are you sure you want to delete the folder '{folder_name}'?**\nThis action **cannot** be undone. Type `CONFIRM` to proceed.")

        try:
            confirmation = await bot.wait_for(
                "message",
                timeout=60,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

            if confirmation.content.strip().upper() == "CONFIRM":
                del folders[folder_name]
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Folder '{folder_name}' has been deleted successfully.")
            else:
                await ctx.send("❌ Folder deletion canceled.")

        except TimeoutError:
            await ctx.send("❌ Folder deletion canceled. You took too long to confirm.")

    @bot.command(name="add_to_folder")
    async def add_to_folder(ctx, folder_name: str, *, alter_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name not in folders:
            await ctx.send(f"❌ Folder '{folder_name}' does not exist.")
            return

        if alter_name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{alter_name}' does not exist.")
            return

        if alter_name in folders[folder_name]["alters"]:
            await ctx.send(f"❌ Alter '{alter_name}' is already in folder '{folder_name}'.")
            return

        folders[folder_name]["alters"].append(alter_name)
        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Alter '{alter_name}' added to folder '{folder_name}' successfully!")

    @bot.command(name="remove_from_folder")
    async def remove_from_folder(ctx, folder_name: str, *, alter_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name not in folders:
            await ctx.send(f"❌ Folder '{folder_name}' does not exist.")
            return

        if alter_name not in folders[folder_name]["alters"]:
            await ctx.send(f"❌ Alter '{alter_name}' is not in folder '{folder_name}'.")
            return

        folders[folder_name]["alters"].remove(alter_name)
        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Alter '{alter_name}' removed from folder '{folder_name}' successfully!")

    @bot.command(name="list_folders")
    async def list_folders(ctx):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if not folders:
            await ctx.send("You don't have any folders set up yet. Use `!create_folder` to create one.")
            return

        folder_list = []
        for folder_name, folder_data in folders.items():
            alter_count = len(folder_data.get("alters", []))
            folder_list.append(f"📁 **{folder_name}** - {alter_count} alter(s)")

        embed = discord.Embed(
            title="📂 Your Folders",
            description="\n".join(folder_list),
            color=0x8A2BE2
        )

        await ctx.send(embed=embed)

    @bot.command(name="folder")
    async def folder(ctx, *, folder_name: str):
        user_id = str(ctx.author.id)
        profile = await ensure_folders_exist(user_id)
        
        folders = profile["folders"]

        if folder_name not in folders:
            await ctx.send(f"❌ Folder '{folder_name}' does not exist.")
            return

        folder = folders[folder_name]
        folder_alters = folder.get("alters", [])

        if not folder_alters:
            embed = discord.Embed(
                title=f"📁 {folder['name']}",
                description=f"**Description:** {folder.get('description', 'No description provided.')}\n\n*This folder is empty.*",
                color=folder.get("color", 0x8A2BE2)
            )
        else:
            alter_list = []
            for alter_name in folder_alters:
                if alter_name in profile.get("alters", {}):
                    alter_data = profile["alters"][alter_name]
                    proxy_text = alter_data.get('proxy', 'No proxy set')
                    alter_list.append(f"• **{alter_name}** — `{proxy_text}`")

            embed = discord.Embed(
                title=f"📁 {folder['name']}",
                description=f"**Description:** {folder.get('description', 'No description provided.')}\n\n" + "\n".join(alter_list),
                color=folder.get("color", 0x8A2BE2)
            )

        embed.set_footer(text=f"User ID: {user_id}")
        await ctx.send(embed=embed)
