import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot is ready. Logged in as {bot.user}")

def is_whitelisted():
    def predicate(interaction: discord.Interaction):
        return interaction.user.get_role(WHITELIST_ROLE_ID) is not None
    return app_commands.check(predicate)

@tree.command(name="test", description="Test if the bot is working", guild=discord.Object(id=GUILD_ID))
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is working and slash commands are active!")

@tree.command(name="affiliate_add", description="Add an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(company="Company name", discord_link="Discord invite", roblox_group="Roblox group link")
@is_whitelisted()
async def affiliate_add(interaction: discord.Interaction, company: str, discord_link: str, roblox_group: str):
    embed = discord.Embed(title="🤝 New Affiliate Added", color=0xE74C3C)
    embed.add_field(name="Company", value=f"**{company}**", inline=False)
    embed.add_field(name="Discord", value=f"[🔗 Discord Link]({discord_link})", inline=False)
    embed.add_field(name="Roblox Group", value=f"[🔗 Roblox Group]({roblox_group})", inline=False)
    embed.set_image(url="https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png")
    embed.set_footer(text=datetime.now().strftime("%d/%m/%Y"))
    await interaction.response.send_message(embed=embed)

@tree.command(name="affiliate_remove", description="Remove an affiliate", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(company="Company name to remove")
@is_whitelisted()
async def affiliate_remove(interaction: discord.Interaction, company: str):
    await interaction.response.send_message(f"Affiliate **{company}** removed (placeholder logic).")

@tree.command(name="embed", description="Send embed from Discohook JSON", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(json_input="Paste raw Discohook JSON")
@is_whitelisted()
async def embed(interaction: discord.Interaction, json_input: str):
    try:
        import json
        parsed = json.loads(json_input)
        embed = discord.Embed.from_dict(parsed["embeds"][0])
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error parsing JSON: {e}")

@tree.command(name="flight_create", description="Create a flight event", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(route="e.g. MAN -> PMI", start_time="e.g. 18:00", aircraft="e.g. B737-800", flight_code="e.g. LS8800")
@is_whitelisted()
async def flight_create(interaction: discord.Interaction, route: str, start_time: str, aircraft: str, flight_code: str):
    await interaction.guild.create_scheduled_event(
        name=f"Flight {flight_code}",
        description=f"**Route:** {route}\n**Time:** {start_time}\n**Aircraft:** {aircraft}\n**Host:** {interaction.user.mention}",
        start_time=discord.utils.utcnow(),  # Placeholder
        end_time=discord.utils.utcnow(),    # Placeholder
        location="Airport",
        entity_type=discord.EntityType.external
    )
    await interaction.response.send_message(f"Flight event for **{flight_code}** created!")

@tree.command(name="flight_host", description="Announce a flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(flight_code="Flight code", aircraft="Aircraft", route="Route")
@is_whitelisted()
async def flight_host(interaction: discord.Interaction, flight_code: str, aircraft: str, route: str):
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("Announcement channel not found.")
        return

    embed = discord.Embed(
        title="**✈️ FLIGHT SCHEDULED**",
        description=f"A new flight has been scheduled!\n\n"
                    f"📆 **Date:** {datetime.now().strftime('%d/%m/%Y')}\n"
                    f"🕓 **Time:** *(see event)*\n"
                    f"📍 **Route:** {route}\n"
                    f"🔢 **Flight Code:** {flight_code}\n"
                    f"✈️ **Aircraft:** {aircraft}",
        color=0x3498DB
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png")
    await channel.send(embed=embed)
    await interaction.response.send_message("Flight announcement sent.")

bot.run(TOKEN)
