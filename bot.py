import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
FLIGHT_CHANNEL_ID = int(os.getenv("FLIGHT_CHANNEL_ID"))
BANNER_URL = os.getenv("BANNER_URL")

# Validate required environment variables
if not all([TOKEN, GUILD_ID, WHITELIST_ROLE_ID, FLIGHT_CHANNEL_ID, BANNER_URL]):
    raise ValueError("One or more required environment variables are missing.")

# Setup intents and bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Generate unique ID for footer
def generate_unique_id():
    return uuid.uuid4().hex[:6].upper()

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"✅ Logged in as {bot.user} and synced commands to guild {GUILD_ID}")

@bot.tree.command(name="flight_create", description="Create a flight event.")
@app_commands.describe(
    route="Flight route (e.g. Manchester to Lanzarote)",
    time="Start time (24hr, e.g. 15:00)",
    date="Date (DD/MM/YYYY)",
    aircraft="Aircraft type (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_create(interaction: discord.Interaction, route: str, time: str, date: str, aircraft: str, flight_code: str):
    # Check if user has the whitelisted role
    if WHITELIST_ROLE_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    try:
        # Parse datetime and add 1 hour
        start_datetime = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
        end_datetime = start_datetime + timedelta(hours=1)
        start_str = start_datetime.strftime("%d/%m/%Y %H:%M")
        end_str = end_datetime.strftime("%d/%m/%Y %H:%M")

        # Build embed
        embed = discord.Embed(
            title="✈️ New Flight Event",
            description=f"**Route:** {route}\n**Flight Code:** {flight_code}",
            color=discord.Color.red()
        )
        embed.add_field(name="Aircraft", value=aircraft, inline=True)
        embed.add_field(name="Time", value=f"{start_str} - {end_str}", inline=True)
        embed.set_image(url=BANNER_URL)
        embed.set_footer(text=f"ID: {generate_unique_id()}")

        # Send embed to flight channel
        channel = bot.get_channel(FLIGHT_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Flight created and posted.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Could not find the flight channel.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to create flight: {e}", ephemeral=True)

bot.run(TOKEN)
