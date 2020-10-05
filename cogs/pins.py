import discord
import json
import time
import os

from discord.ext import commands
from discord.ext import tasks

PIN_EMOTE = "\U0001F4CC"
THRESHOLD = 5
THREE_DAYS = 259200


class Pins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pins = {}
        self._checkrole_id = 458374484244693005

        self.time_checker.start()

        with open(os.join.path(self.bot.dirname, "cogs/pins.json"), "r") as js:
            self.pins = json.load(js)

    # Checks
    def bot_check(self, ctx):
        role = ctx.guild.get_role(self._checkrole_id)
        return role in ctx.author.roles

    # Listeners
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        channel = message.channel

        if str(message.id) in self.pins["blacklisted"].keys():
            return

        if reaction.emoji == PIN_EMOTE:
            pins = self.pins["pins"]
            votes = reaction.count
            strid = str(message.id)

            users = [x.id for x in await reaction.users().flatten()]

            if self.bot.owner_id in users:
                votes += 5

            if votes >= THRESHOLD:
                pin_list = await channel.pins()

                if message not in pin_list:
                    if len(pin_list) == 50:
                        bot_pinned = [
                            (x, pins[x]["votes"])
                            for x in set(str(x.id) for x in pin_list) & set(pins.keys())
                        ]
                        if bot_pinned:
                            filt = lambda x: x[1] < votes
                            removeable = list(filter(filt, bot_pinned))

                            if removeable:
                                unpin = None

                                if len(removeable) == 1:
                                    unpin = removeable[0][0]
                                else:
                                    unpin = min([x[0] for x in removeable])

                                await channel.fetch_message(unpin).unpin()
                                await message.pin(reason="Beat old pin")

                                del pins[str(unpin)]
                    else:
                        await message.pin(reason="Meets emote threshold")

                if not (strid in pins.keys()):
                    pins.update(
                        {
                            strid: {
                                "status": "active",
                                "votes": votes,
                                "start": time.time(),
                            }
                        }
                    )

                if votes > pins[strid]["votes"]:
                    if pins[strid]["status"] == "active":
                        pins[strid]["votes"] = votes

            await self._update()

    # Commands
    @commands.command(aliases=("bp",))
    async def blacklist_pin(self, ctx, mid: int):
        strid = str(mid)

        if strid not in self.pins["blacklisted"].keys():
            self.pins["blacklisted"].update({strid: time.time()})

            message = await ctx.fetch_message(mid)

            if message.pinned:
                await message.unpin(reason="blacklisted")
                del self.pins["pins"][strid]

            await ctx.send("Message blacklisted")
            await self._update()

    # Util
    async def _update(self):
        with open(os.path.join(self.bot.dirname, "cogs/pins.json"), "w") as js:
            json.dump(self.pins, js)

    # Tasks
    @tasks.loop(minutes=30.0)
    async def time_checker(self):
        user = self.bot.get_user(self.bot.owner_id)
        await user.send("Time checker done.")

        for mid, data in self.pins["pins"].items():
            if time.time() - data["start"] >= THREE_DAYS:
                self.pins["pins"][mid]["status"] = "inactive"

        for mid, time in self.pins["blacklisted"].items():
            if time.time() - time >= THREE_DAYS:
                del self.pins["blacklisted"][mid]

        await self._update()

    # Cog funcs
    def cog_unload(self):
        self.time_checker.cancel()


def setup(bot):
    bot.add_cog(Pins(bot))
