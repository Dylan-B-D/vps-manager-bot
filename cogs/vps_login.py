# Standard Libraries
import configparser

# Third-party Libraries
import asyncssh
import discord
import asyncio
from discord.ext import commands
from discord import app_commands

# Local Modules
from utils.text_utils import extract_ascii_art
from utils.vps_utils import (establish_ssh_connection, 
                             send_response_embed, 
                             edit_response_embed, 
                             handle_connection_error,
                             fetch_vps_stats,
                             process_vps_stats)


class VPSLogin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.login_states = {}
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

    @app_commands.command(name="login", description="Login to a VPS server")
    async def slash_login(self, interaction:discord.Interaction, vps_name: str):
        if vps_name not in self.vpses:
            await interaction.response.send_message(f"No VPS found with the name: {vps_name}")
            return

        vps = self.vpses[vps_name]
        await send_response_embed(interaction, f"VPS Login - {vps_name}", "Connecting to VPS... Please wait...", discord.Color.blue())

        conn = await establish_ssh_connection(vps)
        try:
            async with conn:
                result = await conn.run('cat /etc/motd')
                ascii_art = extract_ascii_art(result.stdout)
                description = f"```{ascii_art}```\n" if ascii_art else ""
                description += f"**Log-in as {vps['Username']} Successful!**"
                await edit_response_embed(interaction, f"VPS Login - {vps_name}", description, discord.Color.green())
                self.login_states[(interaction.guild.id, interaction.channel.id)] = vps_name

        except Exception as e:
            await handle_connection_error(e, interaction, vps_name)


    @app_commands.command(name="vpsresources", description="Check the resource usages of the logged-in VPS")
    async def slash_vps_resources(self, interaction:discord.Interaction):
        """Command to check the resource usages of the logged-in VPS."""
        server_id = interaction.guild.id
        channel_id = interaction.channel.id
        vps_name = self.login_states.get((server_id, channel_id), None)

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




    @app_commands.command(name="currentvps", description="Show which vps is logged in in this channel")
    async def slash_current_vps(self, interaction:discord.Interaction):
        """Command to check the current logged-in VPS for the channel."""
        server_id = interaction.guild.id
        channel_id = interaction.channel.id
        vps_name = self.login_states.get((server_id, channel_id), None)
        
        embed = discord.Embed(color=discord.Color.blue())
        
        if vps_name:
            embed.title = ""
            embed.description = f"Currently logged in VPS for this channel: `{vps_name}`"
        else:
            embed.title = ""
            embed.description = "No VPS is currently logged in for this channel."
        
        await interaction.response.send_message(embed=embed)