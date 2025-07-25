@tree.command(name="flight_create", description="Create a flight event")
@app_commands.guilds(discord.Object(id=GUILD_ID))
@is_whitelisted()
@app_commands.describe(
    route="Flight route, e.g. Manchester to Alicante",
    date="Date (DD/MM/YYYY)",
    time="Start time (24-hour HH:MM)",
    aircraft="Aircraft type",
    flight_code="Flight code",
    host="Select the host"
)
async def flight_create(interaction: discord.Interaction, route: str, date: str, time: str, aircraft: str, flight_code: str, host: discord.Member):
    try:
        guild = interaction.guild
        start_dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        
        # Create a scheduled event on the guild
        event = await guild.create_scheduled_event(
            name=f"Flight {flight_code} - {route}",
            start_time=start_dt,
            end_time=end_dt,
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.external,
            entity_metadata=discord.ScheduledEventEntityMetadata(location="Online"),
            description=f"Aircraft: {aircraft}\nHost: {host.display_name}",
        )
        
        embed = discord.Embed(title="Flight Created", color=0x2b2d31)
        embed.add_field(name="Route", value=route, inline=False)
        embed.add_field(name="Aircraft", value=aircraft, inline=False)
        embed.add_field(name="Flight Code", value=flight_code, inline=False)
        embed.add_field(name="Host", value=host.mention, inline=False)
        embed.add_field(name="Event", value=f"[Click here to view the event]({event.url})", inline=False)
        embed.set_footer(text=f"ID: {generate_id()}")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)
