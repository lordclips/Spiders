import discord
import tinydb
import random
import time
import os

from discord.ext import commands
from discord.ext import tasks
from tinydb.middlewares import CachingMiddleware
from tinydb.table import Document
from tinydb import where
from tinydb.operations import add, subtract
from utils.orjson_storage import orjsonStore

CHANCE = 50  # 1/50 chance
BIGCHANCE = 300  # 1/300 chance
BONE = "\U0001F9B4"
BLOCKED_TYPES = [
    discord.MessageType.pins_add,
    discord.MessageType.new_member,
]
BLOCKED_IDS = [
    433899503641165834,
    457003317076426752,
    741801343148097547,
]


class Pumpkins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = tinydb.TinyDB(
            os.path.join(self.bot.dirname, "cogs/pumpkins.json"),
            storage=CachingMiddleware(orjsonStore),
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_table.start()
        self.flush_loop.start()

    # Listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        # Return on literally any of these being true.
        if message.author.bot:
            return
        if message.channel.id in BLOCKED_IDS:
            return
        if message.type in BLOCKED_TYPES:
            return

        # Reusable variables.
        uid = message.author.id

        # Verify user exists.
        await self.verify_user(uid)

        message_table = self.db.table("message_table")

        if random.randint(1, CHANCE) == 1:
            # React with a bone.
            await message.add_reaction(BONE)

            message_table.insert(
                Document({"acted": time.time(), "type": "normal"}, doc_id=message.id)
            )
        elif random.randint(1, BIGCHANCE) == 1:
            # Post wandering skeleton.
            smess = await message.channel.send(
                embed=discord.Embed.from_dict(
                    {
                        "title": "Wandering skeleton encountered!",
                        "description": "12 people must react to get the rewards!",
                        "image": {
                            "url": "http://www.nobodyinlondon.com/wp-content/uploads/2015/05/skeleton-sculpture-investment-2.jpg"
                        },
                    }
                )
            )

            message_table.insert(
                Document({"acted": time.time(), "type": "wandering"}, doc_id=smess.id)
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Ids for convenience
        uid = payload.user_id
        mid = payload.message_id

        # Data models for actual use
        user = self.bot.get_user(uid)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(mid)

        # Tables and documents
        message_table = self.db.table("message_table")
        user_table = self.db.table("user_table")

        # Return on these conditions
        if not payload.emoji.name == BONE:
            return
        if user.bot:
            return
        if not message_table.contains(doc_id=mid):
            return

        doc = message_table.get(doc_id=mid)

        # User verification
        await self.verify_user(uid)

        # Conditionals
        if doc["type"] == "normal":
            # Variable declaration
            udoc = user_table.get(doc_id=uid)
            bones = int(random.randint(5, 10) * min(4, 1.0 + (0.1 * udoc["skeletons"])))

            # Remove message from cache
            message_table.remove(doc_ids=[mid])

            # Update user bone count
            user_table.update(add("bones", bones), doc_ids=[uid])

            await channel.send(f"`{str(user)} has gained {bones} bones!`")

        if doc["type"] == "wandering":
            # Variable declaration
            reaction = [r for r in message.reactions if r.emoji == BONE][0]
            to_send = discord.Embed.from_dict(
                {
                    "title": "Skeleton harvesters!",
                    "description": "The following people have earned 200 bones from participating:\n",
                }
            )

            # Return if there are not enough reactions
            if reaction.count < 12:
                return

            users = await reaction.users().flatten()

            # Iterate over users and add to embed
            for u in users:
                to_send.description += f"{str(u)}\n"

                # Give user 200 bones
                user_table.update(add("bones", 200), doc_ids=[u.id])

            # Remove message from cache
            message_table.remove(doc_ids=[mid])

            await channel.send(embed=to_send)

    # Commands
    @commands.command(aliases=("gb",))
    @commands.is_owner()
    async def give_bone(self, ctx, mid: int):
        message = await ctx.message.channel.fetch_message(mid)

        message_table = self.db.table("message_table")
        message_table.insert(
            Document({"acted": time.time(), "type": "normal"}, doc_id=message.id)
        )

        await message.add_reaction(BONE)

    @commands.command(aliases=("ff",))
    @commands.is_owner()
    async def force_flush(self, ctx):
        self.db.storage.flush()

    @commands.command(aliases=("c",))
    async def collection(self, ctx):
        user_table = self.db.table("user_table")

        uid = ctx.author.id

        await self.verify_user(uid)

        udata = user_table.get(doc_id=uid)
        await ctx.send(
            f"`User inventory`\n"
            f"`Bones:` {udata['bones']}\n"
            f"`Pumpkins:` {udata['pumpkin']}\n"
            f"`Skeletons:` {udata['skeletons']}\n"
            f"`Hearts:` {udata['organs']['heart']}\n"
            f"`Lungs:` {udata['organs']['lungs']}\n"
            f"`Brains:` {udata['organs']['brain']}\n"
            f"`Kidneys:` {udata['organs']['kidneys']}\n"
            f"`Stomachs:` {udata['organs']['stomach']}\n"
            f"`Frankenstein's Monsters:` {udata['fms']}"
        )

    @commands.command(aliases=("cs",))
    async def craft_skeleton(self, ctx):
        user_table = self.db.table("user_table")

        uid = ctx.author.id

        await self.verify_user(uid)

        if user_table.get(doc_id=uid)["bones"] >= 210:
            user_table.update(subtract("bones", 210), doc_ids=[uid])
            user_table.update(add("skeletons", 1), doc_ids=[uid])
            await ctx.send("You have gained a skeleton!")
        else:
            await ctx.send(
                "You do not have enough bones to gain a skeleton. (210 bones required)."
            )

    @commands.command(aliases=("cm",))
    async def craft_monster(self, ctx):
        user_table = self.db.table("user_table")

        uid = ctx.author.id

        await self.verify_user(uid)

        organs = user_table.get(doc_id=uid)["organs"]

        if all(map(lambda n: n >= 5, organs.values())):
            user_table.update(self.dec_dict("organs", 5), doc_ids=[uid])
            user_table.update(add("fms", 1), doc_ids=[uid])
            await ctx.send("You have gained a Frankenstein's Monster!")
        else:
            await ctx.send(
                "You do not have enough organs to gain a Frankenstein's Monster. (5 of each required)."
            )

    @commands.command(aliases=("sp",))
    async def smash_pumpkin(self, ctx):
        user_table = self.db.table("user_table")

        uid = ctx.author.id

        await self.verify_user(uid)

        if user_table.get(doc_id=uid)["pumpkin"]:
            user_table.update(subtract("pumpkin", 1), doc_ids=[uid])

            item = random.choices(
                ["junk", "heart", "lungs", "brain", "kidneys", "stomach"],
                weights=(25, 5, 5, 5, 5, 5),
            )[0]

            if item == "junk":
                await ctx.send("You have earned junk.")
            else:
                user_table.update(self.upd_dict("organs", item, 1), doc_ids=[uid])

                await ctx.send(f"You have earned: {item}")
        else:
            await ctx.send("You do not have any pumpkins to smash.")

    @commands.command(aliases=("bup",))
    async def buy_pumpkin(self, ctx):
        user_table = self.db.table("user_table")

        uid = ctx.author.id

        await self.verify_user(uid)

        if user_table.get(doc_id=uid)["bones"] >= 100:
            user_table.update(subtract("bones", 100), doc_ids=[uid])
            user_table.update(add("pumpkin", 1), doc_ids=[uid])

            await ctx.send("You have bought a pumpkin!")
        else:
            await ctx.send(
                "You do not have enough bones to buy a pumpkin. (100 required)."
            )

    # Utils
    async def verify_user(self, uid):
        user_table = self.db.table("user_table")

        if not user_table.contains(doc_id=uid):
            user_table.insert(Document({"bones": 0, "skeletons": 0}, doc_id=uid))

    def upd_dict(self, field, subfield, amount):
        def transform(doc):
            doc[field][subfield] += amount

        return transform

    def dec_dict(self, field, amount):
        def transform(doc):
            for key in doc[field]:
                doc[field][key] -= amount

        return transform

    # Tasks
    @tasks.loop(minutes=5.0)
    async def check_table(self):
        message_table = self.db.table("message_table")

        # Removing regular bones and wandering skeletons
        # under different criteria.
        # 10 minutes for bones, 30 for wandering skeletons.
        reg_rem = message_table.remove(
            (where("acted") <= (time.time() - 60 * 10)) & (where("type") == "normal")
        )
        wan_rem = message_table.remove(
            (where("acted") <= (time.time() - 60 * 30)) & (where("type") == "wandering")
        )

        if any([bool(reg_rem), bool(wan_rem)]):
            await self.bot.send_log(
                {
                    "title": "Rows removed from bones Database.",
                    "fields": [
                        {"name": "Bones", "value": f"{reg_rem} rows removed."},
                        {"name": "Wandering", "value": f"{wan_rem} rows removed."},
                    ],
                }
            )

    @tasks.loop(minutes=30.0)
    async def flush_loop(self):
        self.db.storage.flush()

        await self.bot.send_log({"title": "Database force flushed."})

    # Cogs funcs
    def cog_unload(self):
        self.db.close()
        self.check_table.cancel()
        self.flush_loop.cancel()


def setup(bot):
    bot.add_cog(Pumpkins(bot))
