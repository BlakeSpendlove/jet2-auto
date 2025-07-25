import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
import os
import asyncio

# Load environment variables from Railway
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))

intents = discord.Intents.default()
intents.members = True  # Needed to get user roles
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Logged in as {bot.user} and commands synced to guild {GUILD_ID}")

@tree.command(name="ping", description="Ping the bot", guild=discord.Object(id=GUILD_ID))
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
    # Role check
    if not any(role.id == SCHEDULE_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    try:
        # Parse local datetime
        local_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        start_dt_utc = local_dt.replace(tzinfo=timezone.utc)
        end_dt_utc = start_dt_utc + timedelta(hours=1)

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        # Create event
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt_utc,
            end_time=end_dt_utc,
            description=f"✈️ Aircraft: {aircraft}\n🛫 Route: {route}\n🆔 Flight Code: {flight_code}\n👨‍✈️ Host: {interaction.user.mention}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        await interaction.response.send_message(
            f"✅ Flight event **{event.name}** created for **{local_dt.strftime('%d/%m/%Y %H:%M')}**!"
        )

        # DM reminder at XX:40
        reminder_time = local_dt.replace(minute=40, second=0)
        delay = (reminder_time - datetime.utcnow()).total_seconds()

        if delay > 0:
            async def send_reminder():
                await asyncio.sleep(delay)
                try:
                    await interaction.user.send(
                        f"🛫 **Reminder:** Your flight **{flight_code} - {route}** starts at {local_dt.strftime('%H:%M')}.\nBe ready to host!"
                    )
                except:
                    print("⚠️ Failed to send DM to host.")
            bot.loop.create_task(send_reminder())
        else:
            print("⏰ Reminder time already passed. Skipping DM.")

    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid date or time format. Use **DD/MM/YYYY** for date and **HH:MM** (24h format).",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

bot.run(DISCORD_TOKEN)
