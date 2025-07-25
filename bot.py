import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

# Load environment variables from Railway
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@tree.command(name="ping", description="Simple ping command", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

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
    # Check if user has the schedule role
    if not any(role.id == SCHEDULE_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            description=f"Aircraft: {aircraft}\nRoute: {route}\nFlight Code: {flight_code}\nHost: {interaction.user.mention}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        await interaction.response.send_message(
            f"✅ Flight event created: **{event.name}** at {start_dt.strftime('%d/%m/%Y %H:%M')}"
        )

        # Schedule DM at XX:40 (15 minutes before a XX:55 flight)
        reminder_time = start_dt.replace(minute=40, second=0)
        now = datetime.utcnow()

        delay = (reminder_time - now).total_seconds()
        if delay > 0:
            await schedule_dm(interaction.user, route, flight_code, start_dt, delay)
        else:
            print("⏰ Skipping DM – XX:40 already passed")

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date or time format. Use DD/MM/YYYY for date and HH:MM for time (24h format).",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

async def schedule_dm(user, route, flight_code, start_dt, delay):
    await asyncio.sleep(delay)
    try:
        await user.send(
            f"✈️ Reminder: **Flight {flight_code} - {route}** is starting soon at **{start_dt.strftime('%H:%M')}**."
        )
        print(f"✅ DM sent to {user} at XX:40.")
    except discord.Forbidden:
        print(f"⚠️ Cannot DM {user} – DMs are disabled.")

bot.run(TOKEN)
