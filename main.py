import discord
import os
import toml

from discord.ext import commands

dirname = os.path.dirname(__file__)

conf = toml.load(os.path.join(dirname, "conf.toml"))

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="a:",
    case_insensitive=True,
    help_command=None,
    owner_id=202640363788173313,
    intents=intents,
)

bot.dirname = dirname


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
    except Exception as e:
        if debug:
            await ctx.send(str(e))
        raise (e)


if __name__ == "__main__":
    for cog in conf["cogs"]:
        bot.load_extension(cog)

    bot.run(conf["tokens"]["d_bot"])
