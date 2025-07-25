import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Available in Python 3.9+
from dotenv import load_dotenv

# Load environment variables (Railway uses these automatically)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # Ensure this is set in Railway

# Setup bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Use built-in command tree

# On bot ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print(f"✅ Slash commands synced to guild ID {GUILD_ID}")

# /ping test command
@tree.command(name="ping", description="Simple ping command", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

# /flight_create command
@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    start_date="Start date in DD/MM/YYYY",
    start_time="Start time in 24h format HH:MM",
    aircraft="Aircraft type (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_create(
    interaction: discord.Interaction,
    route: str,
    start_date: str,
    start_time: str,
    aircraft: str,
    flight_code: str
):
    try:
        # Assume London time (BST/GMT)
        local_zone = ZoneInfo("Europe/London")
        local_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        local_dt = local_dt.replace(tzinfo=local_zone)
        start_dt_utc = local_dt.astimezone(ZoneInfo("UTC"))
        end_dt_utc = start_dt_utc + timedelta(hours=1)

        # Ensure event starts at least 1 min from now
        if start_dt_utc <= datetime.now(tz=ZoneInfo("UTC")) + timedelta(minutes=1):
            await interaction.response.send_message("❌ Start time must be at least 1 minute in the future.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt_utc,
            end_time=end_dt_utc,
            description=f"✈️ Aircraft: {aircraft}\n🛫 Route: {route}\n📟 Flight code: {flight_code}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        await interaction.response.send_message(
            f"✅ **Flight Event Created!**\n"
            f"📌 Name: `{event.name}`\n"
            f"🕒 Starts: {start_dt_utc.strftime('%d/%m/%Y %H:%M')} UTC\n"
            f"⏳ Ends: {end_dt_utc.strftime('%H:%M')} UTC"
        )

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date or time format. Please use **DD/MM/YYYY** for date and **HH:MM** (24-hour) for time.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating event: `{e}`", ephemeral=True)

# Run the bot
bot.run(TOKEN)
