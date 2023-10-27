# Standard Libraries
import configparser

# Third-party Libraries
import asyncssh
import discord
from discord.ext import commands

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

    @commands.command(name='login')
    async def login(self, ctx, vps_name: str):
        if vps_name not in self.vpses:
            await ctx.send(f"No VPS found with the name: {vps_name}")
            return

        vps = self.vpses[vps_name]
        embed = discord.Embed(title=f"VPS Login - {vps_name}", description="Connecting to VPS... Please wait...", color=discord.Color.blue())
        sent_embed = await ctx.send(embed=embed)

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
                await sent_embed.edit(embed=embed)
                self.login_states[(ctx.guild.id, ctx.channel.id)] = vps_name

        except Exception as e:
            error_msg = "Connection failed" if "The semaphore timeout period has expired" in str(e) else str(e)
            embed = discord.Embed(title=f"VPS Login - {vps_name}", description=error_msg, color=discord.Color.red())
            await sent_embed.edit(embed=embed)


    @commands.command(name='currentvps')
    async def current_vps(self, ctx):
        """Command to check the current logged-in VPS for the channel."""
        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        vps_name = self.login_states.get((server_id, channel_id), None)
        
        embed = discord.Embed(color=discord.Color.blue())
        
        if vps_name:
            embed.title = ""
            embed.description = f"Currently logged in VPS for this channel: `{vps_name}`"
        else:
            embed.title = ""
            embed.description = "No VPS is currently logged in for this channel."
        
        await ctx.send(embed=embed)