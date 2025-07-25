import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
FLIGHT_CHANNEL_ID = int(os.getenv("FLIGHT_CHANNEL_ID"))
FLIGHT_ROLE_ID = int(os.getenv("FLIGHT_ROLE_ID"))
AFFILIATE_ROLE_ID = int(os.getenv("AFFILIATE_ROLE_ID"))
BANNER_URL = os.getenv("BANNER_URL")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

def generate_id():
    return uuid.uuid4().hex[:6].upper()

@bot.tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(FLIGHT_ROLE_ID)
@app_commands.describe(
    route="e.g., Manchester to Tenerife",
    time="Start time in 24hr format (HH:MM)",
    aircraft="e.g., B737-800",
    flight_code="e.g., LS8800"
)
async def flight_create(interaction: discord.Interaction, route: str, time: str, aircraft: str, flight_code: str):
    try:
        start_time = datetime.strptime(time, "%H:%M")
        end_time = start_time + timedelta(hours=1)

        embed = discord.Embed(
            title="🛫 New Flight Created",
            color=discord.Color.blue()
        )
        embed.set_image(url=BANNER_URL)
        embed.add_field(name="Route", value=route, inline=False)
        embed.add_field(name="Flight Code", value=flight_code, inline=True)
        embed.add_field(name="Aircraft", value=aircraft, inline=True)
        embed.add_field(name="Start Time", value=start_time.strftime("%H:%M"), inline=True)
        embed.add_field(name="End Time", value=end_time.strftime("%H:%M"), inline=True)
        embed.set_footer(text=f"ID: {generate_id()}")

        channel = bot.get_channel(FLIGHT_CHANNEL_ID)
        await channel.send(embed=embed)
        await interaction.response.send_message("Flight event created successfully!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to create flight: {e}", ephemeral=True)

@bot.tree.command(name="flight_host", description="Send a flight announcement", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(FLIGHT_ROLE_ID)
@app_commands.describe(
    flight="Flight code (e.g., LS8800)",
    host="Who is hosting the flight?",
    time="Time (e.g., 17:30)"
)
async def flight_host(interaction: discord.Interaction, flight: str, host: str, time: str):
    embed = discord.Embed(
        title="📢 Flight Announcement",
        description=f"Flight **{flight}** is now open for boarding!",
        color=discord.Color.green()
    )
    embed.set_image(url=BANNER_URL)
    embed.add_field(name="Hosted by", value=host, inline=True)
    embed.add_field(name="Time", value=time, inline=True)
    embed.set_footer(text=f"ID: {generate_id()}")

    channel = bot.get_channel(FLIGHT_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message("Flight announcement sent.", ephemeral=True)

@bot.tree.command(name="affiliate_add", description="Add a new affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(AFFILIATE_ROLE_ID)
@app_commands.describe(
    company="Affiliate company name",
    discord_link="Invite link",
    roblox_group="Roblox group URL"
)
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(
        title="🤝 New Affiliate",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.add_field(name="Company", value=company, inline=False)
    embed.add_field(name="Discord", value=discord_link, inline=False)
    embed.add_field(name="Roblox Group", value=roblox_group, inline=False)
    embed.set_footer(text=f"Affiliation ID: {generate_id()} • Added {datetime.utcnow().strftime('%Y-%m-%d')}")

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Affiliate added!", ephemeral=True)

@bot.tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(AFFILIATE_ROLE_ID)
@app_commands.describe(company="Affiliate company name to remove")
async def affiliate_remove(interaction: discord.Interaction, company: str):
    embed = discord.Embed(
        title="❌ Affiliate Removed",
        description=f"{company} has been removed from the affiliate list.",
        color=discord.Color.dark_red()
    )
    embed.set_footer(text=f"Removed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} • ID: {generate_id()}")

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Affiliate removed!", ephemeral=True)

@bot.tree.command(name="embed", description="Send a custom embed", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(FLIGHT_ROLE_ID)
@app_commands.describe(
    title="Title of the embed",
    description="Description of the embed"
)
async def embed(interaction: discord.Interaction, title: str, description: str):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"ID: {generate_id()}")

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Embed sent.", ephemeral=True)

bot.run(TOKEN)
