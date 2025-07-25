import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the CommandTree instance here:
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()  # Sync commands when bot is ready
    print(f"Logged in as {bot.user}")

# Now you can define commands using @tree.command decorator
@tree.command(name="ping", description="Test command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="flight_create", description="Create a flight event")
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
        guild = interaction.guild
        start_dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            entity_metadata=discord.ScheduledEventEntityMetadata(location="Online"),
            description=f"Aircraft: {aircraft}\nHost: {host.display_name}",
        )
        
        await interaction.response.send_message(f"Flight event created: {event.url}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

bot.run("YOUR_BOT_TOKEN")
