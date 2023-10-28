# Standard Libraries
import configparser
import os
from datetime import datetime

# Third-party Libraries
import discord
from discord.ext import tasks, commands
from discord import app_commands

# Local Modules
from utils.text_utils import extract_ascii_art
from utils.vps_utils import (establish_ssh_connection, 
                             send_response_embed, 
                             edit_response_embed, 
                             handle_connection_error,
                             fetch_vps_stats,
                             process_vps_stats)
from utils.data_utils import (save_login_state, 
                              load_from_bson, 
                              save_to_bson)


# Directory constants
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE_DIR = os.path.join(BASE_DIR, 'cache', 'gamequeue')

# ---- DIRECTORY SETUP ---- #
# Create directories if they don't exist
for directory in [CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class VPSLogin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.vpses = self.load_vps_configs()
        self.login_states = load_from_bson(os.path.join(CACHE_DIR, 'login_states.bson'))
        self.check_login_validity.start()


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
    
    @tasks.loop(minutes=5)  # Check every 5 minutes
    async def check_login_validity(self):
        """Invalidate logins that are older than 30 minutes."""
        filepath = os.path.join(CACHE_DIR, 'login_states.bson')
        login_states = load_from_bson(filepath)
        current_time = datetime.utcnow()
        updated = False

        for string_key, data in list(login_states.items()):  # Use list() to avoid modifying dict during iteration
            key = tuple(map(int, string_key.split('_')))
            timestamp = data["timestamp"]
            difference = current_time - timestamp
            if difference.total_seconds() > 1800:  # 30 minutes in seconds
                del login_states[string_key]
                updated = True


        if updated:
            save_to_bson(login_states, filepath)

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
                save_login_state((interaction.guild.id, interaction.channel.id), vps_name, os.path.join(CACHE_DIR, 'login_states.bson'))

        except Exception as e:
            await handle_connection_error(e, interaction, vps_name)



    @app_commands.command(name="currentvps", description="Show which vps is logged in in this channel")
    async def slash_current_vps(self, interaction:discord.Interaction):
        """Command to check the current logged-in VPS for the channel."""
        server_id = interaction.guild.id
        channel_id = interaction.channel.id
        string_key = f"{server_id}_{channel_id}"
        vps_name = self.login_states.get(string_key, {}).get("vps_name", None)

        
        embed = discord.Embed(color=discord.Color.blue())
        
        if vps_name:
            embed.title = ""
            embed.description = f"Currently logged in VPS for this channel: `{vps_name}`"
        else:
            embed.title = ""
            embed.description = "No VPS is currently logged in for this channel."
        
        await interaction.response.send_message(embed=embed)