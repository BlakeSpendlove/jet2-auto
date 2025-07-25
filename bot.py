import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import aiohttp

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
FLIGHT_CHANNEL_ID = int(os.getenv("FLIGHT_CHANNEL_ID"))
EVENT_CHANNEL_ID = int(os.getenv("EVENT_CHANNEL_ID"))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

FLIGHT_BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395766076490387597/jet2-and-jet2holidays-logos-1.png?ex=688435b4&is=6882e434&hm=38d94f0257e83e2d98c3a2e6ce3d72326a0804207e8a3f1b202131d4e5f33f63&=&format=webp&quality=lossless&width=1275&height=303"

# Create aiohttp session on bot start for HTTP requests
@bot.event
async def on_ready():
    if not hasattr(bot, "http_session"):
        bot.http_session = aiohttp.ClientSession()
    # Sync commands for the guild only (fast testing)
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"Bot is online as {bot.user} and commands synced.")

# Utility to generate a random 6 char ID
def generate_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

# Helper: fetch image bytes for scheduled event banner
async def get_banner_bytes(url: str):
    async with bot.http_session.get(url) as resp:
        return await resp.read()

# Check role decorator for commands
def has_whitelist_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.user.roles, id=WHITELIST_ROLE_ID)
        if role is None:
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# === COMMANDS === #

@bot.tree.command(name="flight_create", description="Create a flight event")
@has_whitelist_role()
@app_commands.describe(
    route="Route (e.g., Manchester to Alicante)",
    date="Date (DD/MM/YYYY)",
    time="Start Time (24-hour format HH:MM)",
    aircraft="Aircraft (e.g., B737-800)",
    flight_code="Flight Code (e.g., LS8800)",
    host="Select the host"
)
async def flight_create(interaction: discord.Interaction, route: str, date: str, time: str, aircraft: str, flight_code: str, host: discord.Member):
    try:
        start_dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M").replace(tzinfo=datetime.timezone.utc)
        end_dt = start_dt + timedelta(hours=1)

        embed = discord.Embed(
            title="Jet2 Flight Created",
            description=f"**Route:** {route}\n**Aircraft:** {aircraft}\n**Flight Code:** {flight_code}\n**Host:** {host.mention}",
            color=0x2b2d31
        )
        embed.set_image(url=FLIGHT_BANNER_URL)
        embed.set_footer(text=f"ID: {generate_id()}")

        channel = bot.get_channel(FLIGHT_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("❌ Flight channel not found.", ephemeral=True)
            return
        await channel.send(embed=embed)

        event_channel = bot.get_channel(EVENT_CHANNEL_ID)
        if event_channel is None:
            await interaction.response.send_message("❌ Event channel not found.", ephemeral=True)
            return

        banner_bytes = await get_banner_bytes(FLIGHT_BANNER_URL)

        await interaction.guild.scheduled_events.create(
            name=f"Jet2 | {route}",
            description=f"Flight: {flight_code}\nAircraft: {aircraft}\nHost: {host.display_name}",
            start_time=start_dt,
            end_time=end_dt,
            channel=event_channel,
            entity_type=discord.EntityType.voice,
            image=banner_bytes
        )

        await interaction.response.send_message("✅ Flight created and event scheduled.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating flight: {e}", ephemeral=True)

@bot.tree.command(name="flight_host", description="Announce a hosted flight")
@has_whitelist_role()
@app_commands.describe(
    route="Route (e.g., Manchester to Alicante)",
    aircraft="Aircraft (e.g., B737-800)",
    flight_code="Flight Code (e.g., LS8800)",
    host="Select the host"
)
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str, host: discord.Member):
    try:
        embed = discord.Embed(
            title="Jet2 Flight Hosted",
            description=f"**Route:** {route}\n**Aircraft:** {aircraft}\n**Flight Code:** {flight_code}\n**Host:** {host.mention}",
            color=0x2b2d31
        )
        embed.set_image(url=FLIGHT_BANNER_URL)
        embed.set_footer(text=f"ID: {generate_id()}")

        channel = bot.get_channel(FLIGHT_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("❌ Flight channel not found.", ephemeral=True)
            return

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Flight hosted announcement sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="affiliate_add", description="Add an affiliate")
@has_whitelist_role()
@app_commands.describe(
    company="Company name",
    discord_link="Discord invite link",
    roblox_group="Roblox group link"
)
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    try:
        embed = discord.Embed(title=f"New Affiliate: {company}", color=0xff0000)
        embed.add_field(name="Discord", value=discord_link, inline=False)
        embed.add_field(name="Roblox Group", value=roblox_group, inline=False)
        embed.set_footer(text=f"Date: {datetime.utcnow().strftime('%d/%m/%Y')} • ID: {generate_id()}")

        channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("❌ Affiliate channel not found.", ephemeral=True)
            return

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Affiliate added.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error adding affiliate: {e}", ephemeral=True)

@bot.tree.command(name="affiliate_remove", description="Remove an affiliate")
@has_whitelist_role()
@app_commands.describe(company="Company name")
async def affiliate_remove(interaction: discord.Interaction, company: str):
    try:
        embed = discord.Embed(title=f"Affiliate Removed: {company}", color=0xff0000)
        embed.set_footer(text=f"Date: {datetime.utcnow().strftime('%d/%m/%Y')} • ID: {generate_id()}")

        channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("❌ Affiliate channel not found.", ephemeral=True)
            return

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Affiliate removed.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error removing affiliate: {e}", ephemeral=True)

@bot.tree.command(name="embed", description="Send a custom embed from Discohook JSON")
@has_whitelist_role()
@app_commands.describe(json_code="Discohook JSON code")
async def embed(interaction: discord.Interaction, json_code: str):
    try:
        data = json.loads(json_code)

        # Expecting a dict with keys: url, embeds (list)
        webhook_url = data.get("url")
        embeds_data = data.get("embeds")
        if not webhook_url or not embeds_data:
            await interaction.response.send_message("❌ JSON must include 'url' and 'embeds' keys.", ephemeral=True)
            return

        webhook = discord.Webhook.from_url(webhook_url, client=bot)

        embeds = [discord.Embed.from_dict(e) for e in embeds_data]
        await webhook.send(embeds=embeds)
        await interaction.response.send_message("✅ Embed sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Invalid JSON or error: {e}", ephemeral=True)

# Run bot
bot.run(TOKEN)
