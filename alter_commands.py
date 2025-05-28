import discord
from discord.ext import commands
from discord.ui import View, Button
from data_manager import data_manager
import re
import datetime

def setup_alter_commands(bot):
    @bot.command(name="create")
    async def create(ctx, name: str, pronouns: str = "Not set", *, description: str = "No description provided."):
        user_id = str(ctx.author.id)
        
        # Get user profile from MongoDB
        profile = await data_manager.get_user_profile(user_id)
        
        if name in profile.get("alters", {}):
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

            # Enhanced alter data structure for DID/OSDD systems
            alter_data = {
                "displayname": name,
                "pronouns": pronouns,
                "description": description,
                "avatar": None,
                "proxy_avatar": None,
                "banner": None,
                "proxy": None,
                "aliases": [],
                "color": 0x8A2BE2,
                "use_embed": use_embed,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "role": None,  # System role (protector, persecutor, caretaker, etc.)
                "age": None,
                "birthday": None,
                "front_time": 0,  # Total time fronting in minutes
                "last_front": None,
                "privacy": {
                    "show_in_list": True,
                    "allow_proxy": True
                }
            }

            # Create the alter using the data manager
            success = await data_manager.create_alter(user_id, name, alter_data)
            
            if success:
                await ctx.send(f"✅ Alter **{name}** created successfully! 🌟\n"
                             f"💡 *Tip: Use `!edit {name}` to add more details like role, age, or proxy tags.*")
            else:
                await ctx.send(f"❌ Failed to create alter **{name}**. Please try again.")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="edit")
    async def edit(ctx, name: str):
        user_id = str(ctx.author.id)
        
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        alter = profile["alters"][name]

        # Enhanced field options for DID/OSDD systems
        await ctx.send("What would you like to edit?\n"
                      "📝 **Basic Info:** `name`, `displayname`, `pronouns`, `description`\n"
                      "🖼️ **Visual:** `avatar`, `proxyavatar`, `banner`, `color`\n"
                      "🏷️ **System Info:** `proxy`, `role`, `age`, `birthday`\n"
                      "🔒 **Privacy:** `privacy`")

        try:
            field_msg = await bot.wait_for("message", timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            field = field_msg.content.strip().lower()

            valid_fields = ["name", "displayname", "pronouns", "description", "avatar", "proxyavatar", "banner", "proxy", "color", "role", "age", "birthday", "privacy"]
            if field not in valid_fields:
                await ctx.send(f"❌ Invalid field '{field}'. Please choose from the options above.")
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

                alter[field] = image_url
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ {field.replace('_', ' ').capitalize()} for alter '{name}' updated successfully!")
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

                alter["color"] = color_int
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Color for alter '{name}' updated successfully!")
                return

            if field == "role":
                await ctx.send("🎭 What is this alter's role in the system?\n"
                              "Common roles: `protector`, `caretaker`, `persecutor`, `host`, `gatekeeper`, `little`, `trauma holder`, `soother`, etc.\n"
                              "Enter the role or `none` to clear:")
                role_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                role_value = role_msg.content.strip()
                alter["role"] = None if role_value.lower() == "none" else role_value
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Role for alter '{name}' updated successfully!")
                return

            if field == "age":
                await ctx.send("🎂 What is this alter's age? (Enter a number, age range like '5-7', or 'unknown'):")
                age_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                age_value = age_msg.content.strip()
                alter["age"] = None if age_value.lower() in ["none", "unknown"] else age_value
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Age for alter '{name}' updated successfully!")
                return

            if field == "privacy":
                await ctx.send("🔒 Privacy settings for this alter:\n"
                              "Type `show` to allow in member lists, `hide` to hide from lists\n"
                              "Type `proxy` to allow proxying, `noproxy` to disable proxying")
                privacy_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                privacy_value = privacy_msg.content.strip().lower()
                
                if privacy_value == "show":
                    alter["privacy"]["show_in_list"] = True
                elif privacy_value == "hide":
                    alter["privacy"]["show_in_list"] = False
                elif privacy_value == "proxy":
                    alter["privacy"]["allow_proxy"] = True
                elif privacy_value == "noproxy":
                    alter["privacy"]["allow_proxy"] = False
                else:
                    await ctx.send("❌ Invalid privacy setting. Use `show`, `hide`, `proxy`, or `noproxy`.")
                    return
                    
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send(f"✅ Privacy settings for alter '{name}' updated successfully!")
                return

            await ctx.send(f"💬 Please enter the new value for **{field}**.")
            value_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            alter[field] = value_msg.content.strip()

            await data_manager.save_user_profile(user_id, profile)
            await ctx.send(f"✅ Alter '{name}' updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="show")
    async def show(ctx, name: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        alter = profile["alters"][name]
        displayname = alter.get("displayname", name)
        aliases = alter.get("aliases", [])
        alias_list = ", ".join(aliases) if aliases else "None"
        avatar_url = alter.get("avatar", None)
        proxy_avatar_url = alter.get("proxy_avatar") or alter.get("proxyavatar", None)
        banner_url = alter.get("banner", None)
        embed_color = alter.get("color", 0x8A2BE2)
        use_embed = alter.get("use_embed", True)

        description = alter.get("description", "No description provided") or "No description provided"

        # Enhanced description formatting
        description = discord.utils.escape_markdown(description)
        description = re.sub(r"\\\*", "*", description)
        description = re.sub(r"\\_", "_", description)
        description = re.sub(r"\\~", "~", description)
        description = re.sub(r"\\`", "`", description)
        description = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1](\2)", description)

        if use_embed:
            embed = discord.Embed(
                title=f"🗂️ {displayname}",
                color=embed_color
            )
            embed.add_field(name="👤 Alter Name", value=name, inline=True)
            embed.add_field(name="✨ Display Name", value=displayname, inline=True)
            embed.add_field(name="🏷️ Pronouns", value=alter.get("pronouns", "Not set"), inline=True)
            
            # System-specific fields
            if alter.get("role"):
                embed.add_field(name="🎭 Role", value=alter["role"], inline=True)
            if alter.get("age"):
                embed.add_field(name="🎂 Age", value=alter["age"], inline=True)
            
            embed.add_field(name="🔄 Proxy", value=alter.get("proxy", "Not set"), inline=True)
            embed.add_field(name="🏷️ Aliases", value=alias_list, inline=False)
            embed.add_field(name="📝 Description", value=description, inline=False)

            # Privacy indicators
            privacy = alter.get("privacy", {})
            privacy_status = []
            if not privacy.get("show_in_list", True):
                privacy_status.append("Hidden from lists")
            if not privacy.get("allow_proxy", True):
                privacy_status.append("Proxy disabled")
            if privacy_status:
                embed.add_field(name="🔒 Privacy", value=" • ".join(privacy_status), inline=False)

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
            # Non-embed format with enhanced info
            message = [
                f"**🗂️ {displayname}**",
                f"👤 **Alter Name:** {name}",
                f"🏷️ **Pronouns:** {alter.get('pronouns', 'Not set')}",
            ]
            
            if alter.get("role"):
                message.append(f"🎭 **Role:** {alter['role']}")
            if alter.get("age"):
                message.append(f"🎂 **Age:** {alter['age']}")
                
            message.extend([
                f"🔄 **Proxy:** {alter.get('proxy', 'Not set')}",
                f"🏷️ **Aliases:** {alias_list}",
                f"📝 **Description:** {description}"
            ])
            
            await ctx.send("\n".join(message))

    @bot.command(name="list_profiles", aliases=["list"])
    async def list_profiles(ctx):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        user_profiles = profile.get("alters", {})

        system_info = profile.get("system", {})
        system_name = system_info.get("name") or ctx.author.display_name

        if not user_profiles:
            await ctx.send("You don't have any alters set up yet. Use `!create` to add an alter.")
            return

        # Enhanced profile listing with role and privacy info
        profile_entries = []
        for name, alter_data in sorted(user_profiles.items(), key=lambda x: x[0].lower()):
            privacy = alter_data.get("privacy", {})
            if not privacy.get("show_in_list", True):
                continue  # Skip hidden alters
                
            role_text = f" ({alter_data['role']})" if alter_data.get("role") else ""
            proxy_text = alter_data.get('proxy', 'No proxy set')
            profile_entries.append(f"• **{name}**{role_text} — `{proxy_text}`")

        if not profile_entries:
            await ctx.send("No visible alters found. All alters may be set to private.")
            return

        # Pagination
        chunk_size = 15
        pages = [profile_entries[i:i + chunk_size] for i in range(0, len(profile_entries), chunk_size)]

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
                    title=f"🗂️ System Members for {self.system_name} (Page {self.current_page + 1}/{self.total_pages})",
                    description="\n".join(self.pages[self.current_page]),
                    color=0x8A2BE2
                )
                embed.set_footer(text=f"User ID: {self.user_id} • Total visible members: {sum(len(page) for page in self.pages)}")
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

        embed = discord.Embed(
            title=f"🗂️ System Members for {system_name} (Page 1/{len(pages)})",
            description="\n".join(pages[0]),
            color=0x8A2BE2
        )
        embed.set_footer(text=f"User ID: {user_id} • Total visible members: {len(profile_entries)}")

        await ctx.send(embed=embed, view=ProfilePaginator(user_id, system_name, pages))

    @bot.command()
    async def delete(ctx, name: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return
            
        del profile["alters"][name]
        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Alter '{name}' has been deleted successfully.")

    @bot.command()
    async def alias(ctx, name: str, *, alias: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return
            
        profile["alters"][name].setdefault("aliases", []).append(alias)
        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Alias '{alias}' added to alter '{name}' successfully!")

    @bot.command()
    async def remove_alias(ctx, name: str, *, alias: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        alter = profile["alters"][name]
        aliases = alter.get("aliases", [])

        if alias not in aliases:
            await ctx.send(f"❌ Alias '{alias}' does not exist for alter '{name}'.")
            return

        aliases.remove(alias)
        alter["aliases"] = aliases

        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Alias '{alias}' removed from alter '{name}'.")

    @bot.command(name="set_proxy")
    async def set_proxy(ctx, name: str, *, proxy: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        alter = profile["alters"][name]
        alter["proxy"] = proxy

        await data_manager.save_user_profile(user_id, profile)
        await ctx.send(f"✅ Proxy for alter '{name}' set to: `{proxy}`")

    @bot.command(name="proxy")
    async def proxy_command(ctx, name: str, *, message: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        alter = profile["alters"][name]
        displayname = alter.get("displayname", name)
        proxy_avatar = alter.get("proxy_avatar") or alter.get("proxyavatar") or alter.get("avatar")
        
        # Get system tag for display name
        system_info = profile.get("system", {})
        system_tag = system_info.get("tag", "")
        webhook_name = f"{displayname} {system_tag}" if system_tag else displayname

        if ctx.guild:
            webhook = await ctx.channel.create_webhook(name=webhook_name)

            # ALWAYS try to set proxy avatar - NO EXCEPTIONS
            if proxy_avatar:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(proxy_avatar) as response:
                            if response.status == 200:
                                avatar_bytes = await response.read()
                                await webhook.edit(avatar=avatar_bytes)
                                print(f"✅ Successfully set proxy avatar for {displayname}")
                            else:
                                print(f"⚠️ Failed to fetch avatar for {displayname}: HTTP {response.status}")
                except Exception as e:
                    print(f"⚠️ Error setting avatar for {displayname}: {e}")
                    # Continue anyway - don't let avatar errors stop the proxy
            else:
                print(f"⚠️ No proxy avatar set for {displayname}")

            await webhook.send(
                content=message,
                username=webhook_name,
                allowed_mentions=discord.AllowedMentions.none()
            )

            try:
                await ctx.message.delete()
            except discord.Forbidden:
                print(f"⚠️ Missing permissions to delete message in {ctx.channel.name}")

            await webhook.delete()
        else:
            await ctx.send(f"**{webhook_name}:** {message}")

    @bot.command(name="proxyavatar")
    async def proxyavatar(ctx, name: str):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if name not in profile.get("alters", {}):
            await ctx.send(f"❌ Alter '{name}' does not exist.")
            return

        await ctx.send(f"📂 Please send the new **proxy avatar** for {name} as an **attachment** or a **direct image URL**.")
        
        try:
            image_msg = await bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

            if image_msg.attachments:
                image_url = image_msg.attachments[0].url
            elif image_msg.content.startswith("http"):
                image_url = image_msg.content.strip()
            else:
                await ctx.send("❌ Invalid proxy avatar input. Please provide a direct image URL or attachment.")
                return

            alter = profile["alters"][name]
            alter["proxy_avatar"] = image_url

            await data_manager.save_user_profile(user_id, profile)
            await ctx.send(f"✅ Proxy avatar for alter '{name}' updated successfully!")

        except TimeoutError:
            await ctx.send("❌ You took too long to respond. Please try the command again.")

    @bot.command(name="autoproxy")
    async def autoproxy_command(ctx, mode: str = None, *, alter_name: str = None):
        user_id = str(ctx.author.id)
        profile = await data_manager.get_user_profile(user_id)
        
        if "autoproxy" not in profile:
            profile["autoproxy"] = {"mode": "off", "alter": None, "last_proxied": None}
        
        if mode is None:
            await ctx.send("Usage: `!autoproxy <latch|unlatch|front|off> [alter_name]`")
            return
            
        mode = mode.lower()
        
        if mode == "off":
            profile["autoproxy"]["mode"] = "off"
            profile["autoproxy"]["alter"] = None
            await data_manager.save_user_profile(user_id, profile)
            await ctx.send("Autoproxy disabled.")
            
        elif mode == "front":
            if alter_name:
                user_alters = profile.get("alters", {})
                if alter_name in user_alters:
                    profile["autoproxy"]["mode"] = "front"
                    profile["autoproxy"]["alter"] = alter_name
                    await data_manager.save_user_profile(user_id, profile)
                    await ctx.send(f"✅ Autoproxy now set to front mode for {alter_name}!")
                else:
                    await ctx.send(f"Alter '{alter_name}' not found.")
            else:
                await ctx.send("Usage: `!autoproxy front <alter_name>`")
                
        elif mode == "latch":
            if alter_name:
                # Traditional latch with specific alter name
                user_alters = profile.get("alters", {})
                if alter_name in user_alters:
                    profile["autoproxy"]["mode"] = "latch"
                    profile["autoproxy"]["alter"] = alter_name
                    await data_manager.save_user_profile(user_id, profile)
                    await ctx.send(f"✅ Autoproxy latched to {alter_name}.")
                else:
                    await ctx.send(f"Alter '{alter_name}' not found.")
            else:
                # New latch mode - use last proxied alter
                profile["autoproxy"]["mode"] = "latch"
                await data_manager.save_user_profile(user_id, profile)
                await ctx.send("✅ Last proxied alter will be in latch mode in this server!\n**Tip:** To turn off latch mode do `!autoproxy unlatch`, you can also switch to front mode with `!autoproxy front <name>` if you'd like!")
                
        elif mode == "unlatch":
            profile["autoproxy"]["mode"] = "off"
            profile["autoproxy"]["alter"] = None
            await data_manager.save_user_profile(user_id, profile)
            await ctx.send("✅ Autoproxy unlatched and disabled.")
            
        else:
            await ctx.send("Invalid autoproxy command. Use: `latch`, `unlatch`, `front`, or `off`.")
