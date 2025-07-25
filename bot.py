import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

# Load environment variables from Railway
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID", 0))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID", 0))
BANNER_URL = os.getenv("BANNER_URL")

# Jet2 dark red color for embeds (replace if needed)
JET2_DARK_RED = 0x8B0000  # Dark red

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def add_banner(embed: discord.Embed) -> discord.Embed:
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)
    return embed

def has_schedule_role():
    def predicate(interaction: discord.Interaction) -> bool:
        if SCHEDULE_ROLE_ID == 0:
            return True  # If not set, allow all
        role = discord.utils.get(interaction.user.roles, id=SCHEDULE_ROLE_ID)
        return role is not None
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if GUILD_ID != 0:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print(f"Commands synced to guild ID {GUILD_ID}.")
    else:
        await tree.sync()
        print("Commands synced globally.")

@tree.command(name="ping", description="Simple ping command", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
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
            description=(
                f"Aircraft: {aircraft}\n"
                f"Route: {route}\n"
                f"Flight code: {flight_code}\n"
                f"Host: <@{interaction.user.id}>"
            ),
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )
        await interaction.response.send_message(f"Flight event created: {event.name} starting at {start_dt.strftime('%d/%m/%Y %H:%M')}")

        async def send_dm_before_flight():
            now = datetime.utcnow()
            wait_until = start_dt - timedelta(minutes=15)
            delta = (wait_until - now).total_seconds()
            if delta > 0:
                await discord.utils.sleep_until(wait_until)
            try:
                await interaction.user.send(f"Reminder: Your flight {flight_code} is scheduled at {start_dt.strftime('%H:%M')} UTC. Please prepare!")
            except Exception as e:
                print(f"Failed to DM user: {e}")

        bot.loop.create_task(send_dm_before_flight())

    except ValueError:
        await interaction.response.send_message("❌ Invalid date or time format. Use DD/MM/YYYY for date and HH:MM for time (24h format).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error creating event: {e}", ephemeral=True)

@tree.command(name="flight_host", description="Send a flight announcement", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    aircraft="Aircraft type",
    flight_code="Flight code"
)
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a guild.", ephemeral=True)
        return

    events = await guild.fetch_scheduled_events()
    matching_events = [event for event in events if flight_code in event.name]

    if not matching_events:
        await interaction.response.send_message(f"❌ No scheduled flight event found with flight code `{flight_code}`.", ephemeral=True)
        return

    event = matching_events[0]

    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=(
            f"Route: {route}\n"
            f"Aircraft: {aircraft}\n"
            f"Host: <@{interaction.user.id}>\n\n"
            "Please ensure you complete your bag drop, proceed through security, and arrive at the gate on time.\n"
            "Thank you for flying with us! ✈️"
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Flight Announcements")
    embed = add_banner(embed)

    message_content = f"@everyone Flight {flight_code} is now announced!\nJoin the scheduled event here: {event.url}"

    await interaction.response.send_message(content=message_content, embed=embed)

# Add your other commands here, use AFFILIATE_CHANNEL_ID, BANNER_URL, and role checks as needed

bot.run(DISCORD_TOKEN)
