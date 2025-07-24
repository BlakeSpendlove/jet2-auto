import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
ANNOUNCE_CHANNEL_ID = os.getenv("ANNOUNCE_CHANNEL_ID")
WHITELIST_ROLE_ID = os.getenv("WHITELIST_ROLE_ID")

if not DISCORD_TOKEN or not GUILD_ID or not ANNOUNCE_CHANNEL_ID or not WHITELIST_ROLE_ID:
    raise ValueError("One or more required environment variables are missing.")

GUILD_ID = int(GUILD_ID)
ANNOUNCE_CHANNEL_ID = int(ANNOUNCE_CHANNEL_ID)
WHITELIST_ROLE_ID = int(WHITELIST_ROLE_ID)

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"

def is_whitelisted():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == WHITELIST_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("Slash commands synced!")

# /affiliate_add
@bot.tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@is_whitelisted()
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(title="Affiliate Added", color=discord.Color.red())
    embed.add_field(name="Company", value=f"**{company}**", inline=False)
    embed.add_field(name="Discord", value=f":link: [Click here]({discord_link})", inline=False)
    embed.add_field(name="Roblox Group", value=f":link: [Click here]({roblox_group})", inline=False)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Added on {datetime.utcnow().strftime('%d/%m/%Y')}")
    await interaction.response.send_message(embed=embed)

# /affiliate_remove
@bot.tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@is_whitelisted()
async def affiliate_remove(interaction: discord.Interaction, company: str):
    await interaction.response.send_message(f"Affiliate **{company}** has been removed.", ephemeral=True)

# /embed
@bot.tree.command(name="embed", description="Send Discohook JSON as embed", guild=discord.Object(id=GUILD_ID))
@is_whitelisted()
async def send_embed(interaction: discord.Interaction, json_input: str):
    try:
        data = json.loads(json_input)
        embed = discord.Embed.from_dict(data["embeds"][0])
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error parsing embed JSON: {e}", ephemeral=True)

# /flight_create
flight_data = {}  # {flight_code: {details}}

@bot.tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@is_whitelisted()
async def flight_create(interaction: discord.Interaction, route: str, start_time: str, aircraft: str, flight_code: str):
    try:
        event = await interaction.guild.create_scheduled_event(
            name=f"Flight {flight_code}",
            description=f"**Host**: {interaction.user.mention}\n**Route**: {route}\n**Aircraft**: {aircraft}\n**Flight Code**: {flight_code}",
            start_time=datetime.strptime(start_time, "%d/%m/%Y %H:%M"),
            end_time=datetime.strptime(start_time, "%d/%m/%Y %H:%M") + timedelta(hours=1),
            location="In-game"
        )
        flight_data[flight_code] = {
            "route": route,
            "aircraft": aircraft,
            "time": start_time,
            "event_url": f"https://discord.com/events/{interaction.guild.id}/{event.id}"
        }
        await interaction.response.send_message(f"Flight **{flight_code}** created and scheduled.")
    except Exception as e:
        await interaction.response.send_message(f"Failed to create flight: {e}", ephemeral=True)

# /flight_host
@bot.tree.command(name="flight_host", description="Send a flight announcement", guild=discord.Object(id=GUILD_ID))
@is_whitelisted()
async def flight_host(interaction: discord.Interaction, flight_code: str, aircraft: str, route: str):
    if interaction.channel.id != ANNOUNCE_CHANNEL_ID:
        await interaction.response.send_message("This command can only be used in the designated channel.", ephemeral=True)
        return
    if flight_code not in flight_data:
        await interaction.response.send_message("Flight code not found.", ephemeral=True)
        return

    info = flight_data[flight_code]
    embed = discord.Embed(title="**FLIGHT SCHEDULED** :airplane:", color=discord.Color.red())
    embed.add_field(name="Date", value=f"**{info['time'].split()[0]}**", inline=False)
    embed.add_field(name="Time", value=f"**{info['time'].split()[1]}**", inline=False)
    embed.add_field(name="Route", value=f"**{route}**", inline=False)
    embed.add_field(name="Flight Code", value=f"**{flight_code}**", inline=False)
    embed.add_field(name="Aircraft", value=f"{aircraft}", inline=False)
    embed.add_field(name="Event Link", value=info['event_url'], inline=False)
    embed.set_image(url=BANNER_URL)
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
