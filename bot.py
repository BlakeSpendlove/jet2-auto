import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

# Load env variables (Railway sets these in ENV)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID", 0))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID", 0))
BANNER_URL = os.getenv("BANNER_URL")

JET2_DARK_RED = 0x8B0000  # Dark red color hex

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def is_scheduler():
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.user.roles, id=SCHEDULE_ROLE_ID)
        if role is None:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return False
        return True
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
@is_scheduler()
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

        # Create the scheduled event with host mention in description
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            description=f"Aircraft: {aircraft}\nRoute: {route}\nFlight code: {flight_code}\nHost: {interaction.user.mention}",
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        await interaction.response.send_message(f"✅ Flight event created: **{event.name}** starting at {start_dt.strftime('%d/%m/%Y %H:%M')}")
        
        # Schedule DM 15 minutes before the flight (XX:40 when flight is at XX:55)
        dm_time = start_dt - timedelta(minutes=15)
        now = datetime.utcnow()

        if dm_time > now:
            delay = (dm_time - now).total_seconds()
            async def send_dm():
                try:
                    await asyncio.sleep(delay)
                    await interaction.user.send(
                        f"Reminder: Your flight **{flight_code}** is in 15 minutes! Please prepare for boarding."
                    )
                except Exception as e:
                    print(f"Failed to send DM to host: {e}")
            bot.loop.create_task(send_dm())

    except ValueError:
        await interaction.response.send_message("❌ Invalid date or time format. Use DD/MM/YYYY for date and HH:MM for time (24h format).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating event: {e}", ephemeral=True)

@tree.command(name="flight_host", description="Send flight announcement", guild=discord.Object(id=GUILD_ID))
@is_scheduler()
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    aircraft="Aircraft type (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str):
    await interaction.response.defer(ephemeral=False)  # Acknowledge immediately

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("This command must be used in a guild.", ephemeral=True)
        return

    events = await guild.fetch_scheduled_events()
    matching_events = [event for event in events if flight_code in event.name]

    if not matching_events:
        await interaction.followup.send(f"❌ No scheduled flight event found with flight code `{flight_code}`.", ephemeral=True)
        return

    event = matching_events[0]

    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=(
            f"Route: {route}\n"
            f"Aircraft: {aircraft}\n"
            f"Host: {interaction.user.mention}\n\n"
            "Please complete your bag drop, proceed through security, and arrive at the gate on time.\n"
            "Thank you for flying with us! ✈️"
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Flight Announcements")
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    message_content = f"@everyone Flight **{flight_code}** is now announced!\nJoin the scheduled event here: {event.url}"

    await interaction.followup.send(content=message_content, embed=embed)

@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@is_scheduler()
@app_commands.describe(
    company_name="Company name",
    discord_link="Company Discord invite link",
    roblox_group="Roblox group URL or ID"
)
async def affiliate_add(interaction: discord.Interaction, company_name: str, discord_link: str, roblox_group: str):
    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("❌ Affiliate channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title="New Affiliate Added",
        description=(
            f"**Company:** {company_name}\n"
            f"**Discord:** {discord_link}\n"
            f"**Roblox Group:** {roblox_group}\n"
            f"**Added by:** {interaction.user.mention}\n"
            f"**Date:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}"
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Affiliate **{company_name}** added.", ephemeral=True)

@tree.command(name="affiliate_remove", description="Remove an affiliate by company name", guild=discord.Object(id=GUILD_ID))
@is_scheduler()
@app_commands.describe(
    company_name="Company name to remove"
)
async def affiliate_remove(interaction: discord.Interaction, company_name: str):
    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("❌ Affiliate channel not found.", ephemeral=True)
        return

    def check(m):
        return (m.author == bot.user and
                m.embeds and
                company_name.lower() in m.embeds[0].description.lower())

    async for message in channel.history(limit=200):
        if check(message):
            try:
                await message.delete()
                await interaction.response.send_message(f"✅ Affiliate **{company_name}** removed.", ephemeral=True)
                return
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to remove affiliate: {e}", ephemeral=True)
                return
    await interaction.response.send_message(f"❌ Affiliate **{company_name}** not found.", ephemeral=True)

@tree.command(name="embed", description="Send a custom embed from JSON", guild=discord.Object(id=GUILD_ID))
@is_scheduler()
@app_commands.describe(
    json_string="JSON string of the embed"
)
async def embed(interaction: discord.Interaction, json_string: str):
    import json
    try:
        embed_data = json.loads(json_string)
        embed = discord.Embed.from_dict(embed_data)
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Invalid embed JSON: {e}", ephemeral=True)

bot.run(DISCORD_TOKEN)
