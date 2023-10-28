
import discord
from discord.ext import commands
from discord import Embed
from discord import app_commands

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show the available commands")
    async def help(self, interaction:discord.Interaction):
        embed = Embed(title="Help", description="List of commands and their usages:", color=discord.Color.blue())

        # settempchannel command details
        embed.add_field(name="!login <vpsname>", value="Logs in to a VPS and sets that channel state to 'logged in'", inline=False)


        await interaction.response.send_message(embed=embed)