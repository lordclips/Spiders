import discord
import datetime
import uuid

from discord.ext import commands, tasks
from cryptography.fernet import Fernet
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from tinydb.table import Document


# Checks


def dm_check():
    async def predicate(ctx):
        return ctx.message.channel.type == discord.ChannelType.private

    return commands.check(predicate)


def channel_check():
    async def predicate(ctx):
        return ctx.message.channel.id == 774279927893590036

    return commands.check(predicate)


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_db = TinyDB(storage=MemoryStorage)
        self.report_channel_id = 774279927893590036
        self.public_notif = 433896504671862784

    # Commands

    @commands.command()
    @channel_check()
    async def reverse_report(self, ctx, report_id: int, *, reason: str):
        if not self.report_db.get(doc_id=report_id):
            await ctx.send("Report ID does not exist.")
            return

        await ctx.send(
            "Due to the nature of this cog, acknowledgement is required before fully reversing an anonymous report.\n\n"
            "Please type `acknowledge` to acknowledge that reversing this report will notify others that the anonymity of "
            "the report has been broken, and that they will be provided the reasoning in a public manner to hold us "
            "accountable were privacy to be unreasonably broken."
        )

        def predicate(message):
            return (
                message.author == ctx.author
                and message.content.lower() == "acknowledge"
            )

        try:
            message = await self.bot.wait_for("message", check=predicate, timeout=10.0)
        except:
            await ctx.send("Failed to properly acknowledge. Cancelling reversal.")
            return

        doc = list(self.report_db.get(doc_id=report_id).items())[0]

        info = doc[0].encode("utf-8")
        key = doc[1].encode("utf-8")

        fernet = Fernet(key)
        decrypted_info = fernet.decrypt(info)

        await ctx.send(f"`{str(decrypted_info)}`")

        channel = self.bot.get_channel(self.public_notif)

        await channel.send(
            f"Anonymous report has been reverted for the following reason: `{reason}`"
        )

    @commands.command(aliases=("r",))
    @dm_check()
    async def report(self, ctx, *, content: str):
        information = f"{ctx.author.id}:{ctx.message.id}"
        channel = self.bot.get_channel(self.report_channel_id)
        report_id = uuid.uuid4().int
        report_content = content

        await ctx.send("Report received. It is recommended you delete the message.")

        key = Fernet.generate_key()
        fernet = Fernet(key)

        encrypted_id = fernet.encrypt(bytes(information, "utf-8"))

        self.report_db.insert(
            Document(
                {encrypted_id.decode("utf-8"): key.decode("utf-8")}, doc_id=report_id
            )
        )

        await channel.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Anonymous report",
                    "description": f"ID: {report_id}",
                    "fields": [{"name": "Content", "value": report_content}],
                }
            )
        )

    # Tasks

    @tasks.loop(hours=6)
    async def clear_in_memory_data(self):
        self.report_db.truncate()


def setup(bot):
    bot.add_cog(Reports(bot))
