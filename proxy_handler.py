from __future__ import annotations

import io
from typing import Any

import discord
from data_manager import data_manager

# ───────────────────────── debug helper ────────────────────────── #

def _d(tag: str, *vals: Any) -> None:  
    """Print labelled debug output."""
    print(f"[DEBUG] {tag}:", *vals)


# ───────────────────────── setup function ──────────────────────── #

def setup_proxy_handler(bot: discord.Bot) -> None:
    """Register on_message listener for proxying and autoproxy commands."""

    # ============================================================
    # on_message entrypoint
    # ============================================================
    @bot.event
    async def on_message(message: discord.Message):  # noqa: D401
        if message.author.bot:
            return

        _d("MSG", {
            "guild": message.guild.id if message.guild else "DM",
            "author": message.author.id,
            "content": message.content[:80]
        })

        # 1) autoproxy command handling ------------------------------------
        if message.content.startswith("!autoproxy"):
            await _handle_autoproxy_command(message)
            return

        # 2) proxy processing ---------------------------------------------
        proxied = await _process_proxy(message)
        if not proxied:
            await bot.process_commands(message)

    # ============================================================
    # Command: !autoproxy
    # ============================================================
    async def _handle_autoproxy_command(msg: discord.Message) -> None:
        parts = msg.content.split()
        if len(parts) < 2:
            return

        sub = parts[1].lower()
        global_flag = len(parts) >= 3 and parts[-1].lower() == "global"
        scope = "global" if global_flag else "server"
        alter_arg: str | None = None
        if sub == "front" and len(parts) >= 3:
            alter_arg = " ".join(parts[2:-1] if global_flag else parts[2:])

        uid = str(msg.author.id)
        gid = str(msg.guild.id) if msg.guild else None
        if scope == "server" and gid is None:
            await msg.channel.send("⚠️ This command must be used in a server or add `global`.")
            return

        profile = await data_manager.get_user_profile(uid) or {}
        store: dict[str, Any] = profile.get("autoproxy", {})
        key = "global" if scope == "global" else gid
        conf = store.get(key, {"mode": "off", "alter": None, "last_proxied": None})
        alters = profile.get("alters", {})

        if sub in {"off", "unlatch"}:
            if sub == "unlatch" and not global_flag:
                # !autoproxy unlatch (without global) - disable BOTH server and global
                conf.update({"mode": "off", "alter": None})
                store[key] = conf
                
                # Also disable global if it exists
                if "global" in store:
                    global_conf = store["global"]
                    global_conf.update({"mode": "off", "alter": None})
                    store["global"] = global_conf
                    _d("UNLATCH_BOTH", "Disabled both server and global autoproxy")
                else:
                    _d("UNLATCH_SERVER_ONLY", "Disabled server autoproxy (no global config found)")
                
                reply = "🔴 **Autoproxy disabled** (both server and global)."
            else:
                # !autoproxy off or !autoproxy unlatch global - disable only the specified scope
                conf.update({"mode": "off", "alter": None})
                reply = f"🔴 **Autoproxy disabled** ({scope})."
                _d("UNLATCH_SPECIFIC", f"Disabled {scope} autoproxy only")
        elif sub == "front":
            if alter_arg and alter_arg in alters:
                conf.update({"mode": "front", "alter": alter_arg})
                reply = f"🟢 **Autoproxy set to FRONT mode** for **{alter_arg}** ({scope})."
            else:
                await msg.channel.send("❌ **Invalid alter name.**")
                return
        elif sub == "latch":
            conf.update({"mode": "latch", "alter": None})
            reply = f"🟡 **Autoproxy set to LATCH mode** ({scope})."
        else:
            await msg.channel.send("Invalid autoproxy command. Use: `off`, `front <alter>`, `latch`, or `unlatch`.")
            return

        store[key] = conf
        profile["autoproxy"] = store
        await data_manager.save_user_profile(uid, profile)
        await msg.channel.send(reply)
        _d("AUTOPROXY", {key: conf})

    # ============================================================
    # Proxy processing (patterns + autoproxy)
    # ============================================================
    async def _process_proxy(msg: discord.Message) -> bool:
        uid = str(msg.author.id)
        gid = str(msg.guild.id) if msg.guild else None
        is_dm = msg.guild is None

        # ---- blacklist checking --------------------------------------
        if not is_dm and gid:
            # Check if the current channel is blacklisted
            channel_blacklist = await data_manager.get_blacklist("channel", gid)
            if isinstance(channel_blacklist, dict) and str(msg.channel.id) in channel_blacklist:
                _d("BLACKLIST", "Channel blacklisted, skipping proxy")
                return False
            
            # Check if the channel's category is blacklisted
            if hasattr(msg.channel, 'category') and msg.channel.category:
                category_blacklist = await data_manager.get_blacklist("category", gid)
                if isinstance(category_blacklist, dict) and str(msg.channel.category.id) in category_blacklist:
                    _d("BLACKLIST", "Category blacklisted, skipping proxy")
                    return False

        profile = await data_manager.get_user_profile(uid) or {}
        alters = profile.get("alters", {})

        # ---- explicit proxy patterns ------------------------------
        for name, alter_data in alters.items():
            proxy_pattern = alter_data.get("proxy")
            if not proxy_pattern or proxy_pattern == "No proxy set":
                continue

            content_hit: str | None = None
            
            # 1) prefix...suffix style
            if "..." in proxy_pattern:
                pre, suf = proxy_pattern.split("...", 1)
                if msg.content.startswith(pre) and msg.content.endswith(suf):
                    content_hit = msg.content[len(pre):-len(suf)] if suf else msg.content[len(pre):]

            # 2) prefix text style
            elif proxy_pattern.endswith(" text"):
                prefix = proxy_pattern[:-5]
                if msg.content.startswith(prefix):
                    content_hit = msg.content[len(prefix):]

            # 3) prefix style
            else:
                if msg.content.startswith(proxy_pattern):
                    content_hit = msg.content[len(proxy_pattern):]

            # Check if have a pattern match
            if content_hit is not None:
                content_hit = content_hit.strip()
                _d("PROXY_MATCH", {
                    "pattern": proxy_pattern,
                    "alter": name,
                    "content": content_hit,
                    "attachments": len(msg.attachments)
                })
                
                # Process if have content OR attachments
                if content_hit or msg.attachments:
                    if is_dm:
                        await msg.channel.send("I cannot proxy in DMs. Please head to a server.")
                        return True
                    
                    # Update global latch if active
                    autoproxy_store = profile.get("autoproxy", {})
                    if "global" in autoproxy_store and autoproxy_store["global"].get("mode") == "latch":
                        autoproxy_store["global"]["last_proxied"] = name
                        profile["autoproxy"] = autoproxy_store
                        await data_manager.save_user_profile(uid, profile)
                        _d("GLOBAL_LATCH_UPDATE", f"Updated global latch to {name}")
                    
                    return await _proxy_send(msg, name, content_hit, alter_data)

        # ---- autoproxy front / latch ------------------------------
        store: dict[str, Any] = profile.get("autoproxy", {})
        auto: dict[str, Any] | None = None
        key: str | None = None
        
        # 1. Check server config first if it exists and is active
        if gid and gid in store and store[gid].get("mode") != "off":
            auto = store[gid]
            key = gid
        # 2. Check global config if server config doesn't exist or is inactive
        elif "global" in store and store["global"].get("mode") != "off":
            auto = store["global"]
            key = "global"
        # 3. Fall back to inactive server config if it exists
        elif gid and gid in store:
            auto = store[gid]
            key = gid

        _d("AUTOPROXY_CHECK", {
            "gid": gid,
            "has_server_config": gid in store if gid else False,
            "has_global_config": "global" in store,
            "selected_key": key,
            "auto_config": auto,
            "store_keys": list(store.keys())
        })

        if not auto or auto["mode"] == "off":
            _d("AUTOPROXY_SKIP", "No autoproxy config or mode is off")
            return False

        target: str | None = None
        if auto["mode"] == "front" and auto.get("alter"):
            target = auto["alter"]
        elif auto["mode"] == "latch" and auto.get("last_proxied"):
            target = auto["last_proxied"]

        _d("AUTOPROXY_TARGET", {
            "mode": auto["mode"],
            "target": target,
            "last_proxied": auto.get("last_proxied"),
            "available_alters": list(alters.keys())
        })

        if target and target in alters:
            if is_dm:
                await msg.channel.send("I cannot proxy in DMs. Please head to a server.")
                return True
            
            # Update last_proxied for latch mode
            if auto["mode"] == "latch":
                auto["last_proxied"] = target
                store[key] = auto
                profile["autoproxy"] = store
                await data_manager.save_user_profile(uid, profile)
            
            return await _proxy_send(msg, target, msg.content, alters[target])

        _d("AUTOPROXY_NO_TARGET", "No valid target found")
        return False

    # ============================================================
    # Low‑level send via webhook
    # ============================================================
    async def _proxy_send(msg: discord.Message, alter: str, content: str, data: dict[str, Any]) -> bool:
        uid = str(msg.author.id)

        _d("PROXY_SEND", {
            "alter": alter,
            "content": content,
            "attachments": len(msg.attachments),
            "attachment_names": [att.filename for att in msg.attachments]
        })

        # 1) Download attachments before deleting
        files: list[discord.File] = []
        for att in msg.attachments:
            try:
                buf = await att.read()
                files.append(discord.File(io.BytesIO(buf), filename=att.filename))
                _d("ATTACH_DOWNLOAD", f"Successfully downloaded {att.filename}")
            except Exception as e:
                _d("ATTACH_ERR", e)
                content += f"\n[Attachment: {att.filename}]({att.url})"

        # 2) Delete original message
        try:
            await msg.delete()
        except discord.Forbidden:
            await msg.channel.send("⚠️ Need 'Manage Messages' permission to proxy.")
            return False
        except discord.NotFound:
            pass

        # 3) Compose display / avatar
        profile = await data_manager.get_user_profile(uid) or {}
        tag = profile.get("system", {}).get("tag")
        display = data.get("displayname", alter) + (f" {tag}" if tag else "")
        avatar = data.get("proxy_avatar") or data.get("avatar")

        # 4) Send via webhook
        try:
            wh = next((w for w in await msg.channel.webhooks() if w.name == "Pixel Proxy"), None)
            if not wh:
                wh = await msg.channel.create_webhook(name="Pixel Proxy")
            await wh.send(content=content if content.strip() else None, username=display, avatar_url=avatar, files=files)
            _d("PROXY", display, "→", content[:60])
        except discord.Forbidden:
            await msg.channel.send(f"⚠️ Can't create webhooks. Proxy message from {display}: {content}")
            return True
        except Exception as e:
            _d("WEBHOOK_ERR", e)
            return False

        # 5) Update last_proxied if latch is active
        ap = profile.get("autoproxy", {})
        gid = str(msg.guild.id) if msg.guild else None
        key = gid if gid and gid in ap else "global"
        if key in ap and ap[key]["mode"] == "latch":
            ap[key]["last_proxied"] = alter
            profile["autoproxy"] = ap
            await data_manager.save_user_profile(uid, profile)
        return True
