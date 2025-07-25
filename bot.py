import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

# Load environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Discord intents and bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Slash commands tree

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print("✅ Slash commands synced.")

# Basic /ping command
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
        # Convert to UTC from Europe/London time
        local_zone = ZoneInfo("Europe/London")
        local_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        local_dt = local_dt.replace(tzinfo=local_zone)
        start_dt_utc = local_dt.astimezone(ZoneInfo("UTC"))
        end_dt_utc = start_dt_utc + timedelta(hours=1)

        # Time must be in the future
        if start_dt_utc <= datetime.now(tz=ZoneInfo("UTC")) + timedelta(minutes=1):
            await interaction.response.send_message("❌ Start time must be at least 1 minute in the future.", ephemeral=True)
            return

        # Must be in a server
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        host_mention = interaction.user.mention

        # Create the event
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt_utc,
            end_time=end_dt_utc,
            description=(
                f"✈️ Aircraft: {aircraft}\n"
                f"🛫 Route: {route}\n"
                f"📟 Flight code: {flight_code}\n"
                f"👤 Host: {host_mention}"
            ),
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        await interaction.response.send_message(
            f"✅ **Flight Event Created!**\n"
            f"📌 Name: `{event.name}`\n"
            f"🕒 Starts: {start_dt_utc.strftime('%d/%m/%Y %H:%M')} UTC\n"
            f"⏳ Ends: {end_dt_utc.strftime('%H:%M')} UTC\n"
            f"👤 Host: {host_mention}"
        )

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date or time format. Please use **DD/MM/YYYY** for date and **HH:MM** (24-hour) for time.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating event: `{e}`", ephemeral=True)

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GUILD_ID:
        raise RuntimeError("❌ DISCORD_TOKEN or GUILD_ID not set in Railway variables.")
    bot.run(DISCORD_TOKEN)
