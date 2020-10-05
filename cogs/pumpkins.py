import discord
import tinydb
import random
import time
import os

from discord.ext import commands
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb.table import Document

CHANCE = 150  # 1/150 chance
BONE = "\U0001F9B4"


class Pumpkins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maintenence = 753522913839153163
        self.db = tinydb.TinyDB(
            os.path.join(self.bot.dirname, "cogs/pumpkins.json"),
            storage=CachingMiddleware(JSONStorage),
        )

    # Listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if random.randint(1, CHANCE) == 1:
            try:
                message_table = self.db.table("message_table")

                message_table.insert(
                    Document({"reacted": time.time()}, doc_id=message.id)
                )
                await message.add_reaction(BONE)
            except Exception as e:
                test_chan = message.guild.get_channel(self.maintenence)
                await test_chan.send(e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        pass

    # Commands
    @commands.command()
    @commands.is_owner()
    async def wipe(self, ctx):
        self.db.table("message_table").truncate()
        await ctx.send("Table truncated")

    @commands.command(aliases=("gb",))
    @commands.is_owner()
    async def give_bone(self, ctx, mid: int):
        message = await ctx.message.channel.fetch_message(mid)

        message_table = self.db.table("message_table")
        message_table.insert(Document({"reacted": time.time()}, doc_id=message.id))

        await message.add_reaction(BONE)

    @commands.command()
    async def check_db(self, ctx):
        message_table = self.db.table("message_table")
        await ctx.send(message_table.all())

    # Utils

    # Cogs funcs
    def cog_unload(self):
        self.db.close()


def setup(bot):
    bot.add_cog(Pumpkins(bot))
