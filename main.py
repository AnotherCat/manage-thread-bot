import asyncio
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import tasks
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import Context
from tortoise import Tortoise

from config import POLL_ROLE_PING, THREAD_INACTIVE_HOURS, token, ADD_USER_IDS
from tortoise_config import TORTOISE_ORM

logging.basicConfig(level=logging.INFO)


THREAD_INACTIVE_TIME = 60 * 60 * THREAD_INACTIVE_HOURS


from models import Guild, Thread


class Bot(BotBase):
    async def init_db(self) -> None:
        await Tortoise.init(config=TORTOISE_ORM)

    async def start(self, *args, **kwargs) -> None:  # type: ignore
        await self.init_db()
        await super().start(*args, **kwargs)

    async def close(self) -> None:
        await Tortoise.close_connections()
        await super().close()


bot = Bot(command_prefix="!")


@bot.command(name="keep-alive")
async def keep_alive(ctx: Context):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❗This channel is not a thread!")
        return
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send('❗You do not have the required permissions, "ADMINISTRATOR"')
        return
    guild = (await Guild.get_or_create(id=ctx.guild.id))[0]
    thread = (
        await Thread.get_or_create(id=ctx.channel.id, defaults={"guild_id": guild.id})
    )[0]
    if thread.keep_alive:
        await ctx.send(
            "❗Keep Alive already started for this thread, use `!stop-keep-alive` to stop."
        )
    else:
        thread.keep_alive = True
        await thread.save()
        await ctx.send("Keep Alive started!")


@bot.command(name="stop-keep-alive")
async def keep_alive(ctx: Context):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❗This channel is not a thread!")
        return
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send('❗You do not have the required permissions, "ADMINISTRATOR"')
        return
    guild = (await Guild.get_or_create(id=ctx.guild.id))[0]
    thread = (
        await Thread.get_or_create(id=ctx.channel.id, defaults={"guild_id": guild.id})
    )[0]
    if not thread.keep_alive:
        await ctx.send(
            "❗Keep Alive has not been started for this thread, use `!keep-alive` to start."
        )
    else:
        thread.keep_alive = False
        await thread.save()
        await ctx.send("Keep Alive stopped!")


@bot.command(name="start-poll")
async def keep_alive(ctx: Context):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❗This channel is not a thread!")
        return
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send('❗You do not have the required permissions, "ADMINISTRATOR"')
        return
    guild = (await Guild.get_or_create(id=ctx.guild.id))[0]
    thread = (
        await Thread.get_or_create(id=ctx.channel.id, defaults={"guild_id": guild.id})
    )[0]
    if thread.waiting_on_poll:
        await ctx.send(
            "❗Poll already started for this thread, use `!stop-poll` to stop."
        )
    else:
        thread.keep_alive = True
        thread.waiting_on_poll = True
        await thread.save()
        await ctx.send(
            f"The poll will be started after {THREAD_INACTIVE_HOURS} hours of inactivity."
        )


@bot.command(name="stop-poll")
async def keep_alive(ctx: Context):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❗This channel is not a thread!")
        return
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send('❗You do not have the required permissions, "ADMINISTRATOR"')
        return
    guild = (await Guild.get_or_create(id=ctx.guild.id))[0]
    thread = (
        await Thread.get_or_create(id=ctx.channel.id, defaults={"guild_id": guild.id})
    )[0]
    if not thread.waiting_on_poll:
        await ctx.send(
            "❗Poll has not been started for this thread, use `!start-poll` to start."
        )
    else:
        thread.keep_alive = True
        thread.waiting_on_poll = False
        await thread.save()
        await ctx.send(
            'Poll stopped! Please note "Keep Alive" is still on, use `!stop-keep-alive` to stop'
        )


async def check_archive(
    before: discord.Thread, after: discord.Thread, thread_settings: Thread
) -> bool:
    if not after.permissions_for(after.guild.me).manage_threads:
        return
    if not before.archived and after.archived:
        if thread_settings is not None:
            if thread_settings.keep_alive:
                await after.edit(archived=False, locked=False)


async def check_activity(thread: discord.Thread, thread_settings: Thread) -> bool:
    if not thread_settings.waiting_on_poll:
        return False
    last_message_time = discord.utils.snowflake_time(thread.id)
    current_time = datetime.now(tz=timezone.utc)
    if last_message_time < current_time - timedelta(seconds=THREAD_INACTIVE_TIME):
        thread_settings.waiting_on_poll = False
        await thread_settings.save()
        msg = await thread.send(
            f"There has been no activity on this thread for {THREAD_INACTIVE_HOURS} hours "
            f"<@&{POLL_ROLE_PING}>\n"
            if POLL_ROLE_PING
            else ""
            f'Starting a poll. Please note "Keep Alive" is still on use `!stop-keep-alive` to stop.'
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        return True
    return False


@bot.event
async def on_thread_update(before: discord.Thread, after: discord.Thread) -> None:
    thread_settings = await Thread.get_or_none(id=after.id)
    if thread_settings is None:
        return
    await check_archive(before, after, thread_settings)


@bot.event
async def on_thread_join(thread: discord.Thread) -> None:
    if len(ADD_USER_IDS) < 1:
        return
    for user_id in ADD_USER_IDS:
        if user_id == thread.owner_id:
            continue
        await thread.add_user(discord.Object(user_id))
        await asyncio.sleep(5)

    await thread.add_user(bot.user)


@tasks.loop(hours=1)
async def check_activity_task():
    guilds = await Guild.all()
    for guild in guilds:
        async for thread in guild.threads:
            bot_guild = bot.get_guild(guild.id)
            thread_channel = bot_guild.get_thread(thread.id)
            await check_activity(thread_channel, thread)


@tasks.loop(hours=12)
async def check_archive_task():
    guilds = await Guild.all()
    for guild in guilds:
        async for thread in guild.threads:
            bot_guild = bot.get_guild(guild.id)
            thread_channel = bot_guild.get_thread(thread.id)
            await check_archive(thread_channel, thread)


bot.startup = True


@bot.event
async def on_ready():
    if bot.startup:
        bot.startup = False
        check_activity_task.start()
        check_archive_task.start()


bot.run(token)
