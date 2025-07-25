import os
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # Your test server ID here

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree

def generate_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    # Sync commands only for the test guild (very fast for testing)
    await tree.sync(guild=guild)
    print(f"Synced commands to guild ID {GUILD_ID}")

# Simple example command to verify commands are visible
@tree.command(name="ping", description="Simple test command")
@app_commands.guilds(discord.Object(id=GUILD_ID))  # This limits to your guild for quick registration
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# Example command with parameters and role check
def is_whitelisted():
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.user.roles, id=int(os.getenv("WHITELIST_ROLE_ID")))
        if role is None:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@tree.command(name="flight_create", description="Create a flight event")
@app_commands.guilds(discord.Object(id=GUILD_ID))
@is_whitelisted()
@app_commands.describe(
    route="Flight route, e.g. Manchester to Alicante",
    date="Date (DD/MM/YYYY)",
    time="Start time (24-hour HH:MM)",
    aircraft="Aircraft type",
    flight_code="Flight code",
    host="Select the host"
)
async def flight_create(interaction: discord.Interaction, route: str, date: str, time: str, aircraft: str, flight_code: str, host: discord.Member):
    try:
        start_dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        embed = discord.Embed(title="Flight Created", color=0x2b2d31)
        embed.add_field(name="Route", value=route)
        embed.add_field(name="Aircraft", value=aircraft)
        embed.add_field(name="Flight Code", value=flight_code)
        embed.add_field(name="Host", value=host.mention)
        embed.set_footer(text=f"ID: {generate_id()}")

        # You can send the embed in a specific channel if you want here

        await interaction.response.send_message("Flight created!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

bot.run(TOKEN)
