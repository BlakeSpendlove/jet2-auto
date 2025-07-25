import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID"))
BANNER_URL = os.getenv("BANNER_URL")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

JET2_DARK_RED = discord.Color.from_str("#B00000")

# Permissions check
def is_scheduler():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == SCHEDULE_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user} and commands synced.")

@tree.command(name="ping", description="Check bot responsiveness", guild=discord.Object(id=GUILD_ID))
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
@is_scheduler()
async def flight_create(interaction: discord.Interaction, route: str, start_date: str, start_time: str, aircraft: str, flight_code: str):
    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        guild = interaction.guild

        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            description=(
                f"Aircraft: {aircraft}\n"
                f"Route: {route}\n"
                f"Flight code: {flight_code}\n"
                f"Host: {interaction.user.mention}"
            ),
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            location="Online / Virtual"
        )

        # DM host 15 mins before flight (at XX:40 if flight is XX:55)
        notify_time = start_dt - timedelta(minutes=15)

        @tasks.loop(seconds=30)
        async def notify_host():
            if datetime.utcnow() >= notify_time:
                try:
                    await interaction.user.send(f"Reminder: Your flight '{flight_code}' starts at {start_dt.strftime('%H:%M')}! Prepare the airport.")
                except:
                    print("Could not DM host.")
                notify_host.stop()

        notify_host.start()

        await interaction.response.send_message(f"✅ Flight event created: {event.name} at {start_dt.strftime('%d/%m/%Y %H:%M')}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@tree.command(name="flight_host", description="Send flight announcement", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    route="Flight route (e.g. LHR to JFK)",
    aircraft="Aircraft type (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
@is_scheduler()
async def flight_host(interaction: discord.Interaction, route: str, aircraft: str, flight_code: str):
    await interaction.response.defer(ephemeral=False)
    guild = interaction.guild
    events = await guild.fetch_scheduled_events()
    matching = [e for e in events if flight_code in e.name]

    if not matching:
        await interaction.followup.send(f"❌ No scheduled flight found with `{flight_code}`", ephemeral=True)
        return

    event = matching[0]

    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=(
            f"✈️ **Route:** {route}\n"
            f"🛩️ **Aircraft:** {aircraft}\n"
            f"👨‍✈️ **Host:** {interaction.user.mention}\n\n"
            "📢 Please check in, complete bag drop, and proceed through security.\n"
            "🎮 Join the airport below."
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🕹️ Game", value="[Join Jet2 Paphos Airport](https://www.roblox.com/games/117460430857307/Jet2-Pahpos-Airport)", inline=False)
    embed.add_field(name="📅 Event", value=f"[Click to View Event]({event.url})", inline=False)
    embed.set_footer(text="Flight Announcements")
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    await interaction.followup.send(
        content="@everyone Flight is now boarding!",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )

@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    company_name="Name of the company",
    discord_link="Discord invite link",
    roblox_group="Roblox group link"
)
@is_scheduler()
async def affiliate_add(interaction: discord.Interaction, company_name: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(
        title=f"Affiliate Added: {company_name}",
        description=(
            f"🔗 **Discord:** {discord_link}\n"
            f"🏢 **Roblox Group:** {roblox_group}\n"
            f"🕵️‍♂️ **Added by:** {interaction.user.mention}"
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Affiliate System")
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Affiliate added and logged in <#{AFFILIATE_CHANNEL_ID}>", ephemeral=True)

@tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(company_name="Company name to remove")
@is_scheduler()
async def affiliate_remove(interaction: discord.Interaction, company_name: str):
    embed = discord.Embed(
        title=f"Affiliate Removed: {company_name}",
        description=f"🕵️‍♂️ Removed by: {interaction.user.mention}",
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Affiliate System")
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    channel = bot.get_channel(AFFILIATE_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Affiliate removed and logged in <#{AFFILIATE_CHANNEL_ID}>", ephemeral=True)

@tree.command(name="embed", description="Send a custom embed from Discohook JSON", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(json_code="Embed JSON code from Discohook")
@is_scheduler()
async def embed(interaction: discord.Interaction, json_code: str):
    try:
        import json
        data = json.loads(json_code)
        emb = discord.Embed.from_dict(data["embeds"][0])
        await interaction.channel.send(embed=emb)
        await interaction.response.send_message("✅ Embed sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Invalid JSON: {e}", ephemeral=True)

bot.run(TOKEN)
