import os
import discord
import json
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
FLIGHT_ANNOUNCE_CHANNEL_ID = int(os.getenv("FLIGHT_ANNOUNCE_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Flight store for mock linking
flight_data = {}

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png?ex=6882e6fe&is=6881957e&hm=fb230793ee874c1e922ea013ff52da81c2a67b85a7c84aa6b0297ed7c8897e90&=&format=webp&quality=lossless&width=843&height=24"

# Check if user has required role
def is_whitelisted(interaction: discord.Interaction) -> bool:
    return any(role.id == WHITELIST_ROLE_ID for role in interaction.user.roles)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot connected as {bot.user}")

# /affiliate_add
@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
async def affiliate_add(interaction: discord.Interaction, company_name: str, discord_link: str, roblox_group: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"New Affiliate Added",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Company", value=f"**{company_name}**", inline=False)
    embed.add_field(name="Discord", value=f"[🔗 Discord Link]({discord_link})", inline=True)
    embed.add_field(name="Roblox Group", value=f"[🔗 Roblox Group]({roblox_group})", inline=True)
    embed.set_image(url=BANNER_URL)

    await interaction.response.send_message(embed=embed)

# /affiliate_remove
@tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
async def affiliate_remove(interaction: discord.Interaction, company_name: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Affiliate Removed",
        description=f"The affiliate **{company_name}** has been removed.",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_image(url=BANNER_URL)
    await interaction.response.send_message(embed=embed)

# /embed
@tree.command(name="embed", description="Send embed using Discohook JSON", guild=discord.Object(id=GUILD_ID))
async def embed(interaction: discord.Interaction, json_input: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    try:
        data = json.loads(json_input)
        embed = discord.Embed.from_dict(data["embeds"][0])
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error parsing embed: {e}", ephemeral=True)

# /flight_create
@tree.command(name="flight_create", description="Create a new flight event", guild=discord.Object(id=GUILD_ID))
async def flight_create(interaction: discord.Interaction, route: str, start_time: str, aircraft: str, flight_code: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    event_name = f"{flight_code} - {route}"
    description = (
        f"**Flight Host**: {interaction.user.mention}\n"
        f"**Flight Code**: {flight_code}\n"
        f"**Route**: {route}\n"
        f"**Aircraft**: {aircraft}\n"
        f"**Start Time**: {start_time}"
    )

    guild = interaction.guild
    event = await guild.scheduled_events.create(
        name=event_name,
        start_time=discord.utils.parse_time(start_time),
        description=description,
        channel=guild.system_channel,
        entity_type=discord.EntityType.external,
        location="TBD",
        privacy_level=discord.PrivacyLevel.guild_only,
    )

    flight_data[flight_code] = {
        "event_id": event.id,
        "route": route,
        "aircraft": aircraft,
        "time": start_time
    }

    await interaction.response.send_message(f"Flight created: {event.name} (ID: {event.id})")

# /flight_host
@tree.command(name="flight_host", description="Announce a scheduled flight", guild=discord.Object(id=GUILD_ID))
async def flight_host(interaction: discord.Interaction, flight_code: str, aircraft: str, route: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    if flight_code not in flight_data:
        await interaction.response.send_message("No event found for this flight code.", ephemeral=True)
        return

    data = flight_data[flight_code]
    announce_channel = bot.get_channel(FLIGHT_ANNOUNCE_CHANNEL_ID)

    embed = discord.Embed(
        title="✈️ FLIGHT SCHEDULED",
        description=(
            f"A new flight has been scheduled on **{datetime.utcnow().strftime('%d/%m/%Y')}** at **{data['time']}**\n"
            f"Your flight will be **{route}**.\n\n"
            f"Flight **{flight_code}** is operating with {aircraft}."
        ),
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_image(url=BANNER_URL)

    await announce_channel.send(embed=embed)
    await interaction.response.send_message("Flight announcement sent!", ephemeral=True)

bot.run(TOKEN)
