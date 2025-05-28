import discord
from discord.ext import commands
from data_manager import data_manager
import re

def setup_system_commands(bot):
    @bot.command(name="create_system")
    async def create_system(ctx, *, system_name: str):
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        
        if profile.get("system", {}).get("name"):
            await ctx.send("You already have a system set up. Use `!edit_system` to modify it.")
            return

        profile["system"] = {
            "name": system_name,
            "description": "No description provided.",
            "avatar": None,
            "banner": None,
            "pronouns": "Not set",
            "color": 0x8A2BE2,
            "created_at": None,
            "front_history": [],
            "system_avatar": None,
            "system_banner": None,
            "privacy_settings": {
                "show_front": True,
                "show_member_count": True,
                "allow_member_list": True
            }
        }

        success = await data_manager.save_user_profile(user_id, profile)
        if success:
            await ctx.send(f"✅ System '{system_name}' created successfully!")
        else:
            await ctx.send("❌ Failed to create system. Please try again.")

    @bot.command(name="edit_system")
    async def edit_system(ctx):
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        
        if not profile.get("system", {}).get("name"):
            await ctx.send("❌ You don't have a system set up yet. Use `!create_system` to create one.")
            return

        system = profile["system"]

        await ctx.send("What would you like to edit? (name, description, avatar, banner, pronouns, color, tag)")

        try:
            field_msg = await bot.wait_for("message", timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            field = field_msg.content.strip().lower()

            if field not in ["name", "description", "avatar", "banner", "pronouns", "color", "tag"]:
                await ctx.send(f"❌ Invalid field '{field}'. Use 'name', 'description', 'avatar', 'banner', 'pronouns', 'color', or 'tag'.")
                return

            if field in ["avatar", "banner"]:
                await ctx.send(f"📂 Please send the new **{field}** as an **attachment** or a **direct image URL**.")

                try:
                    image_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

                    if image_msg.attachments:
                        image_url = image_msg.attachments[0].url
                    elif image_msg.content.strip().startswith("http"):
                        image_url = image_msg.content.strip()
                    else:
                        await ctx.send(f"❌ Invalid {field} input. Please provide a direct image URL or attachment.")
                        return

                    system[field] = image_url
                    await data_manager.save_user_profile(user_id, profile)
                    await ctx.send(f"✅ {field.capitalize()} for your system updated successfully!")
                    return

                except TimeoutError:
                    await ctx.send("❌ You took too long to respond. Please try the command again.")
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

                system["color"] = color_int
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Color for your system updated successfully!")
                return

            await ctx.send(f"💬 Please enter the new value for **{field}**.")
            value_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            system[field] = value_msg.content.strip()

            await data_manager.save_user_profile(user_id, profile)
            await ctx.send(f"✅ System **{system.get('name', 'Unnamed System')}** updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="delete_system")
    async def delete_system(ctx):
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        
        if not profile.get("system", {}).get("name"):
            await ctx.send("❌ You don't have a system set up yet.")
            return

        await ctx.send("⚠️ **Are you sure you want to delete your entire system?**\nThis action **cannot** be undone. Type `CONFIRM` to proceed.")

        try:
            confirmation = await bot.wait_for(
                "message",
                timeout=60,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

            if confirmation.content.strip().upper() == "CONFIRM":
                # Reset to default profile
                default_profile = {
                    "user_id": user_id,
                    "system": {
                        "name": None,
                        "description": None,
                        "pronouns": None,
                        "created_at": None,
                        "front_history": [],
                        "system_avatar": None,
                        "system_banner": None,
                        "privacy_settings": {
                            "show_front": True,
                            "show_member_count": True,
                            "allow_member_list": True
                        }
                    },
                    "alters": {},
                    "folders": {},
                    "settings": {
                        "default_proxy_mode": "webhook",
                        "auto_delete_commands": True,
                        "dm_proxy_enabled": False,
                        "timezone": "UTC"
                    }
                }
                await data_manager.save_user_profile(user_id, default_profile)
                await ctx.send("✅ Your system has been deleted successfully.")
            else:
                await ctx.send("❌ System deletion canceled.")

        except TimeoutError:
            await ctx.send("❌ System deletion canceled. You took too long to confirm.")

    @bot.command(name="set_system_tag")
    async def set_system_tag(ctx, *, tag: str = None):
        """Set or update your system tag"""
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        
        if not profile.get("system", {}).get("name"):
            await ctx.send("❌ You don't have a system set up yet. Use `!create_system` to create one.")
            return

        if tag is None:
            await ctx.send("💬 Please enter your system tag (or 'none' to remove):")
            try:
                tag_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                tag = tag_msg.content.strip()
            except TimeoutError:
                await ctx.send("❌ You took too long to respond. Please try the command again.")
                return

        if tag.lower() == "none":
            profile["system"]["tag"] = None
            await data_manager.save_user_profile(user_id, profile)
            await ctx.send("✅ System tag removed successfully!")
        else:
            profile["system"]["tag"] = tag
            await data_manager.save_user_profile(user_id, profile)
            await ctx.send(f"✅ System tag set to: **{tag}**")

    @bot.command(name="system")
    async def system(ctx):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        system_info = profile.get("system", {})

        if not system_info or not system_info.get("name"):
            await ctx.send("❌ You don't have a system set up yet. Use `!create_system` to create one.")
            return

        system_name = system_info.get("name", "Unnamed System")
        system_pronouns = system_info.get("pronouns", "Not set")
        system_description = system_info.get("description", "No description provided.")
        system_avatar = system_info.get("avatar", None)
        system_banner = system_info.get("banner", None)
        system_color = system_info.get("color", 0x8A2BE2)
        system_tag = system_info.get("tag", None)

        def preserve_links(text):
            if text is None:
                return "No description provided."
            return re.sub(
                r"(?<!\\)\[([^\]]+)\]\((https?://[^\s)]+)\)",
                r"[\1](\2)",
                str(text)
            )

        system_description = preserve_links(system_description)

        # Build description with system tag if it exists
        description_parts = [
            f"**System Name**\n{system_name}\n",
            f"**Pronouns**\n{system_pronouns}\n"
        ]
        
        if system_tag:
            description_parts.append(f"**System Tag**\n{system_tag}\n")
            
        description_parts.extend([
            f"**Description**\n{system_description}\n",
            f"||Linked Discord Account: {ctx.author.mention}||"
        ])

        embed = discord.Embed(
            title=system_name,
            description="\n".join(description_parts),
            color=system_color
        )

        if system_avatar:
            embed.set_thumbnail(url=system_avatar)

        if system_banner:
            embed.set_image(url=system_banner)

        embed.set_footer(text=f"User ID: {user_id}")

        await ctx.send(embed=embed)

    @bot.command(name="wipe_alters")
    async def wipe_alters(ctx):
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        if not profile.get("alters"):
            await ctx.send("You don't have any alters to wipe.")
            return

        await ctx.send("⚠️ **Are you sure you want to wipe all alters from your system?**\nThis action **cannot** be undone. Type `CONFIRM` to proceed.")

        try:
            confirmation = await bot.wait_for(
                "message",
                timeout=60,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

            if confirmation.content.strip().upper() == "CONFIRM":
                profile["alters"] = {}
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send("✅ All alters have been wiped from your system.")
            else:
                await ctx.send("❌ Wipe canceled. Your alters are safe.")

        except TimeoutError:
            await ctx.send("❌ Wipe canceled. You took too long to confirm.")
