# Standard Libraries
import configparser

# Third-party Libraries
import discord
from discord.ext import commands

# Bot Data

# Bot Modules

# Bot Cogs
from cogs.vps_login_cog import VPSLogin
from cogs.utils_commands_cog import Utils


# ==============================
# CONFIGURATION
# ==============================

# Configuration File Parsing
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['Bot']['Token']
except (configparser.Error, KeyError) as e:
    raise SystemExit("Error reading configuration file.") from e

# Bot Command Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot initialization
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')


# ==============================
# BOT EVENTS
# ==============================

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    await bot.add_cog(VPSLogin(bot))
    await bot.add_cog(Utils(bot))

    await bot.tree.sync()


@bot.event
async def on_slash_command_error(ctx, error):
    embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)