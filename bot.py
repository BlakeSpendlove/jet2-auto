import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from datetime import datetime

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
FLIGHT_ANNOUNCE_CHANNEL_ID = int(os.getenv("FLIGHT_ANNOUNCE_CHANNEL_ID"))

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png?ex=6882e6fe&is=6881957e&hm=fb230793ee874c1e922ea013ff52da81c2a67b85a7c84aa6b0297ed7c8897e90&=&format=webp&quality=lossless&width=843&height=24"

flight_events = {}

def is_whitelisted(interaction: discord.Interaction):
    return WHITELIST_ROLE_ID in [role.id for role in interaction.user.roles]

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Logged in as {client.user}")

# /affiliate_add
@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(company="Company name", discord_link="Discord invite", roblox_group="Roblox group link")
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title="New Affiliate Added",
        description=f"**{company}**\n\n🔗 [Discord Link]({discord_link})\n🔗 [Roblox Group]({roblox_group})",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"Added on {datetime.utcnow().strftime('%d/%m/%Y')}")

    await interaction.response.send_message(embed=embed)

# /affiliate_remove
@tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(company="Company name to remove")
async def affiliate_remove(interaction: discord.Interaction, company: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    await interaction.response.send_message(f"Affiliate **{company}** has been removed from the list.")

# /embed
@tree.command(name="embed", description="Send a Discohook JSON embed", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(json_data="Embed JSON from Discohook")
async def embed(interaction: discord.Interaction, json_data: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    try:
        data = json.loads(json_data)
        embed = discord.Embed.from_dict(data)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

# /flight_create
@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(route="e.g. LBA to ALC", time="e.g. 19:00", aircraft="e.g. B737-800", flight_code="e.g. LS8800")
async def flight_create(interaction: discord.Interaction, route: str, time: str, aircraft: str, flight_code: str):
    if not is_whitelisted(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    name = f"{flight_code} - {route}"
    description = (
        f"**Route**: {route}\n"
        f"**Time**: {time}\n"
        f"**Aircraft**: {aircraft}\n"
        f"**Flight Code**: {flight_code}\n"
        f"**Host**: {interaction.user.mention}"
    )

    try:
        event = await interaction.guild.scheduled_events.create(
            name=name,
            description=description,
            start_time=discord.utils.utcnow(),
            end_time=discord.utils.utcnow(),
            entity_type=discord.EntityType.external,
            location="Airport",
            privacy_level=discord.PrivacyLevel.guild_only
        )
        flight_events[flight_code] = {
            "event_id": event.id,
            "time": time,
            "route": route,
            "aircraft": aircraft
        }
        await interaction.response.send_message(f"Flight event **{name}** created and scheduled.")
    except Exception as e:
        await interaction.response.send_message(f"Failed to create event: {e}", ephemeral=True)

# /flight_host
@tree.command(name="flight_host", description="Announce a flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(flight_code="Flight code", aircraft="Aircraft", route="Route")
async def flight_host(interaction: discord.Interaction, flight_code: str, aircraft: str, route: str):
    if not is_whitelisted(interaction) or interaction.channel.id != FLIGHT_ANNOUNCE_CHANNEL_ID:
        await interaction.response.send_message("You are not authorized to use this command in this channel.", ephemeral=True)
        return

    if flight_code not in flight_events:
        await interaction.response.send_message(f"No flight found for code **{flight_code}**", ephemeral=True)
        return

    flight = flight_events[flight_code]

    embed = discord.Embed(
        title="**FLIGHT SCHEDULED ✈️**",
        description=(
            f"A new flight has been scheduled on **{datetime.utcnow().strftime('%d/%m/%Y')}** at **{flight['time']}**\n"
            f"Your flight will be **{route}**.\n\n"
            f"Flight **{flight_code}** is operating with {aircraft}"
        ),
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)

    await interaction.response.send_message(embed=embed)

client.run(TOKEN)
