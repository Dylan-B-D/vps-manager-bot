# bot.py

# Third-party Libraries
import discord
from discord.ext import commands

# Bot Cogs
from cogs.vps_login_cog import VPSLogin
from cogs.utils_commands_cog import Utils

# Bot Modules
from utils.data_utils import get_bot_token

# ==============================
# CONFIGURATION
# ==============================

TOKEN = get_bot_token()

# Bot Command Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot initialization
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# ==============================
# BOT EVENTS
# ==============================

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    await bot.add_cog(VPSLogin(bot))
    await bot.add_cog(Utils(bot))

    await bot.tree.sync(guild=discord.Object(id=1154371216451317834))


@bot.event
async def on_slash_command_error(ctx, error):
    embed = discord.Embed(title="Error", description=str(error), color=discord.Color.red())
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN)