import discord
from discord.ext import commands
from discord.ui import View, Button
import json

def setup_utility_commands(bot):
    suggestion_channels = {}

    def load_suggestion_channels():
        nonlocal suggestion_channels
        try:
            with open("suggestion_channels.json", "r") as f:
                suggestion_channels = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            suggestion_channels = {}

    def save_suggestion_channels():
        with open("suggestion_channels.json", "w") as f:
            json.dump(suggestion_channels, f, indent=4)

    load_suggestion_channels()

    @bot.command(name="set_suggestion_channel")
    @commands.has_permissions(administrator=True)
    async def set_suggestion_channel(ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)

        suggestion_channels[guild_id] = channel.id
        save_suggestion_channels()

        await ctx.send(f"✅ Suggestions will now be sent to {channel.mention}.")

    @bot.command(name="suggest")
    async def suggest(ctx):
        guild_id = str(ctx.guild.id)

        if guild_id not in suggestion_channels:
            await ctx.send("❌ The suggestion channel has not been set up yet. Please ask an admin to set it with `!set_suggestion_channel`.")
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print(f"⚠️ Missing permissions to delete message in {ctx.channel.name}")

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send("💡 Please type your suggestion. You have **2 minutes** to respond.")

            message = await bot.wait_for(
                "message",
                timeout=120,
                check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
            )

            suggestion_channel = bot.get_channel(suggestion_channels[guild_id])

            embed = discord.Embed(
                title="📝 New Anonymous Suggestion",
                description=message.content.strip(),
                color=0x8A2BE2
            )
            embed.set_footer(text="Sent anonymously")

            view = View()

            async def accept_callback(interaction):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
                    return

                try:
                    await dm_channel.send("✅ Your suggestion has been **accepted**. Thank you for your input!")
                    await interaction.message.edit(content="✅ This suggestion has been **accepted**.", embed=embed, view=None)
                    await interaction.response.send_message("✅ Suggestion accepted.", ephemeral=True)
                except Exception as e:
                    print(f"⚠️ Error sending DM to {ctx.author}: {e}")

            async def reject_callback(interaction):
                if not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
                    return

                try:
                    await dm_channel.send("❌ Your suggestion has been **rejected**. Thank you for your input!")
                    await interaction.message.edit(content="❌ This suggestion has been **rejected**.", embed=embed, view=None)
                    await interaction.response.send_message("❌ Suggestion rejected.", ephemeral=True)
                except Exception as e:
                    print(f"⚠️ Error sending DM to {ctx.author}: {e}")

            accept_button = Button(label="✅ Accept", style=discord.ButtonStyle.success)
            reject_button = Button(label="❌ Reject", style=discord.ButtonStyle.danger)

            accept_button.callback = accept_callback
            reject_button.callback = reject_callback

            view.add_item(accept_button)
            view.add_item(reject_button)

            await suggestion_channel.send(embed=embed, view=view)
            await dm_channel.send("✅ Your suggestion has been sent anonymously. Thank you for your feedback!")

        except TimeoutError:
            await dm_channel.send("❌ You took too long to respond. Please try again.")

        except Exception as e:
            print(f"⚠️ Error sending DM to {ctx.author}: {e}")

    @bot.command()
    async def pixelhelp(ctx):
        """Paginated help command with navigation"""
        
        class HelpPaginator(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.current_page = 0
                self.pages = [
                    # Page 0 - Guide/Index
                    {
                        "title": "📖 Pixel Command Guide",
                        "description": "**Welcome to Pixel Bot!**\n\nUse the buttons below to navigate through different command categories:\n\n"
                                     "📄 **Page 1** - System Management\n"
                                     "👥 **Page 2** - Profile & Alter Management\n"
                                     "📁 **Page 3** - Folder Management\n"
                                     "🗣️ **Page 4** - Proxy & Autoproxy\n"
                                     "📂 **Page 5** - Import & Export\n"
                                     "🔧 **Page 6** - Admin Commands\n"
                                     "🛠️ **Page 7** - Utility Commands\n\n"
                                     "💡 **Tip:** Commands marked with `(admin only)` require administrator permissions.",
                        "color": 0x8A2BE2
                    },
                    # Page 1 - System Management
                    {
                        "title": "🗃️ System Management Commands",
                        "description": "**System Setup & Configuration:**\n\n"
                                     "`!create_system <name>` - Create a new system\n"
                                     "`!edit_system` - Edit system details (name, avatar, banner, description, pronouns, color, tag)\n"
                                     "`!set_system_tag <tag>` - Set or update your system tag\n"
                                     "`!delete_system` - Delete the current system\n"
                                     "`!system` - Show system info with avatars, banners, and colors\n\n"
                                     "**System Tags:**\nSystem tags appear after alter names when proxying\n"
                                     "Example: `Alter Name | [your tag]`",
                        "color": 0x8A2BE2
                    },
                    # Page 2 - Profile & Alter Management  
                    {
                        "title": "👥 Profile & Alter Management",
                        "description": "**Creating & Managing Alters:**\n\n"
                                     "`!create <name> <pronouns> <description>` - Create new alter with embed support\n"
                                     "`!edit <name>` - Edit alter details (name, displayname, pronouns, description, avatar, banner, proxy, color, role, age, birthday, privacy)\n"
                                     "`!show <name>` - Display alter profile with avatars, banners, and colors\n"
                                     "`!list_profiles` - List all alters in current system\n"
                                     "`!delete <name>` - Delete an alter\n\n"
                                     "**Aliases:**\n"
                                     "`!alias <name> <alias>` - Add alias to alter\n"
                                     "`!remove_alias <name> <alias>` - Remove alias from alter",
                        "color": 0x8A2BE2
                    },
                    # Page 3 - Folder Management
                    {
                        "title": "📁 Folder Management",
                        "description": "**Organize your alters into folders:**\n\n"
                                     "`!create_folder` - Create a new folder with a name, color, banner, icon, and alters\n"
                                     "`!edit_folder <folder name>` - Edit an existing folder\n"
                                     "`!delete_folder <folder name>` - Delete a folder\n"
                                     "`!list_folders` - List all folders in your system\n"
                                     "`!wipe_folder_alters <folder name>` - Remove all alters from a folder\n"
                                     "`!show_folder <folder name>` - Show the contents of a folder\n"
                                     "`!add_alters <folder name> <alter1, alter2>` - Add one or more alters to a folder\n"
                                     "`!remove_alters <folder name> <alter1, alter2>` - Remove one or more alters from a folder",
                        "color": 0x8A2BE2
                    },
                    # Page 4 - Proxy & Autoproxy
                    {
                        "title": "🗣️ Proxy & Autoproxy Commands",
                        "description": "**Proxy Setup:**\n"
                                     "`!set_proxy <name> <proxy>` - Set proxy for alter\n"
                                     "• Simple format: `a:` (requires text after)\n"
                                     "• Advanced format: `a:...;` (text between prefix/suffix)\n"
                                     "`!proxyavatar <name>` - Set separate avatar for proxying\n"
                                     "`!proxy <name> <message>` - Send proxied message manually\n\n"
                                     "**Autoproxy:**\n"
                                     "`!autoproxy latch` - Last proxied alter stays active\n"
                                     "`!autoproxy latch <name>` - Set specific alter to latch\n"
                                     "`!autoproxy front <name>` - Set alter as front\n"
                                     "`!autoproxy unlatch` - Disable autoproxy completely\n"
                                     "`!autoproxy off` - Turn off autoproxy",
                        "color": 0x8A2BE2
                    },
                    # Page 5 - Import & Export
                    {
                        "title": "📂 Import & Export Commands",
                        "description": "**System Data Management:**\n\n"
                                     "`!export_system` - Export entire system to JSON file (sent to DMs)\n"
                                     "`!import_system` - Import previously exported system from JSON file\n\n"
                                     "**PluralKit Integration:**\n"
                                     "`!import_pluralkit` - Import PluralKit system data\n"
                                     "• Imports profiles with proxy avatars and colors\n"
                                     "• Converts groups to folders automatically\n"
                                     "• Preserves system tags and member details\n\n"
                                     "**Note:** Import commands will overwrite existing data. Export first as backup!",
                        "color": 0x8A2BE2
                    },
                    # Page 6 - Admin Commands
                    {
                        "title": "🔧 Admin Commands (Admin Only)",
                        "description": "**Channel & Category Management:**\n\n"
                                     "`!blacklist_channel <channel>` - Blacklist channel from proxy detection\n"
                                     "`!blacklist_category <category>` - Blacklist entire category from proxy detection\n"
                                     "`!list_blacklists` - List all blacklisted channels and categories\n"
                                     "`!admin_commands` - Display all admin commands\n\n"
                                     "**Note:** These commands require administrator permissions in the server.",
                        "color": 0x8A2BE2
                    },
                    # Page 7 - Utility Commands
                    {
                        "title": "🛠️ Utility Commands",
                        "description": "**Bot Information & Help:**\n\n"
                                     "`!pixelhelp` - Show this command list\n"
                                     "**Need help?** Join our support server!",
                        "color": 0x8A2BE2
                    }
                ]

            async def update_message(self, interaction):
                page = self.pages[self.current_page]
                embed = discord.Embed(
                    title=page["title"],
                    description=page["description"],
                    color=page["color"]
                )
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • Use buttons to navigate")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
            async def previous_page(self, interaction, button):
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    self.current_page = len(self.pages) - 1
                await self.update_message(interaction)

            @discord.ui.button(label="Soon", style=discord.ButtonStyle.blurple, emoji="📖")
            async def guide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = 0
                embed = discord.Embed(
                    title=self.pages[self.current_page]["title"],
                    description=self.pages[self.current_page]["description"],
                    color=0x8A2BE2
                )
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction, button):
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                else:
                    self.current_page = 0
                await self.update_message(interaction)

        # Send initial page
        paginator = HelpPaginator()
        page = paginator.pages[0]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=page["color"]
        )
        embed.set_footer(text=f"Page 1/{len(paginator.pages)} • Use buttons to navigate")
        await ctx.send(embed=embed, view=paginator)
