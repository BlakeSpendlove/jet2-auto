import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))
allowed_channel_id = int(os.getenv("ALLOWED_CHANNEL_ID"))

SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png?ex=687ba6be&is=687a553e&hm=a96e719147a26743f923afbe2337735c43a22a2a657e1b0cd2e53820b75b0ad0&=&format=webp&quality=lossless&width=843&height=24"

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged in as {bot.user}")

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    return f"ID: {generate_id()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight", guild=discord.Object(id=guild_id))
@app_commands.describe(
    host="Host of the flight",
    time="Time of the flight (e.g. 18:00 GMT)",
    flight_info="Flight info (e.g. Bournemouth -> Punta Cana)",
    aircraft_type="Aircraft used (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_schedule(interaction: discord.Interaction, host: str, time: str, flight_info: str, aircraft_type: str, flight_code: str):
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    start_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)

    event = await interaction.guild.create_scheduled_event(
        name=f"Jet2 Flight - {flight_code}",
        description=f"**Host:** {host}\n**Aircraft:** {aircraft_type}\n**Flight Schedule:** {flight_info}\n**Flight Code:** {flight_code}",
        start_time=start_time,
        end_time=end_time,
        entity_type=discord.EntityType.external,
        location="Jet2 Airport",
        privacy_level=discord.PrivacyLevel.guild_only
    )

    await interaction.response.send_message(f"Flight event created for **{flight_code}**. [View Event]({event.url})", ephemeral=False)

@bot.tree.command(name="flight_announce", description="Announce a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(
    time="Flight time",
    flight_info="Flight info (e.g. Bournemouth -> Punta Cana)",
    aircraft="Aircraft used",
    airport_link="Airport link",
    flight_code="Flight code",
    channel_id="Channel ID to send announcement"
)
async def flight_announce(interaction: discord.Interaction, time: str, flight_info: str, aircraft: str, airport_link: str, flight_code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return await interaction.response.send_message("Invalid channel ID.", ephemeral=True)

    embed = discord.Embed(
        title=":airplane: FLIGHT ANNOUNCEMENT",
        description=f"There is a flight today at {time}. We will be operating the {aircraft}.\nThis flight will be from {flight_info}.\n\nWe hope to see you attend **{flight_code}**!",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send("@everyone")
    await channel.send(embed=embed)
    await interaction.response.send_message("Flight announced.", ephemeral=True)

@bot.tree.command(name="infract", description="Discipline a staff member", guild=discord.Object(id=guild_id))
@app_commands.describe(
    user="User to discipline",
    reason="Reason for infraction",
    type="Type of action (Termination / Infraction / Demotion)",
    demotion_role="(Optional) Role if demotion"
)
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: discord.Role = None):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("This command can only be used in the designated channel.", ephemeral=True)
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    embed = discord.Embed(
        title="Infraction Notice",
        description=f"**Infracted By:** {interaction.user.mention}\n**User:** {user.mention}\n**Type:** {type}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Infraction logged.", ephemeral=True)

@bot.tree.command(name="promote", description="Promote a staff member", guild=discord.Object(id=guild_id))
@app_commands.describe(
    user="User to promote",
    promotion_to="New role or title",
    reason="Reason for promotion"
)
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("This command can only be used in the designated channel.", ephemeral=True)
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    embed = discord.Embed(
        title="Promotion Notice",
        description=f"**Promoted By:** {interaction.user.mention}\n**User:** {user.mention}\n**Promotion To:** {promotion_to}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Promotion logged.", ephemeral=True)

@bot.tree.command(name="flight_log", description="Log a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(
    user="User who hosted the flight",
    evidence="Image evidence of flight",
    session_date="Date of the session",
    flight_code="Flight code"
)
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str, flight_code: str):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("This command can only be used in the designated channel.", ephemeral=True)
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    if not evidence.content_type.startswith("image"):
        return await interaction.response.send_message("Please upload a valid image as evidence.", ephemeral=True)

    embed = discord.Embed(
        title="Flight Log",
        description=f"**Logged By:** {interaction.user.mention}\n**User:** {user.mention}\n**Flight Code:** {flight_code}\n**Session Date:** {session_date}",
        color=0x8b2828
    )
    embed.set_image(url=evidence.url)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Flight log submitted.", ephemeral=True)

bot.run(token)
