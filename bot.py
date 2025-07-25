import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

def get_env_int(var_name: str) -> int:
    val = os.getenv(var_name)
    if val is None:
        raise ValueError(f"Environment variable {var_name} not set.")
    try:
        return int(val)
    except Exception:
        raise ValueError(f"Environment variable {var_name} must be an integer.")

# Load environment variables
try:
    GUILD_ID = get_env_int("GUILD_ID")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if not DISCORD_TOKEN:
        raise ValueError("Environment variable DISCORD_TOKEN not set.")
except Exception as e:
    print(f"Config error: {e}")
    exit(1)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    try:
        await tree.sync(guild=guild)
        print(f"Commands synced to guild {GUILD_ID}.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@tree.command(name="ping", description="Simple ping command", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    start_date="Start date in DD/MM/YYYY",
    start_time="Start time in 24h format HH:MM",
    aircraft="Aircraft type (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_create(interaction: discord.Interaction, route: str, start_date: str, start_time: str, aircraft: str, flight_code: str):
    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command must be used in a guild.", ephemeral=True)
            return
        
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            description=f"Aircraft: {aircraft}\nRoute: {route}\nFlight code: {flight_code}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )
        await interaction.response.send_message(f"Flight event created: {event.name} starting at {start_dt.strftime('%d/%m/%Y %H:%M')}")
    except ValueError:
        await interaction.response.send_message("Invalid date or time format. Please use DD/MM/YYYY for date and HH:MM (24-hour) for time.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error creating event: {e}", ephemeral=True)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
