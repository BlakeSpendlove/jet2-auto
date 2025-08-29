import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from discord.utils import utcnow
from discord import ui, Interaction, ButtonStyle
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
AFFILIATE_CHANNEL_ID = int(os.getenv("AFFILIATE_CHANNEL_ID"))
BANNER_URL = os.getenv("BANNER_URL")
STAFF_FLIGHT_ID = os.getenv("STAFF_FLIGHT_ID")
FR3161_GAME_LINK = os.getenv("FR3161_GAME_LINK")
FR5519_GAME_LINK = os.getenv("FR5519_GAME_LINK")
FR4927_GAME_LINK = os.getenv("FR4927_GAME_LINK")

intents = discord.Intents.default()
intents.presences = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)  # ✅ create bot first
tree = bot.tree  # ✅ now this works

JET2_DARK_RED = discord.Color.from_str("#193e75")

# Define available routes in one place
ROUTES = [ 
    {
        "code": "FR3161",
        "text": "Pafos International Airport → Bristol Airport",
        "env": "FR3161_GAME_LINK"
    },
    {
        "code": "FR5519",
        "text": "Krakow Airport → Bristol Airport",
        "env": "FR5519_GAME_LINK"
    },
        {
        "code": "FR4927",
        "text": "Manchester Airport → Pafos International Airport",
        "env": "FR4927_GAME_LINK"
    }
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="RYR Infractions"
    )
    await bot.change_presence(activity=activity)
    print("Status set to 'Watching Flight Creations'")

    # Sync commands
    await bot.tree.sync(guild=guild)

# Permissions check
def is_scheduler():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == SCHEDULE_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)

# On ready
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user} and commands synced.")

# Ping command
@tree.command(name="ping", description="Check bot responsiveness", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# ConfirmView for buttons
class ConfirmView(ui.View):
    def __init__(self, on_confirm, on_cancel=None, timeout=60):
        super().__init__(timeout=timeout)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    @ui.button(label="✅ Confirm", style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.on_confirm(interaction)
        self.stop()

    @ui.button(label="❌ Cancel", style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        if self.on_cancel:
            await self.on_cancel(interaction)
        else:
            await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        self.stop()
        
# Create a flight event
@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    start_date="Start date in DD/MM/YYYY",
    start_time="Start time in 24h format HH:MM",
    aircraft="Aircraft type (e.g. B737-800)",
    route="Select a route"
)
@app_commands.choices(route=[
    app_commands.Choice(name=f"{r['code']} {r['text']}", value=f"{r['code']}|{r['text']}") for r in ROUTES
])
@is_scheduler()
async def flight_create(interaction: discord.Interaction, start_date: str, start_time: str, aircraft: str, route: app_commands.Choice[str]):
    try:
        flight_code, route_text = route.value.split("|", 1)
        start_dt_naive = datetime.strptime(f"{start_date} {start_time}", "%d/%m/%Y %H:%M")
        start_dt = start_dt_naive.replace(tzinfo=utcnow().tzinfo)
        end_dt = start_dt + timedelta(hours=1)

        member = interaction.user
        role = discord.utils.get(member.roles, id=int(SCHEDULE_ROLE_ID))
        if not role:
            await interaction.response.send_message("❌ You are not authorized to create a flight event.", ephemeral=True)
            return

        # Flight preview embed
        embed = discord.Embed(title="✈️ Flight Event Confirmation", color=discord.Color.blue())
        embed.add_field(name="Flight Code", value=flight_code, inline=True)
        embed.add_field(name="Route", value=route_text, inline=True)
        embed.add_field(name="Aircraft", value=aircraft, inline=True)
        embed.add_field(name="Date & Time", value=start_dt.strftime("%d/%m/%Y %H:%M"), inline=False)
        embed.add_field(name="Host", value=member.mention, inline=False)
        embed.set_footer(text="Press Confirm to create this flight event.")

        async def create_event(inter_confirm: Interaction):
            guild = interaction.guild
            event = await guild.create_scheduled_event(
                name=f"Flight {flight_code} - {route_text}",
                start_time=start_dt,
                end_time=end_dt,
                description=(
                    f"Aircraft: {aircraft}\n"
                    f"Route: {route_text}\n"
                    f"Flight Code: {flight_code}\n"
                    f"Host: {member.mention}"
                ),
                privacy_level=discord.PrivacyLevel.guild_only,
                entity_type=discord.EntityType.external,
                location="Online / Virtual"
            )

            # Edit DM embed for staff announcement step
            embed2 = discord.Embed(
                title="✅ Flight Created!",
                description="Flight created successfully.\n\nWould you like to send the Staff Announcement?",
                color=discord.Color.orange()
            )
            view2 = ConfirmView(on_confirm=lambda i: send_staff_announcement(i, event, inter_confirm.message))
            await inter_confirm.message.edit(embed=embed2, view=view2)

            # Reminder task
            notify_time = start_dt - timedelta(minutes=20)
            @tasks.loop(seconds=30)
            async def notify_host():
                if datetime.now(tz=start_dt.tzinfo) >= notify_time:
                    try:
                        await member.send(f"Reminder: Your flight '{flight_code}' starts at {start_dt.strftime('%H:%M')}! Ensure you now run the /flight_briefing command and start briefing. Failure to do so will result in an infraction.")
                    except:
                        pass
                    notify_host.stop()
            notify_host.start()

        async def send_staff_announcement(inter_staff: Interaction, event, dm_message):
            try:
                staff_channel = await bot.fetch_channel(int(STAFF_FLIGHT_ID))
                staff_msg = await staff_channel.send(
                    content=f"**FLIGHT {flight_code}**\n@everyone\n\n{event.url}\n\n**Please confirm your attendance below.**",
                    allowed_mentions=discord.AllowedMentions(everyone=True)
                )
                await staff_msg.add_reaction("🟩")
                await staff_msg.add_reaction("🟨")
                await staff_msg.add_reaction("🟥")
                # Edit DM embed to final confirmation
                embed3 = discord.Embed(
                    title="✅ Flight Created & Staff Announcement Sent!",
                    description=f"Flight {flight_code} has been created and the staff announcement has been sent.",
                    color=discord.Color.green()
                )
                await dm_message.edit(embed=embed3, view=None)
                await inter_staff.response.send_message("📢 Staff announcement sent.", ephemeral=True)
            except Exception as e:
                await inter_staff.response.send_message(f"⚠️ Could not send staff announcement: {e}", ephemeral=True)

        view = ConfirmView(on_confirm=create_event)
        await member.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Flight preview sent to your DMs.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# Flight host announcement
@tree.command(name="flight_host", description="Send flight announcement", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    aircraft="Aircraft type (e.g. B737-800)",
    route="Select a route"
)
@app_commands.choices(route=[
    app_commands.Choice(name=f"{r['code']} {r['text']}", value=f"{r['code']}|{r['text']}") for r in ROUTES
])
@is_scheduler()
async def flight_host(interaction: discord.Interaction, aircraft: str, route: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=False)
    guild = interaction.guild

    # Extract flight_code and route_text
    flight_code, route_text = route.value.split("|", 1)

    events = await guild.fetch_scheduled_events()
    matching = [e for e in events if flight_code in e.name]

    if not matching:
        await interaction.followup.send(f"❌ No scheduled flight found with `{flight_code}`", ephemeral=True)
        return

    event = matching[0]

    # Game link pulled from env var e.g. FR4813_GAME_LINK
    game_link = os.getenv(f"{flight_code}_GAME_LINK", "https://www.roblox.com")

    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=(
            f"✈️ **Route:** {route_text}\n"
            f"🛩️ **Aircraft:** {aircraft}\n"
            f"👨‍✈️ **Host:** {interaction.user.mention}\n\n"
            "📢 Please check in, complete bag drop, and proceed through security.\n"
            "🎮 Join the airport below."
        ),
        color=JET2_DARK_RED,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🕹️ Game", value=f"[Game Link]({game_link})", inline=False)
    embed.add_field(name="📅 Event", value=f"[Click to View Event]({event.url})", inline=False)
    embed.set_footer(text="Flight Announcements")
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    await interaction.followup.send(
        content="@everyone Flight is now boarding!",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )

# Add an affiliate
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

# Remove an affiliate
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

# Custom embed sender
@tree.command(name="embed", description="Send a custom embed from Discohook JSON", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(json_code="Embed JSON code from Discohook")
@is_scheduler()
async def embed(interaction: discord.Interaction, json_code: str):
    try:
        data = json.loads(json_code)
        emb = discord.Embed.from_dict(data["embeds"][0])
        await interaction.channel.send(embed=emb)
        await interaction.response.send_message("✅ Embed sent.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Invalid JSON: {e}", ephemeral=True)

# DM a user with a Discohook embed
from discord import app_commands, Interaction, User, Embed
import discord
import json

@tree.command(name="dm", description="Send a JSON-formatted embed to a user.")
@app_commands.describe(
    user="User to DM",
    json_embed="Valid embed JSON structure (excluding outer curly braces)"
)
async def dm(interaction: Interaction, user: User, json_embed: str):
    try:
        # Attempt to parse the embed JSON
        embed_data = json.loads("{" + json_embed + "}")
        embed = Embed().from_dict(embed_data["embeds"][0]) if "embeds" in embed_data else None

        if not embed:
            await interaction.response.send_message("❌ No embed content found.", ephemeral=True)
            return

        # Send embed as a DM
        await user.send(embed=embed)
        await interaction.response.send_message(f"✅ Embed sent to {user.mention}.", ephemeral=True)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Invalid JSON or DM failed: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Invalid JSON or DM failed: {e}", ephemeral=True)


# Run the bot
bot.run(TOKEN)
