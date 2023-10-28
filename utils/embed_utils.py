# utils/embed_utils.py


# Third-party Libraries
import discord

async def send_response_embed(interaction, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    await interaction.response.send_message(embed=embed)

async def edit_response_embed(interaction, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    await interaction.edit_original_response(embed=embed)

async def handle_connection_error(e, interaction, vps_name):
    error_msg = "Connection failed" if "The semaphore timeout period has expired" in str(e) else str(e)
    await edit_response_embed(interaction, f"VPS Resources - {vps_name}", error_msg, discord.Color.red())