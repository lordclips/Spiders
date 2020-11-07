import discord
import os
import toml
import sys

from discord.ext import commands, tasks
from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware

from utils.orjson_storage import orjsonStore

DIRNAME = os.path.dirname(__file__)
BOT_LOG = 753522913839153163

conf = toml.load(os.path.join(DIRNAME, "conf.toml"))

# To be changed later.
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="a:",
    case_insensitive=True,
    help_command=None,
    owner_id=202640363788173313,
    intents=intents,
)

bot.dirname = DIRNAME
bot.database = TinyDB(
    os.path.join(DIRNAME, "db.json"), storage=CachingMiddleware(orjsonStore)
)


async def send_log(data: dict):
    channel_obj = bot.get_channel(BOT_LOG)
    to_send = discord.Embed.from_dict(data)

    await channel_obj.send(embed=to_send)


bot.send_log = send_log


@bot.command(aliases=("e",))
@commands.is_owner()
async def ext(ctx, com: str, name: str, debug: bool = True):
    com = com.lower()

    if not com in (
        "load",
        "unload",
        "reload",
    ):
        await ctx.send(f"Command `{com}` not found.")
        return

    try:
        getattr(bot, f"{com}_extension")(name)
        await ctx.send(f"Extension {name} {com}ed.")
    except Exception as e:
        await ctx.send(f"Failed to {com} {name}.")


@bot.command()
@commands.is_owner()
async def force_flush(ctx):
    bot.database.storage.flush()

    await ctx.send("Database force flushed")


@tasks.loop(minutes=10)
async def flush_database():
    bot.database.storage.flush()


if __name__ == "__main__":
    for cog, data in conf["cogs"].items():
        if data["active_by_default"]:
            bot.load_extension(cog)

    bot.run(conf["tokens"]["d_bot"])
