
import discord
from discord.ext import commands
from discord import Embed

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = Embed(title="Help", description="List of commands and their usages:", color=discord.Color.blue())

        # settempchannel command details
        embed.add_field(name="!login <vpsname>", value="Logs in to a VPS and sets that channel state to 'logged in'", inline=False)


        await ctx.send(embed=embed)