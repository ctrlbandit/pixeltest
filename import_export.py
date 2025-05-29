"""
import_export.py – PixelBot import/export commands
=================================================

Key points
----------
* **Async‑safe** – every call to `data_manager` is properly awaited and then double‑checked;
  if a coroutine somehow leaks through, we await it once more.
* **Attachment in same message** supported: `!import_system <attach>` or
  `!import_pluralkit <attach>` works alongside the classic prompt flow.
* **Tracebacks** only echo to guild owners/admins for quick debugging without spamming users.
* **Robust colour + UUID/ID handling**; missing/invalid values fall back cleanly.
"""

from __future__ import annotations

import json
import asyncio
import discord
from discord.ext import commands
import aiohttp
import aiofiles
from typing import Any

from data_manager import data_manager  # your DB wrapper

# ────────────────────────── small helpers ─────────────────────────── #

def _pk_colour(value: str | int | None, default: int = 0x8A2BE2) -> int:
    """Convert PluralKit colour strings like "#ff00ff" to int; tolerate garbage."""
    if not value:
        return default
    if isinstance(value, str):
        try:
            return int(value.replace("#", ""), 16)
        except ValueError:
            return default
    return value  # already int


def _is_admin(ctx: commands.Context) -> bool:
    return ctx.guild is None or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.manage_guild


async def _get_profile(uid: str) -> dict[str, Any]:
    """Await `data_manager.get_user_profile` safely even if it double‑wraps a coroutine."""
    profile = await data_manager.get_user_profile(uid)
    if asyncio.iscoroutine(profile):
        # underlying lib returned another coroutine – await it once more
        profile = await profile
    return profile or {}

# ───────────────────────── command setup ──────────────────────────── #

def setup_import_export(bot: commands.Bot) -> None:

    #                        EXPORT SYSTEM                       #
    @bot.command(name="export_system")
    async def export_system(ctx: commands.Context):
        uid = str(ctx.author.id)
        profile = await _get_profile(uid)

        if not profile.get("system", {}).get("name"):
            await ctx.send("❌ You don't have a system set up yet.")
            return

        filename = "pixel export.json"
        try:
            async with aiofiles.open(filename, "w") as f:
                await f.write(json.dumps(profile, indent=4))

            dm = await ctx.author.create_dm()
            await dm.send(
                "📂 Here is your **Pixel** system export file. Keep it safe!",
                file=discord.File(filename),
            )
            await ctx.send("✅ Export completed – check your DMs.")
        except Exception as e:
            print(f"⚠️ export_system failed for {ctx.author}: {e}")
            await ctx.send("❌ Couldn't export your system – please try again.")

    #                        IMPORT PIXEL BACKUP                  #
    @bot.command(name="import_system")
    async def import_system(ctx: commands.Context):
        uid = str(ctx.author.id)

        # attachment may already be present
        if ctx.message.attachments:
            message = ctx.message
        else:
            await ctx.send("📂 Please upload your **PixelBot** system backup JSON file.")
            try:
                message = await bot.wait_for(
                    "message",
                    timeout=300,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments,
                )
            except asyncio.TimeoutError:
                return

        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(message.attachments[0].url) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            data["user_id"] = uid
            await data_manager.save_user_profile(uid, data)
            
            # Count imported items for feedback
            num_alters = len(data.get("alters", {}))
            num_folders = len(data.get("folders", {}))
            
            await ctx.send(
                "✅ **Pixel system import completed!**\n" +
                f"📊 **Imported:** {num_alters} members and {num_folders} folders"
            )
        except Exception as e:
            print(f"⚠️ import_system failed for {ctx.author}: {e}")
            if _is_admin(ctx):
                await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")
            await ctx.send("❌ An error occurred while importing your system.")

    #                        IMPORT PLURALKIT                      #
    @bot.command(name="import_pluralkit")
    async def import_pluralkit(ctx: commands.Context):
        uid = str(ctx.author.id)

        if ctx.message.attachments:
            message = ctx.message
        else:
            await ctx.send("📂 Please upload your **PluralKit** export JSON file.")
            try:
                message = await bot.wait_for(
                    "message",
                    timeout=300,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments,
                )
            except asyncio.TimeoutError:
                return

        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(message.attachments[0].url) as resp:
                    resp.raise_for_status()
                    pk = await resp.json()

            profile = await _get_profile(uid)
            profile.setdefault("system", {})
            profile.setdefault("alters", {})
            profile.setdefault("folders", {})

            # ───── system block ─────
            if pk.get("name"):
                profile["system"] = {
                    "name":        pk.get("name", "Imported System"),
                    "description": pk.get("description", "Imported from PluralKit"),
                    "pronouns":    pk.get("pronouns", "Not set"),
                    "avatar":      pk.get("avatar_url"),
                    "banner":      pk.get("banner"),
                    "color":       _pk_colour(pk.get("color")),
                    "tag":         pk.get("tag"),
                    "created_at":  pk.get("created"),
                    "front_history": [],
                    "system_avatar": pk.get("avatar_url"),
                    "system_banner": pk.get("banner"),
                    "privacy_settings": {
                        "show_front": True,
                        "show_member_count": True,
                        "allow_member_list": True,
                    },
                }

            # ───── member / alter block ─────
            for member in pk.get("members", []):
                name = member.get("name", "Unknown")
                if name in profile["alters"]:
                    continue

                proxy_tags = member.get("proxy_tags", [])
                proxy = "No proxy set"
                if proxy_tags:
                    pre = proxy_tags[0].get("prefix", "")
                    suf = proxy_tags[0].get("suffix", "")
                    if pre and suf:
                        proxy = f"{pre}...{suf}"
                    elif pre:
                        proxy = f"{pre} text"
                    elif suf:
                        proxy = f"text {suf}"

                profile["alters"][name] = {
                    "displayname": member.get("display_name") or name,
                    "pronouns":    member.get("pronouns", "Not set"),
                    "description": member.get("description", "Imported from PluralKit"),
                    "avatar":      member.get("avatar_url"),
                    "proxy_avatar": member.get("avatar_url"),
                    "banner":      member.get("banner"),
                    "proxy":       proxy,
                    "aliases":     [],
                    "color":       _pk_colour(member.get("color")),
                    "use_embed":   True,
                    "created_at":  member.get("created"),
                    "role":        None,
                    "age":         None,
                    "birthday":    member.get("birthday"),
                    "front_time":  0,
                    "last_front":  None,
                    "privacy": {
                        "show_in_list": member.get("visibility", "public") == "public",
                        "allow_proxy":  True,
                    },
                }

            # ───── groups / folders block ─────
            for group in pk.get("groups", []):
                gname = group.get("name", "Unknown Group")
                if gname in profile["folders"]:
                    continue

                profile["folders"][gname] = {
                    "name":        gname,
                    "description": group.get("description", "Imported from PluralKit"),
                    "color":       _pk_colour(group.get("color")),
                    "alters":      [],
                }

                for uuid in group.get("members", []):
                    for m in pk.get("members", []):
                        m_uid = m.get("uuid") or m.get("id")
                        if m_uid == uuid:
                            n = m.get("name")
                            if n and n not in profile["folders"][gname]["alters"]:
                                profile["folders"][gname]["alters"].append(n)

            # ───── save and report ─────
            await data_manager.save_user_profile(uid, profile)
            await ctx.send(
                "✅ **PluralKit import completed!**\n" +
                f"📊 **Imported:** {1 if profile['system'].get('name') else 0} system, "
                f"{len(profile['alters'])} alters, {len(profile['folders'])} folders"
            )

        except Exception as e:
            print(f"⚠️ import_pluralkit failed for {ctx.author}: {e}")
            if _is_admin(ctx):
                await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")
            await ctx.send("❌ An error occurred while importing your PluralKit data.")
