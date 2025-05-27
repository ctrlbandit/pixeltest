
import discord
from discord.ext import commands
from data_manager import category_blacklist, channel_blacklist, save_category_blacklist, save_blacklist, global_profiles

def setup_admin_commands(bot):
    @bot.command(name="pixel")
    @commands.has_permissions(administrator=True)
    async def pixel(ctx):
        latency = round(bot.latency * 1000)
        embed = discord.Embed(
            title="🌌 PixelBot Status",
            description=f"**Current Latency:** `{latency} ms`",
            color=0x8A2BE2
        )
        await ctx.send(embed=embed)

    @pixel.error
    async def pixel_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need to be a **server admin** to use this command.")

    @bot.command(name="blacklist_category")
    @commands.has_permissions(administrator=True)
    async def blacklist_category(ctx, category: discord.CategoryChannel):
        guild_id = str(ctx.guild.id)

        if guild_id not in category_blacklist:
            category_blacklist[guild_id] = []

        if category.id not in category_blacklist[guild_id]:
            category_blacklist[guild_id].append(category.id)
            save_category_blacklist(category_blacklist)
            await ctx.send(f"🚫 Category **{category.name}** has been blacklisted successfully.")
        else:
            await ctx.send(f"🚫 Category **{category.name}** is already blacklisted.")

    @bot.command(name="unblacklist_category")
    @commands.has_permissions(administrator=True)
    async def unblacklist_category(ctx, category: discord.CategoryChannel):
        guild_id = str(ctx.guild.id)

        if guild_id in category_blacklist and category.id in category_blacklist[guild_id]:
            category_blacklist[guild_id].remove(category.id)
            save_category_blacklist(category_blacklist)
            await ctx.send(f"✅ Category **{category.name}** has been removed from the blacklist.")
        else:
            await ctx.send(f"⚠️ Category **{category.name}** is not blacklisted.")

    @blacklist_category.error
    @unblacklist_category.error
    async def category_blacklist_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need to be a **server admin** to use this command.")

    @bot.command(name="blacklist_channel")
    @commands.has_permissions(administrator=True)
    async def blacklist_channel(ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)

        if guild_id not in channel_blacklist:
            channel_blacklist[guild_id] = []

        if channel.id not in channel_blacklist[guild_id]:
            channel_blacklist[guild_id].append(channel.id)
            save_blacklist(channel_blacklist)
            await ctx.send(f"🚫 Channel **{channel.mention}** has been blacklisted successfully.")
        else:
            await ctx.send(f"🚫 Channel **{channel.mention}** is already blacklisted.")

    @bot.command(name="unblacklist_channel")
    @commands.has_permissions(administrator=True)
    async def unblacklist_channel(ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)

        if guild_id in channel_blacklist and channel.id in channel_blacklist[guild_id]:
            channel_blacklist[guild_id].remove(channel.id)
            save_blacklist(channel_blacklist)
            await ctx.send(f"✅ Channel **{channel.mention}** has been removed from the blacklist.")
        else:
            await ctx.send(f"⚠️ Channel **{channel.mention}** is not blacklisted.")

    @blacklist_channel.error
    @unblacklist_channel.error
    async def blacklist_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need to be a **server admin** to use this command.")

    @bot.command(name="admincommands")
    @commands.has_permissions(administrator=True)
    async def admincommands(ctx):
        embed = discord.Embed(
            title="🔧 Admin Commands",
            description="A list of all available admin-only commands:",
            color=0x8A2BE2
        )

        embed.add_field(
            name="🌌 **Pixel**",
            value="`!pixel` - Check the bot's current latency.",
            inline=False
        )

        embed.add_field(
            name="🛠️ **Admin Commands**",
            value="`!admincommands` - Show a list of all admin commands.",
            inline=False
        )

        embed.add_field(
            name="🚫 **Channel Blacklist**",
            value=(
                "`!blacklist_channel <channel>` - Prevent the bot from reading or sending messages in a channel.\n"
                "`!unblacklist_channel <channel>` - Remove a channel from the bot's blacklist.\n"
                "`!blacklist_category <category>` - Prevent the bot from reading or sending messages in a whole category.\n"
                "`!unblacklist_category <category>` - Remove a category from the bot's blacklist."
            ),
            inline=False
        )

        embed.set_footer(text="Admin commands - Only for server admins")
        await ctx.send(embed=embed)

    @admincommands.error
    async def admincommands_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need to be a **server admin** to use this command.")

    @bot.command(name="bot_stats")
    async def bot_stats(ctx):
        total_systems = len(global_profiles)
        total_guilds = len({guild.id for guild in bot.guilds})

        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="Current stats for the bot:",
            color=0x8A2BE2
        )
        embed.add_field(name="🔄 Total Systems", value=f"{total_systems}", inline=True)
        embed.add_field(name="🏠 Total Guilds", value=f"{total_guilds}", inline=True)
        embed.set_footer(text="PixelBot - Bringing your system to life 🌌")

        await ctx.send(embed=embed)
