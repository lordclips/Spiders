import discord
import json
import time
import os

from discord.ext import commands

WEEK = 604800


class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subjects = {}
        self._checkrole_id = 458374484244693005
        self._tracker_chan_id = 755624749824082050

        with open(os.path.join(self.bot.dirname, "cogs/tracker.json"), "r") as js:
            self.subjects = json.load(js)

    # Check
    """
    def bot_check(self, ctx):
        role = ctx.guild.get_role(self._checkrole_id)
        return role in ctx.author.roles
    """

    # Listeners
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.author.id) in self.subjects.keys():
            user = message.author
            trackchan = message.guild.get_channel(self._tracker_chan_id)

            await trackchan.send(
                embed=discord.Embed().from_dict(
                    {
                        "title": f"Message from {str(user)}",
                        "url": message.jump_url,
                        "description": f"> {message.content}",
                        "footer": {"text": f"{message.id} | {message.created_at}"},
                        "author": {
                            "name": f"{str(user)}",
                            "icon_url": str(user.avatar_url),
                        },
                    }
                )
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        created = member.created_at

        if member.bot:
            return

        if (time.time() - created.timestamp()) < WEEK:
            trackchan = member.guild.get_channel(self._tracker_chan_id)

            await trackchan.send(
                embed=discord.Embed().from_dict(
                    {
                        "title": f"New account {str(member)} (under 7 days old).",
                        "description": f"Account made on {created}",
                        "footer": {
                            "text": f"{member.id}",
                        },
                    }
                )
            )

    # Commands
    @commands.command(aliases=("tl",))
    @commands.is_owner()
    async def tracklist(self, ctx):
        await ctx.send(
            embed=discord.Embed().from_dict(
                {
                    "title": "Tracked users list.",
                    "description": "\n".join(
                        [f"`{x}` : {y}" for x, y in self.subjects.items()]
                    ),
                }
            )
        )

    @commands.command(aliases=("ta",))
    @commands.is_owner()
    async def trackadd(self, ctx, uid: int):
        try:
            tag = str(ctx.guild.get_member(uid))
        except:
            await ctx.send("User could not be found.")

        if uid not in self.subjects.keys():
            self.subjects.update({str(uid): tag})

            await ctx.send(f"Track list updated. Added user `{uid}` ({tag})")
        else:
            await ctx.send("User could not be added.")

        self._update()

    @commands.command(aliases=("td",))
    @commands.is_owner()
    async def trackdel(self, ctx, uid: int):
        uid = str(uid)
        tag = self.subjects[uid]

        if uid in self.subjects.keys():
            self.subjects.pop(uid)

            await ctx.send(f"Track list updated. Removed user `{uid}` ({tag})")
        else:
            await ctx.send("User could not be removed.")

        self._update()

    @commands.command()
    @commands.is_owner()
    async def trackdebug(self, ctx):
        await ctx.send(
            embed=discord.Embed().from_dict(
                {
                    "title": "Tracker debug",
                    "description": str(self.subjects),
                }
            )
        )

    # Util
    def _update(self):
        with open(os.path.join(self.bot.dirname, "cogs/tracker.json"), "w") as js:
            json.dump(self.subjects, js)


def setup(bot):
    bot.add_cog(Tracker(bot))
