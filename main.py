import discord
import os
import toml
import sys

from discord.ext import commands

DIRNAME = os.path.dirname(__file__)
BOT_LOG = 753522913839153163

conf = toml.load(os.path.join(DIRNAME, "conf.toml"))

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="a:",
    case_insensitive=True,
    help_command=None,
    owner_id=202640363788173313,
    intents=intents,
)

bot.dirname = DIRNAME


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


if __name__ == "__main__":
    if sys.argv.pop() == "-a":
        for cog in conf["cogs"]:
            bot.load_extension(cog)

    bot.run(conf["tokens"]["d_bot"])
