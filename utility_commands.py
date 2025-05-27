
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

    @bot.command(name="pixelhelp")
    async def pixelhelp(ctx):
        embed = discord.Embed(
            title="📂 PixelBot Command List",
            description="Here are all the available commands for managing systems, alters, folders, and more:",
            color=0x8A2BE2
        )

        embed.add_field(
            name="🗃️ **System Management**",
            value=(
                "`!create_system <name>` - Create a new system.\n"
                "`!edit_system` - Edit the current system (name, avatar, banner, description, pronouns, color, tag).\n"
                "`!set_system_tag <tag>` - Set or update your system tag.\n"
                "`!delete_system` - Delete the current system.\n"
                "`!system` - Show the current system's info, including avatars, banners, and colors.\n"
                "`!export_system` - Export your entire system to a JSON file (sent to DMs).\n"
                "`!import_system` - Import a previously exported system from a JSON file."
            ),
            inline=False
        )

        embed.add_field(
            name="👥 **Profile and Alter Management**",
            value=(
                "`!create <name> <pronouns> <description>` - Create a new profile with optional embed support.\n"
                "`!edit <name>` - Edit an existing profile (name, displayname, pronouns, description, avatar, banner, proxy, color, proxy avatar).\n"
                "`!show <name>` - Show a profile, including avatars, banners, and colors.\n"
                "`!list_profiles` - List all profiles in the current system.\n"
                "`!delete <name>` - Delete a profile.\n"
                "`!alias <name> <alias>` - Add an alias to a profile.\n"
                "`!remove_alias <name> <alias>` - Remove an alias from a profile."
            ),
            inline=False
        )

        embed.add_field(
            name="📁 **Folder Management**",
            value=(
                "`!create_folder` - Create a new folder with a name, color, banner, icon, and alters.\n"
                "`!edit_folder <folder name>` - Edit an existing folder.\n"
                "`!delete_folder <folder name>` - Delete a folder.\n"
                "`!wipe_folder_alters <folder name>` - Remove all alters from a folder.\n"
                "`!show_folder <folder name>` - Show the contents of a folder.\n"
                "`!add_alters <folder name> <alter1, alter2>` - Add one or more alters to a folder.\n"
                "`!remove_alters <folder name> <alter1, alter2>` - Remove one or more alters from a folder."
            ),
            inline=False
        )

        embed.add_field(
            name="🗣️ **Proxy Management**",
            value=(
                "`!proxyavatar <name>` - Set a separate avatar for proxying.\n"
                "`!proxy` - Send a proxied message.\n"
                "`!set_proxy <name> <proxy>` - Set a proxy for an alter."
            ),
            inline=False
        )

        embed.add_field(
            name="📂 **Import and Export**",
            value=(
                "`!export_system` - Export your entire system to a JSON file (sent to DMs).\n"
                "`!import_system` - Import a previously exported system from a JSON file.\n"
                "`!import_pluralkit` - Import your PluralKit profiles, including proxy avatars and colors."
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 **Admin Commands**",
            value=(
                "`!blacklist_channel <channel>` - Blacklist a channel from proxy detection (admin only).\n"
                "`!blacklist_category <category>` - Blacklist an entire category from proxy detection (admin only).\n"
                "`!list_blacklists` - List all blacklisted channels and categories (admin only).\n"
                "`!admin_commands` - Display all admin commands (admin only)."
            ),
            inline=False
        )

        embed.add_field(
            name="🛠️ **Utility Commands**",
            value=(
                "`!pixel` - Check the bot's current speed and latency (admin only).\n"
                "`!pixelhelp` - Show the full command list."
            ),
            inline=False
        )

        embed.set_footer(text="PixelBot - The Ultimate Proxy and System Management Bot")

        await ctx.send(embed=embed)
