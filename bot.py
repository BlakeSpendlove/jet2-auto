import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
FLIGHT_CHANNEL_ID = int(os.getenv("FLIGHT_CHANNEL_ID"))

if not TOKEN or not GUILD_ID or not WHITELIST_ROLE_ID or not FLIGHT_CHANNEL_ID:
    raise ValueError("One or more required environment variables are missing.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Banner for embeds and events
EVENT_BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395766076490387597/jet2-and-jet2holidays-logos-1.png?ex=688435b4&is=6882e434&hm=38d94f0257e83e2d98c3a2e6ce3d72326a0804207e8a3f1b202131d4e5f33f63&=&format=webp&quality=lossless&width=1275&height=303"

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# --------------------------- /affiliate_add ---------------------------
@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(WHITELIST_ROLE_ID)
@app_commands.describe(company="Company name", discord_link="Discord invite", roblox_group="Roblox group link")
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(title="Affiliate Added", color=discord.Color.red())
    embed.add_field(name="Company", value=company, inline=False)
    embed.add_field(name="Discord", value=discord_link, inline=False)
    embed.add_field(name="Roblox Group", value=roblox_group, inline=False)
    embed.set_image(url=EVENT_BANNER_URL)
    embed.set_footer(text=f"Added by {interaction.user}", icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

# --------------------------- /affiliate_remove ---------------------------
@tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(WHITELIST_ROLE_ID)
@app_commands.describe(company="Company name to remove")
async def affiliate_remove(interaction: discord.Interaction, company: str):
    embed = discord.Embed(title="Affiliate Removed", description=f"{company} has been removed.", color=discord.Color.red())
    embed.set_image(url=EVENT_BANNER_URL)
    embed.set_footer(text=f"Removed by {interaction.user}", icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

# --------------------------- /embed ---------------------------
@tree.command(name="embed", description="Send a custom embed (JSON from Discohook)", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(WHITELIST_ROLE_ID)
@app_commands.describe(json="Raw Discohook-style JSON embed")
async def custom_embed(interaction: discord.Interaction, json: str):
    try:
        data = discord.Embed.from_dict(eval(json))
        await interaction.channel.send(embed=data)
        await interaction.response.send_message("✅ Embed sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to send embed: {e}", ephemeral=True)

# --------------------------- /flight_create ---------------------------
@tree.command(name="flight_create", description="Create a new flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(WHITELIST_ROLE_ID)
@app_commands.describe(route="Flight route", start_time="Start time (DD/MM/YYYY HH:MM)", aircraft="Aircraft", flight_code="Flight code")
async def flight_create(interaction: discord.Interaction, route: str, start_time: str, aircraft: str, flight_code: str):
    try:
        start_dt = datetime.strptime(start_time, "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)

        scheduled_event = await interaction.guild.create_scheduled_event(
            name=f"Flight {flight_code}",
            description=f"**Route:** {route}\n**Aircraft:** {aircraft}\n**Flight Code:** {flight_code}",
            start_time=start_dt,
            end_time=end_dt,
            entity_type=discord.EntityType.external,
            location="Jet2 Virtual Gate",
            privacy_level=discord.PrivacyLevel.guild_only
        )

        embed = discord.Embed(title="Flight Created", color=discord.Color.red())
        embed.add_field(name="Route", value=route, inline=False)
        embed.add_field(name="Aircraft", value=aircraft)
        embed.add_field(name="Flight Code", value=flight_code)
        embed.add_field(name="Start Time", value=start_dt.strftime("%d/%m/%Y %H:%M"))
        embed.add_field(name="End Time", value=end_dt.strftime("%d/%m/%Y %H:%M"))
        embed.set_image(url=EVENT_BANNER_URL)
        embed.set_footer(text=f"Created by {interaction.user}", icon_url=interaction.user.avatar.url)

        channel = bot.get_channel(FLIGHT_CHANNEL_ID)
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Flight created and event posted.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating flight: {e}", ephemeral=True)

# --------------------------- /flight_host ---------------------------
@tree.command(name="flight_host", description="Announce an existing flight", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_role(WHITELIST_ROLE_ID)
@app_commands.describe(route="Route", aircraft="Aircraft", flight_code="Flight code", host="Host user")
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str, host: discord.Member):
    embed = discord.Embed(title="Flight Announcement", color=discord.Color.red())
    embed.add_field(name="Route", value=route)
    embed.add_field(name="Aircraft", value=aircraft)
    embed.add_field(name="Flight Code", value=flight_code)
    embed.add_field(name="Host", value=host.mention)
    embed.set_image(url=EVENT_BANNER_URL)
    embed.set_footer(text=f"Announced by {interaction.user}", icon_url=interaction.user.avatar.url)

    channel = bot.get_channel(FLIGHT_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Flight announcement sent.")

# --------------------------- Error Handling ---------------------------
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)

bot.run(TOKEN)
