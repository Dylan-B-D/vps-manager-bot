# Standard Libraries
import os
import configparser

# Third-party Libraries
import discord
from discord.ext import commands
from discord import app_commands

# Local Modules
from utils.vps_utils import (establish_ssh_connection, 
                             send_response_embed, 
                             edit_response_embed, 
                             handle_connection_error,
                             fetch_vps_stats,
                             process_vps_stats)
from utils.data_utils import get_login_state

# Directory constants
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE_DIR = os.path.join(BASE_DIR, 'cache', 'gamequeue')

# ---- DIRECTORY SETUP ---- #
# Create directories if they don't exist
for directory in [CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.vpses = self.load_vps_configs()

    def load_vps_configs(self):
        vpses = {}
        for section in self.config.sections():
            if section != "Bot":  # Exclude the Bot section
                vpses[section] = {
                    'IP': self.config[section]['IP'],
                    'Username': self.config[section]['Username'],
                    'Password': self.config[section]['Password']
                }
        return vpses

    @app_commands.command(name="vpsresources", description="Check the resource usages of the logged-in VPS")
    async def slash_vps_resources(self, interaction:discord.Interaction):
        """Command to check the resource usages of the logged-in VPS."""
        server_id = interaction.guild.id
        channel_id = interaction.channel.id
        string_key = f"{server_id}_{channel_id}"
        vps_name = get_login_state(server_id, channel_id, os.path.join(CACHE_DIR, 'login_states.bson'))

        if not vps_name:
            embed = discord.Embed(title="", description="No VPS is currently logged in for this channel.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        await send_response_embed(interaction, f"VPS Resources - {vps_name}", "Establishing connection... Please wait...", discord.Color.blue())
        vps = self.vpses[vps_name]

        conn = await establish_ssh_connection(vps)
        try:
            async with conn:
                stats = await fetch_vps_stats(conn)
                mem_usage, disk_usage, cpu_usage, top_processes = await process_vps_stats(stats, conn)

                # Creating Embed
                embed = discord.Embed(title=f"VPS Resources - {vps_name}", color=discord.Color.green())
                embed.add_field(name="Memory Usage", value=f"```{mem_usage}```", inline=True)
                embed.add_field(name="Disk Usage", value=f"```{disk_usage}```", inline=True)
                embed.add_field(name="CPU", value=f"```{cpu_usage}```", inline=True)
                embed.add_field(name="Top 5 CPU Processes", value=f"```{top_processes}```", inline=False)
                
                await interaction.edit_original_response(embed=embed)
        except Exception as e:
            await handle_connection_error(e, interaction, vps_name)

    @app_commands.command(name="help", description="Show the available commands")
    async def help(self, interaction:discord.Interaction):
        embed = discord.Embed(title="Help", description="List of commands and their usages:", color=discord.Color.blue())

        # settempchannel command details
        embed.add_field(name="!login <vpsname>", value="Logs in to a VPS and sets that channel state to 'logged in'", inline=False)


        await interaction.response.send_message(embed=embed)