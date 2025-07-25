import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import os
import asyncio
import json

# Load environment variables from Railway
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree  # Use existing command tree

JET2_DARK_RED = 0x8B0000  # Dark Red color hex (can be adjusted if needed)

def has_schedule_role():
    def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        roles = interaction.user.roles if hasattr(interaction.user, "roles") else []
        return any(role.id == SCHEDULE_ROLE_ID for role in roles)
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print("Commands synced.")

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
            description=f"Host: <@{interaction.user.id}>\nAircraft: {aircraft}\nRoute: {route}\nFlight code: {flight_code}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        async def dm_host():
            await discord.utils.sleep_until(start_dt.replace(minute=40, second=0, microsecond=0))
            try:
                await interaction.user.send(f"Reminder: Your flight {flight_code} event starts at {start_dt.strftime('%H:%M')} (15 minutes from now).")
            except Exception:
                print(f"Could not send DM to {interaction.user}.")

        bot.loop.create_task(dm_host())

        await interaction.response.send_message(f"Flight event created: {event.name} starting at {start_dt.strftime('%d/%m/%Y %H:%M')}")

    except ValueError:
        await interaction.response.send_message("❌ Invalid date or time format. Use DD/MM/YYYY for date and HH:MM for time (24h format).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error creating event: {e}", ephemeral=True)

@tree.command(name="embed", description="Send a custom embed (JSON from Discohook)", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
@app_commands.describe(json_string="JSON string for the embed")
async def embed(interaction: discord.Interaction, json_string: str):
    try:
        embed_data = json.loads(json_string)
        embed = discord.Embed.from_dict(embed_data)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Failed to send embed: {e}", ephemeral=True)

@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
@app_commands.describe(
    company="Affiliate company name",
    discord_link="Affiliate Discord invite link",
    roblox_group="Roblox group link"
)
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(
        title=f"Affiliate Added: {company}",
        description=f"Discord: {discord_link}\nRoblox Group: {roblox_group}",
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Affiliate Management")

    # Send embed to affiliate channel
    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Affiliate {company} added and logged.", ephemeral=True)
    else:
        await interaction.response.send_message("Affiliate channel not found.", ephemeral=True)

@tree.command(name="affiliate_remove", description="Remove an affiliate by company name", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
@app_commands.describe(company="Affiliate company name to remove")
async def affiliate_remove(interaction: discord.Interaction, company: str):
    embed = discord.Embed(
        title=f"Affiliate Removed: {company}",
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Affiliate Management")

    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Affiliate {company} removed and logged.", ephemeral=True)
    else:
        await interaction.response.send_message("Affiliate channel not found.", ephemeral=True)

@tree.command(name="flight_host", description="Send a flight announcement", guild=discord.Object(id=GUILD_ID))
@has_schedule_role()
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    aircraft="Aircraft type",
    flight_code="Flight code"
)
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str):
    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=f"Route: {route}\nAircraft: {aircraft}\nHost: <@{interaction.user.id}>",
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Flight Announcements")
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
