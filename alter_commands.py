
import discord
from discord.ext import commands
from discord.ui import View, Button
from data_manager import global_profiles, save_profiles
import re

def setup_alter_commands(bot):
    @bot.command(name="create")
    async def create(ctx, name: str, pronouns: str = "Not set", *, description: str = "No description provided."):
        user_id = str(ctx.author.id)

        if user_id not in global_profiles:
            global_profiles[user_id] = {"system": {}, "alters": {}}

        if "alters" not in global_profiles[user_id]:
            global_profiles[user_id]["alters"] = {}

        if name in global_profiles[user_id]["alters"]:
            await ctx.send(f"❌ An alter with the name **{name}** already exists.")
            return

        await ctx.send("🖼️ Would you like this profile to use **embeds**? (yes/no)")

        try:
            response = await bot.wait_for(
                "message",
                timeout=60,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
            use_embed = response.content.strip().lower() in ["yes", "y"]

            global_profiles[user_id]["alters"][name] = {
                "displayname": name,
                "pronouns": pronouns,
                "description": description,
                "avatar": None,
                "proxyavatar": None,
                "banner": None,
                "proxy": None,
                "aliases": [],
                "color": 0x8A2BE2,
                "use_embed": use_embed
            }

            save_profiles(global_profiles)
            await ctx.send(f"✅ Profile **{name}** created successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="edit")
    async def edit(ctx, name: str):
        user_id = str(ctx.author.id)

        if user_id not in global_profiles or name not in global_profiles[user_id]["alters"]:
            await ctx.send(f"❌ Profile '{name}' does not exist.")
            return

        profile = global_profiles[user_id]["alters"][name]

        await ctx.send("What would you like to edit? (name, displayname, pronouns, description, avatar, proxyavatar, banner, proxy, color)")

        try:
            field_msg = await bot.wait_for("message", timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            field = field_msg.content.strip().lower()

            valid_fields = ["name", "displayname", "pronouns", "description", "avatar", "proxyavatar", "banner", "proxy", "color"]
            if field not in valid_fields:
                await ctx.send(f"❌ Invalid field '{field}'. Please choose from: {', '.join(valid_fields)}.")
                return

            if field in ["avatar", "banner", "proxyavatar"]:
                await ctx.send(f"📂 Please send the new **{field}** as an **attachment** or a **direct image URL**.")
                image_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

                if image_msg.attachments:
                    image_url = image_msg.attachments[0].url
                elif image_msg.content.startswith("http"):
                    image_url = image_msg.content.strip()
                else:
                    await ctx.send(f"❌ Invalid {field} input. Please provide a direct image URL or attachment.")
                    return

                profile[field] = image_url
                save_profiles(global_profiles)
                await ctx.send(f"✅ {field.replace('_', ' ').capitalize()} for profile '{name}' updated successfully!")
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

                profile["color"] = color_int
                save_profiles(global_profiles)
                await ctx.send(f"✅ Color for profile '{name}' updated successfully!")
                return

            await ctx.send(f"💬 Please enter the new value for **{field}**.")
            value_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            profile[field] = value_msg.content.strip()

            save_profiles(global_profiles)
            await ctx.send(f"✅ Profile '{name}' updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="proxyavatar")
    async def proxyavatar(ctx, name: str):
        user_id = str(ctx.author.id)
        user_profiles = global_profiles.get(user_id, {}).get("alters", {})

        if name not in user_profiles:
            await ctx.send(f"❌ Alter **{name}** does not exist.")
            return

        profile = user_profiles[name]

        await ctx.send("📂 Please send the new **proxy avatar** as an **attachment** or a **direct image URL**.")

        try:
            image_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

            if image_msg.attachments:
                image_url = image_msg.attachments[0].url
            elif image_msg.content.startswith("http"):
                image_url = image_msg.content.strip()
            else:
                await ctx.send("❌ Invalid proxy avatar input. Please provide a direct image URL or attachment.")
                return

            profile["proxy_avatar"] = image_url
            save_profiles(global_profiles)
            await ctx.send(f"✅ Proxy avatar for **{name}** updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="show")
    async def show(ctx, name: str):
        user_id = str(ctx.author.id)
        user_profiles = global_profiles.get(user_id, {}).get("alters", {})

        if name not in user_profiles:
            await ctx.send(f"❌ Profile '{name}' does not exist.")
            return

        profile = user_profiles[name]
        displayname = profile.get("displayname", name)
        aliases = profile.get("aliases", [])
        alias_list = ", ".join(aliases) if aliases else "None"
        avatar_url = profile.get("avatar", None)
        proxy_avatar_url = profile.get("proxy_avatar") or profile.get("proxyavatar", None)
        banner_url = profile.get("banner", None)
        embed_color = profile.get("color", 0x8A2BE2)
        use_embed = profile.get("use_embed", True)

        description = profile.get("description", "No description provided") or "No description provided"

        description = discord.utils.escape_markdown(description)
        description = re.sub(r"\\\*", "*", description)
        description = re.sub(r"\\_", "_", description)
        description = re.sub(r"\\~", "~", description)
        description = re.sub(r"\\`", "`", description)
        description = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1](\2)", description)

        if use_embed:
            embed = discord.Embed(
                title=f"🗂️  {displayname}",
                color=embed_color
            )
            embed.add_field(name=" Display Name", value=displayname, inline=False)
            embed.add_field(name="👤 Alter Name", value=name, inline=False)
            embed.add_field(name=" Pronouns", value=profile.get("pronouns", "Not set"), inline=False)
            embed.add_field(name=" Proxy", value=profile.get("proxy", "Not set"), inline=False)
            embed.add_field(name=" Aliases", value=alias_list, inline=False)
            embed.add_field(name="📝 Description", value=description, inline=False)

            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

            if banner_url:
                embed.set_image(url=banner_url)

            if proxy_avatar_url:
                embed.set_footer(text=f"Proxy Avatar for {displayname}", icon_url=proxy_avatar_url)
            else:
                embed.set_footer(text=f"User ID: {user_id}")
            
            if proxy_avatar_url and proxy_avatar_url != avatar_url:
                embed.add_field(name="🔄 Proxy Avatar", value=f"[View Proxy Avatar]({proxy_avatar_url})", inline=False)

            await ctx.send(embed=embed)

        else:
            message = (
                f"**🗂️ Profile:** {displayname}\n"
                f"👤 **Alter Name:** {name}\n"
                f" **Pronouns:** {profile.get('pronouns', 'Not set')}\n"
                f" **Proxy:** {profile.get('proxy', 'Not set')}\n"
                f" **Aliases:** {alias_list}\n"
                f"📝 **Description:** {description}\n"
            )
            await ctx.send(message)

    class ProfilePaginator(View):
        def __init__(self, user_id, system_name, pages):
            super().__init__(timeout=180)
            self.user_id = user_id
            self.system_name = system_name
            self.pages = pages
            self.current_page = 0
            self.total_pages = len(pages)

            if self.total_pages == 1:
                self.disable_buttons()

        def disable_buttons(self):
            for child in self.children:
                if isinstance(child, Button):
                    child.disabled = True

        async def update_message(self, interaction):
            embed = discord.Embed(
                title=f"🗂️ Profiles for {self.system_name} (Page {self.current_page + 1}/{self.total_pages})",
                description="\n".join(self.pages[self.current_page]),
                color=0x8A2BE2
            )
            embed.set_footer(text=f"User ID: {self.user_id}")
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
        async def previous_page(self, interaction, button):
            self.current_page -= 1
            if self.current_page < 0:
                self.current_page = self.total_pages - 1
            await self.update_message(interaction)

        @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
        async def next_page(self, interaction, button):
            self.current_page += 1
            if self.current_page >= self.total_pages:
                self.current_page = 0
            await self.update_message(interaction)

    @bot.command(name="list_profiles")
    async def list_profiles(ctx):
        user_id = str(ctx.author.id)
        user_data = global_profiles.get(user_id, {})
        user_profiles = user_data.get("alters", {})

        system_info = user_data.get("system", {})
        system_name = system_info.get("name") or ctx.author.display_name

        if not user_profiles:
            await ctx.send("You don't have any profiles set up yet. Use `!create` to add a profile.")
            return

        profile_entries = sorted(
            [f"• **{name}** — `{profile.get('proxy', 'No proxy set')}`" for name, profile in user_profiles.items()],
            key=lambda x: x.split("**")[1].lower()
        )

        chunk_size = 15
        pages = [profile_entries[i:i + chunk_size] for i in range(0, len(profile_entries), chunk_size)]

        embed = discord.Embed(
            title=f"🗂️ Profiles for {system_name} (Page 1/{len(pages)})",
            description="\n".join(pages[0]),
            color=0x8A2BE2
        )
        embed.set_footer(text=f"User ID: {user_id}")

        message = await ctx.send(embed=embed, view=ProfilePaginator(user_id, system_name, pages))

    @bot.command()
    async def delete(ctx, name: str):
        user_id = str(ctx.author.id)
        if name not in global_profiles.get(user_id, {}).get("alters", {}):
            await ctx.send(f"Profile '{name}' does not exist.")
            return
        del global_profiles[user_id]["alters"][name]
        save_profiles(global_profiles)
        await ctx.send(f"Profile '{name}' has been deleted successfully.")

    @bot.command()
    async def alias(ctx, name: str, *, alias: str):
        user_id = str(ctx.author.id)
        if name not in global_profiles.get(user_id, {}).get("alters", {}):
            await ctx.send(f"Profile '{name}' does not exist.")
            return
        global_profiles[user_id]["alters"][name].setdefault("aliases", []).append(alias)
        save_profiles(global_profiles)
        await ctx.send(f"Alias '{alias}' added to profile '{name}' successfully!")

    @bot.command()
    async def remove_alias(ctx, name: str, *, alias: str):
        user_id = str(ctx.author.id)
        user_profiles = global_profiles.get(user_id, {}).get("alters", {})
        if name not in user_profiles:
            await ctx.send(f"Profile '{name}' does not exist.")
            return
        if alias not in user_profiles[name].get("aliases", []):
            await ctx.send(f"Alias '{alias}' does not exist for profile '{name}'.")
            return
        user_profiles[name]["aliases"].remove(alias)
        save_profiles(global_profiles)
        await ctx.send(f"Alias '{alias}' removed from profile '{name}' successfully!")
