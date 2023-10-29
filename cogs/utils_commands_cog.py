# cogs/utils_commands_cog.py

# Standard Libraries
import os
import configparser

# Third-party Libraries
import discord
from discord.ext import commands
from discord import app_commands

# Local Modules
from utils.ssh_utils import (establish_ssh_connection, fetch_vps_stats, process_vps_stats)
from utils.embed_utils import (send_response_embed, handle_connection_error)
from utils.data_utils import (get_login_state, load_vps_configs, setup_cache_directory)

# Initialize cache directory
CACHE_DIR = setup_cache_directory()

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.vpses = load_vps_configs(self.config)


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