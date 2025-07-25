import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

# Set your guild ID here for faster command registration during testing
GUILD_ID = 123456789012345678  # replace with your server's guild ID as int

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree  # Use existing tree from bot

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # Sync commands to your guild for quick update
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print("Commands synced.")

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
        # Parse start datetime from input
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)  # Event duration fixed to 1 hour
        
        # Create Discord event in the current guild's scheduled events channel (or default)
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command must be used in a guild.", ephemeral=True)
            return
        
        # Create the event
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
    except Exception as e:
        await interaction.response.send_message(f"Error creating event: {e}", ephemeral=True)

bot.run("YOUR_BOT_TOKEN")
