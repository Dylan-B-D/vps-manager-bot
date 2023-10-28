# Standard Libraries
import configparser

# Third-party Libraries
import asyncssh
import discord
from discord.ext import commands
from discord import app_commands


# Local Modules
from utils.text_utils import extract_ascii_art


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
        embed = discord.Embed(title=f"VPS Login - {vps_name}", description="Connecting to VPS... Please wait...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

        try:
            async with asyncssh.connect(
                vps['IP'],
                username=vps['Username'],
                password=vps['Password'],
                known_hosts=None
            ) as conn:
                result = await conn.run('cat /etc/motd')
                ascii_art = extract_ascii_art(result.stdout)
                description = f"```{ascii_art}```\n" if ascii_art else ""
                description += f"**Log-in as {vps['Username']} Successful!**"
                embed = discord.Embed(title=f"VPS Login - {vps_name}", description=description, color=discord.Color.green())
                await interaction.edit_original_response(embed=embed)
                self.login_states[(interaction.guild.id, interaction.channel.id)] = vps_name

        except Exception as e:
            error_msg = "Connection failed" if "The semaphore timeout period has expired" in str(e) else str(e)
            embed = discord.Embed(title=f"VPS Login - {vps_name}", description=error_msg, color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)

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

        embed = discord.Embed(title=f"VPS Resources - {vps_name}", description="Establishing connection... Please wait...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

        vps = self.vpses[vps_name]

        try:
            async with asyncssh.connect(
                vps['IP'],
                username=vps['Username'],
                password=vps['Password'],
                known_hosts=None
            ) as conn:
                # Get basic resource usage using 'free -h' and 'df -h' commands
                memory_result = await conn.run('free -h | tail -n +2')
                disk_result = await conn.run('df -h / | tail -n +2')
                
                # Extract the top 5 processes using resources with 'ps'
                top_processes_result = await conn.run("ps -eo pid,%cpu,%mem,cmd --sort=-%cpu | head -n 6")

                # Parsing memory usage
                mem_data = memory_result.stdout.split()
                mem_usage = f"Total: {mem_data[0]}\nUsed: {mem_data[1]}\nFree: {mem_data[2]}\nShared: {mem_data[4]}\nBuff/Cache: {mem_data[5]}\nAvailable: {mem_data[6]}"

                # Parsing disk usage
                disk_data = disk_result.stdout.split()
                disk_usage = f"Size: {disk_data[1]}\nUsed: {disk_data[2]}\nAvail: {disk_data[3]}\nUse%: {disk_data[4]}"
                
                # Parsing top processes
                process_lines = top_processes_result.stdout.splitlines()[1:]  # Skip the header
                top_processes = "\n".join([f"{i+1}. {line}" for i, line in enumerate(process_lines)])
                
                # Creating Embed
                embed = discord.Embed(title=f"VPS Resources - {vps_name}", color=discord.Color.green())
                embed.add_field(name="Memory Usage", value=f"```{mem_usage}```", inline=True)
                embed.add_field(name="Disk Usage", value=f"```{disk_usage}```", inline=True)
                embed.add_field(name="Top 5 CPU Processes", value=f"```{top_processes}```", inline=False)
                await interaction.edit_original_response(embed=embed)

        except Exception as e:
            error_msg = "Connection failed" if "The semaphore timeout period has expired" in str(e) else str(e)
            embed = discord.Embed(title=f"VPS Resources - {vps_name}", description=error_msg, color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)



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