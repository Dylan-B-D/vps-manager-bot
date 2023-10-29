# cogs/vps_login_cog.py

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
from utils.ssh_utils import establish_ssh_connection
from utils.embed_utils import (send_response_embed, handle_connection_error, edit_response_embed)
from utils.data_utils import (save_login_state, load_from_bson, save_to_bson, load_vps_configs, setup_cache_directory)

# Initialize cache directory
CACHE_DIR = setup_cache_directory()

# Time before login state for channel expires
TIMEOUT_SECONDS = 1800

class VPSLogin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.vpses = load_vps_configs(self.config)
        self.login_states = load_from_bson(os.path.join(CACHE_DIR, 'login_states.bson'))
        self.check_login_validity.start()


    
    @tasks.loop(minutes=5)  # Check every 5 minutes
    async def check_login_validity(self):
        """Invalidate logins that are older than 30 minutes."""
        filepath = os.path.join(CACHE_DIR, 'login_states.bson')
        login_states = load_from_bson(filepath)
        current_time = datetime.utcnow()
        updated = False

        for string_key, data in list(login_states.items()):
            key = tuple(map(int, string_key.split('_')))
            timestamp = data["timestamp"]
            difference = current_time - timestamp
            if difference.total_seconds() > TIMEOUT_SECONDS:  # 30 minutes in seconds
                del login_states[string_key]
                updated = True


        if updated:
            save_to_bson(login_states, filepath)

    @app_commands.command(name="login", description="Login to a VPS server")
    async def slash_login(self, interaction:discord.Interaction):
        # Create a view with the available VPS names
        view = SelectVPSView(self.vpses, self)
        embed = discord.Embed(
            title="VPS Login",
            description="Choose a VPS from the dropdown menu below.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)



    @app_commands.command(name="currentvps", description="Show which vps is logged in in this channel")
    async def slash_current_vps(self, interaction:discord.Interaction):
        """Command to check the current logged-in VPS for the channel."""
        server_id = interaction.guild.id
        channel_id = interaction.channel.id
        string_key = f"{server_id}_{channel_id}"
        
        # Get the latest login states
        login_states = load_from_bson(os.path.join(CACHE_DIR, 'login_states.bson'))
        
        vps_name = login_states.get(string_key, {}).get("vps_name", None)
        timestamp = login_states.get(string_key, {}).get("timestamp", None)

        embed = discord.Embed(color=discord.Color.blue())
        
        if vps_name and timestamp:
            current_time = datetime.utcnow()
            difference = current_time - timestamp
            remaining_seconds = TIMEOUT_SECONDS - difference.total_seconds()
            remaining_minutes = int(remaining_seconds // 60)

            embed.title = ""
            embed.description = f"Currently logged in VPS for this channel: `{vps_name}`\n"
            embed.description += f"Time until loginstate expires: `{remaining_minutes} minutes`"
        else:
            embed.title = ""
            embed.description = "No VPS is currently logged in for this channel."
        
        await interaction.response.send_message(embed=embed)

class VPSDropdown(discord.ui.Select):
    def __init__(self, vpses, cog):
        self.vpses = vpses
        self.cog = cog  # Reference to the cog to access its methods and attributes

        options = [
            discord.SelectOption(label=name, value=name)
            for name in vpses.keys()
        ]
        super().__init__(placeholder="Select a VPS to login", options=options)

    async def callback(self, interaction: discord.Interaction):
        vps_name = self.values[0]
        vps = self.vpses[vps_name]

        # Starting the login process
        await send_response_embed(interaction, f"VPS Login - {vps_name}", "Connecting to VPS... Please wait...", discord.Color.blue())

        try:
            # Establishing an SSH connection to the VPS
            conn = await establish_ssh_connection(vps)
            async with conn:
                # Running a command to fetch the MOTD or any other information
                result = await conn.run('cat /etc/motd')
                
                # Extracting ASCII art if any, from the MOTD
                ascii_art = extract_ascii_art(result.stdout)
                description = f"```{ascii_art}```\n" if ascii_art else ""
                description += f"**Log-in as {vps['Username']} Successful!**"
                
                # Sending a response to the user
                await edit_response_embed(interaction, f"VPS Login - {vps_name}", description, discord.Color.green())
                
                # Saving the login state
                save_login_state((interaction.guild.id, interaction.channel.id), vps_name, os.path.join(CACHE_DIR, 'login_states.bson'))

        except Exception as e:
            # Handling any connection errors
            await handle_connection_error(e, interaction, vps_name)

        finally:
            # Removing the select menu after the login attempt
            await interaction.message.edit(view=None)

class SelectVPSView(discord.ui.View):
    def __init__(self, vpses, interaction, timeout=15):
        super().__init__(timeout=timeout)
        self.add_item(VPSDropdown(vpses, interaction))