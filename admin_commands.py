import discord
from discord.ext import commands
from data_manager import data_manager

def setup_admin_commands(bot):
    @bot.command(name="pixel")
    @commands.has_permissions(administrator=True)
    async def pixel(ctx):
        # Calculate latencies
        latency = round(bot.latency * 1000)
        
        # Get database connection status
        try:
            db_status = "🟢 Connected" if data_manager.profiles_collection is not None else "🔴 Disconnected"
        except:
            db_status = "🔴 Disconnected"
        
        # Calculate total users across all servers
        total_users = sum(guild.member_count for guild in bot.guilds if guild.member_count)
        total_guilds = len(bot.guilds)
        
        embed = discord.Embed(
            title="🌌 PixelBot Status Dashboard",
            description="Bot statistics and health information",
            color=0x8A2BE2
        )
        
        # Connection & Performance
        embed.add_field(
            name="🔗 **Connection Status**",
            value=(
                f"**Database:** {db_status}\n"
                f"**Discord Latency:** `{latency} ms`\n"
                f"**WebSocket Latency:** `{round(bot.latency * 1000)} ms`"
            ),
            inline=True
        )
        
        # Server Statistics
        embed.add_field(
            name="🏠 **Server Statistics**",
            value=(
                f"**Total Servers:** `{total_guilds:,}`\n"
                f"**Total Users:** `{total_users:,}`\n"
                f"**Average Users/Server:** `{round(total_users/total_guilds) if total_guilds > 0 else 0}`"
            ),
            inline=True
        )
        
        embed.set_footer(text=f"PixelBot v2.0 • Running on {total_guilds} servers")
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    @pixel.error
    async def pixel_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need to be a **server admin** to use this command.")

    @bot.command(name="blacklist_channel")
    @commands.has_permissions(administrator=True)
    async def blacklist_channel(ctx, channel: discord.TextChannel):
        """Blacklist a channel from proxy functionality"""
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        # Get current blacklist
        current_blacklist = await data_manager.get_blacklist("channel", guild_id)
        if not isinstance(current_blacklist, list):
            current_blacklist = []
        
        if channel_id not in current_blacklist:
            current_blacklist.append(channel_id)
            success = await data_manager.save_blacklist("channel", guild_id, current_blacklist)
            
            if success:
                embed = discord.Embed(
                    title="✅ Channel Blacklisted",
                    description=f"Channel {channel.mention} has been blacklisted from proxy functionality.",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to save blacklist. Please try again.")
        else:
            embed = discord.Embed(
                title="⚠️ Already Blacklisted",
                description=f"Channel {channel.mention} is already blacklisted.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)

    @bot.command(name="blacklist_category")
    @commands.has_permissions(administrator=True)
    async def blacklist_category(ctx, category: discord.CategoryChannel):
        """Blacklist a category from proxy functionality"""
        guild_id = str(ctx.guild.id)
        category_id = str(category.id)
        
        # Get current blacklist
        current_blacklist = await data_manager.get_blacklist("category", guild_id)
        if not isinstance(current_blacklist, list):
            current_blacklist = []
        
        if category_id not in current_blacklist:
            current_blacklist.append(category_id)
            success = await data_manager.save_blacklist("category", guild_id, current_blacklist)
            
            if success:
                embed = discord.Embed(
                    title="✅ Category Blacklisted",
                    description=f"Category **{category.name}** has been blacklisted from proxy functionality.",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to save blacklist. Please try again.")
        else:
            embed = discord.Embed(
                title="⚠️ Already Blacklisted",
                description=f"Category **{category.name}** is already blacklisted.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)

    @bot.command(name="unblacklist_channel")
    @commands.has_permissions(administrator=True)
    async def unblacklist_channel(ctx, channel: discord.TextChannel):
        """Remove a channel from the blacklist"""
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        
        # Get current blacklist
        current_blacklist = await data_manager.get_blacklist("channel", guild_id)
        if not isinstance(current_blacklist, list):
            current_blacklist = []
        
        if channel_id in current_blacklist:
            current_blacklist.remove(channel_id)
            success = await data_manager.save_blacklist("channel", guild_id, current_blacklist)
            
            if success:
                embed = discord.Embed(
                    title="✅ Channel Unblacklisted",
                    description=f"Channel {channel.mention} has been removed from the blacklist.",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to save blacklist. Please try again.")
        else:
            embed = discord.Embed(
                title="⚠️ Not Blacklisted",
                description=f"Channel {channel.mention} is not currently blacklisted.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)

    @bot.command(name="unblacklist_category")
    @commands.has_permissions(administrator=True)
    async def unblacklist_category(ctx, category: discord.CategoryChannel):
        """Remove a category from the blacklist"""
        guild_id = str(ctx.guild.id)
        category_id = str(category.id)
        
        # Get current blacklist
        current_blacklist = await data_manager.get_blacklist("category", guild_id)
        if not isinstance(current_blacklist, list):
            current_blacklist = []
        
        if category_id in current_blacklist:
            current_blacklist.remove(category_id)
            success = await data_manager.save_blacklist("category", guild_id, current_blacklist)
            
            if success:
                embed = discord.Embed(
                    title="✅ Category Unblacklisted",
                    description=f"Category **{category.name}** has been removed from the blacklist.",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to save blacklist. Please try again.")
        else:
            embed = discord.Embed(
                title="⚠️ Not Blacklisted",
                description=f"Category **{category.name}** is not currently blacklisted.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)

    @bot.command(name="list_blacklists")
    @commands.has_permissions(administrator=True)
    async def list_blacklists(ctx):
        """List all blacklisted channels and categories for this server"""
        guild_id = str(ctx.guild.id)
        
        embed = discord.Embed(
            title="🚫 Server Blacklists",
            description="Channels and categories where proxy functionality is disabled",
            color=0xff0000
        )
        
        # Get blacklisted channels
        channel_blacklist = await data_manager.get_blacklist("channel", guild_id)
        if not isinstance(channel_blacklist, list):
            channel_blacklist = []
            
        blacklisted_channels = []
        for channel_id in channel_blacklist:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                blacklisted_channels.append(channel.mention)
            else:
                blacklisted_channels.append(f"Unknown Channel (ID: {channel_id})")
        
        # Get blacklisted categories
        category_blacklist = await data_manager.get_blacklist("category", guild_id)
        if not isinstance(category_blacklist, list):
            category_blacklist = []
            
        blacklisted_categories = []
        for category_id in category_blacklist:
            category = ctx.guild.get_channel(int(category_id))
            if category:
                blacklisted_categories.append(f"**{category.name}**")
            else:
                blacklisted_categories.append(f"Unknown Category (ID: {category_id})")
        
        # Add fields to embed
        if blacklisted_channels:
            embed.add_field(
                name="📝 Blacklisted Channels",
                value="\n".join(blacklisted_channels),
                inline=False
            )
        else:
            embed.add_field(
                name="📝 Blacklisted Channels",
                value="*No channels blacklisted*",
                inline=False
            )
        
        if blacklisted_categories:
            embed.add_field(
                name="📁 Blacklisted Categories",
                value="\n".join(blacklisted_categories),
                inline=False
            )
        else:
            embed.add_field(
                name="📁 Blacklisted Categories",
                value="*No categories blacklisted*",
                inline=False
            )
        
        embed.set_footer(text="Use !unblacklist_channel or !unblacklist_category to remove items")
        await ctx.send(embed=embed)

    @bot.command(name="admin_commands")
    @commands.has_permissions(administrator=True)
    async def admin_commands(ctx):
        """Display all available admin commands"""
        embed = discord.Embed(
            title="🛠️ Admin Commands",
            description="Available administrator commands for PixelBot",
            color=0x8A2BE2
        )
        
        embed.add_field(
            name="📊 **Bot Management**",
            value=(
                "`!admin_commands` - Show this help menu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🚫 **Blacklist Management**",
            value=(
                "`!blacklist_channel <channel>` - Blacklist a channel\n"
                "`!blacklist_category <category>` - Blacklist a category\n"
                "`!unblacklist_channel <channel>` - Remove channel from blacklist\n"
                "`!unblacklist_category <category>` - Remove category from blacklist\n"
                "`!list_blacklists` - View all blacklisted channels/categories"
            ),
            inline=False
        )
        
        embed.set_footer(text="All commands require Administrator permissions")
        await ctx.send(embed=embed)

    # Error handlers for the new commands
    @blacklist_channel.error
    async def blacklist_channel_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Please mention a valid text channel. Usage: `!blacklist_channel #channel`")

    @blacklist_category.error
    async def blacklist_category_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Please specify a valid category. Usage: `!blacklist_category Category Name`")

    @unblacklist_channel.error
    async def unblacklist_channel_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Please mention a valid text channel. Usage: `!unblacklist_channel #channel`")

    @unblacklist_category.error
    async def unblacklist_category_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Please specify a valid category. Usage: `!unblacklist_category Category Name`")

    @list_blacklists.error
    async def list_blacklists_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.")

    @admin_commands.error
    async def admin_commands_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need **Administrator** permissions to use this command.") 