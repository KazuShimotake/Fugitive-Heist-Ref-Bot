import discord
from discord.ext import commands
import asyncio
import datetime

TOKEN = 'YOUR_TOKEN_HERE'
GUILD_ID = YOUR_SERVER_ID_HERE

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

team1_name = "Team 1"
team2_name = "Team 2"
team1_score = 0
team2_score = 0
team1_role = "attacking"
team2_role = "defending"
round_active = False
round_task = None
round_start_time = None
round_duration_minutes = 55
photo_scores = {}
paused = False
paused_time = 0

def get_attacking_team():
    return team1_name if team1_role == "attacking" else team2_name

def get_defending_team():
    return team1_name if team1_role == "defending" else team2_name

async def delete_global_commands():
    print("Deleting global commands...")
    commands_list = bot.tree.get_commands()
    for cmd in commands_list:
        if cmd.guild_id is None:
            await bot.tree.remove_command(cmd.name)
            print(f"Deleted global command: {cmd.name}")
    await bot.tree.sync()

# ====== SLASH COMMANDS ======
@bot.tree.command(name="set_teams", description="Set team names.", guild=discord.Object(id=GUILD_ID))
async def set_teams(interaction: discord.Interaction, team1: str, team2: str):
    global team1_name, team2_name
    team1_name = team1
    team2_name = team2
    await interaction.response.send_message(f"Teams set: {team1_name} vs {team2_name}.")

@bot.tree.command(name="start_round", description="Start a new round without resetting scores.", guild=discord.Object(id=GUILD_ID))
async def start_round(interaction: discord.Interaction, minutes: int = 55):
    global round_active, round_start_time, round_duration_minutes, round_task, paused, paused_time
    if round_active:
        await interaction.response.send_message("A round is already active.", ephemeral=True)
        return
    round_start_time = datetime.datetime.utcnow()
    round_duration_minutes = minutes
    round_active = True
    paused = False
    paused_time = 0
    await interaction.response.send_message("Round started!")
    round_task = bot.loop.create_task(round_timer(interaction.channel, minutes))

@bot.tree.command(name="stop_round", description="Stop the current round.", guild=discord.Object(id=GUILD_ID))
async def stop_round(interaction: discord.Interaction):
    global round_active, round_task
    if not round_active:
        await interaction.response.send_message("No round is active.", ephemeral=True)
        return
    round_active = False
    if round_task:
        round_task.cancel()
    await interaction.response.send_message("Round stopped manually.")

@bot.tree.command(name="pause_timer", description="Pause the round timer.", guild=discord.Object(id=GUILD_ID))
async def pause_timer(interaction: discord.Interaction):
    global paused, paused_time, round_start_time
    if not round_active:
        await interaction.response.send_message("No active round to pause.", ephemeral=True)
        return
    if paused:
        await interaction.response.send_message("Timer is already paused.", ephemeral=True)
        return
    paused = True
    paused_time = (datetime.datetime.utcnow() - round_start_time).total_seconds()
    await interaction.response.send_message("Timer paused.")

@bot.tree.command(name="resume_timer", description="Resume the paused timer.", guild=discord.Object(id=GUILD_ID))
async def resume_timer(interaction: discord.Interaction):
    global paused, round_start_time
    if not paused:
        await interaction.response.send_message("Timer is not paused.", ephemeral=True)
        return
    paused = False
    round_start_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=paused_time)
    await interaction.response.send_message("Timer resumed.")

@bot.tree.command(name="extend_round", description="Extend the current round.", guild=discord.Object(id=GUILD_ID))
async def extend_round(interaction: discord.Interaction, extra_minutes: int):
    global round_duration_minutes
    round_duration_minutes += extra_minutes
    await interaction.response.send_message(f"Round extended by {extra_minutes} minutes.")

@bot.tree.command(name="flip_roles", description="Flip attacking and defending roles.", guild=discord.Object(id=GUILD_ID))
async def flip_roles(interaction: discord.Interaction):
    global team1_role, team2_role
    team1_role, team2_role = team2_role, team1_role
    await interaction.response.send_message(f"Roles flipped: {team1_name} is now {team1_role}, {team2_name} is now {team2_role}.")

@bot.tree.command(name="score", description="Show current scores.", guild=discord.Object(id=GUILD_ID))
async def score(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏆 Scores:\n{team1_name}: {team1_score} points\n{team2_name}: {team2_score} points")

@bot.tree.command(name="reset_scores", description="Reset all scores to zero.", guild=discord.Object(id=GUILD_ID))
async def reset_scores(interaction: discord.Interaction):
    global team1_score, team2_score
    team1_score = 0
    team2_score = 0
    await interaction.response.send_message("Scores have been reset.")

@bot.tree.command(name="subtract_points", description="Subtract points from a team.", guild=discord.Object(id=GUILD_ID))
async def subtract_points(interaction: discord.Interaction, team: str, points: int):
    global team1_score, team2_score
    team = team.lower()
    if team == team1_name.lower():
        team1_score -= points
        await interaction.response.send_message(f"Subtracted {points} points from {team1_name}.")
    elif team == team2_name.lower():
        team2_score -= points
        await interaction.response.send_message(f"Subtracted {points} points from {team2_name}.")
    else:
        await interaction.response.send_message("Team name not recognized.", ephemeral=True)

@bot.tree.command(name="add_points", description="Add points to a team.", guild=discord.Object(id=GUILD_ID))
async def add_points(interaction: discord.Interaction, team: str, points: int):
    global team1_score, team2_score
    team = team.lower()
    if team == team1_name.lower():
        team1_score += points
        await interaction.response.send_message(f"Added {points} points to {team1_name}.")
    elif team == team2_name.lower():
        team2_score += points
        await interaction.response.send_message(f"Added {points} points to {team2_name}.")
    else:
        await interaction.response.send_message("Team name not recognized.", ephemeral=True)

@bot.tree.command(name="round_time_left", description="Show time left in the current round.", guild=discord.Object(id=GUILD_ID))
async def round_time_left(interaction: discord.Interaction):
    if not round_active or round_start_time is None:
        await interaction.response.send_message("No round is active.", ephemeral=True)
        return
    now = datetime.datetime.utcnow()
    elapsed = (now - round_start_time).total_seconds()
    total = round_duration_minutes * 60
    remaining = total - elapsed
    if paused:
        remaining = total - paused_time
    if remaining <= 0:
        await interaction.response.send_message("The round is over!", ephemeral=True)
    else:
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        await interaction.response.send_message(f"⏳ {minutes} minutes and {seconds} seconds remaining.")

@bot.tree.command(name="check_timer", description="Quickly check the timer.", guild=discord.Object(id=GUILD_ID))
async def check_timer(interaction: discord.Interaction):
    await round_time_left(interaction)

@bot.tree.command(name="status", description="Show full round status.", guild=discord.Object(id=GUILD_ID))
async def status(interaction: discord.Interaction):
    if not round_active:
        await interaction.response.send_message("⏸ No round is currently active.")
        return
    now = datetime.datetime.utcnow()
    elapsed = (now - round_start_time).total_seconds()
    total = round_duration_minutes * 60
    remaining = total - elapsed
    if paused:
        remaining = total - paused_time
        pause_note = "⏸ Paused"
    else:
        pause_note = "▶️ Active"
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    await interaction.response.send_message(
        f"🏁 **Round Status:** {pause_note}\n"
        f"⏳ **Time Left:** {minutes} minutes, {seconds} seconds\n"
        f"🥷 **Attacking Team:** {get_attacking_team()}\n"
        f"👮‍♂️ **Defending Team:** {get_defending_team()}\n"
        f"🏆 **Scores:** {team1_name}: {team1_score}, {team2_name}: {team2_score}"
    )

@bot.tree.command(name="help", description="List all available commands.", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Available Commands:**\n"
        "/set_teams team1 team2\n"
        "/start_round [minutes]\n"
        "/stop_round\n"
        "/pause_timer\n"
        "/resume_timer\n"
        "/extend_round extra_minutes\n"
        "/flip_roles\n"
        "/score\n"
        "/reset_scores\n"
        "/subtract_points team points\n"
        "/add_points team points\n"
        "/round_time_left\n"
        "/check_timer\n"
        "/status\n"
        "/help"
    )
    await interaction.response.send_message(help_text, ephemeral=True)

async def round_timer(channel, minutes):
    global round_active
    for _ in range(minutes // 5):
        await asyncio.sleep(300)
        if not paused:
            await channel.send(f"🏆 Auto Score Update:\n{team1_name}: {team1_score} points\n{team2_name}: {team2_score} points")
    if minutes % 5 != 0:
        await asyncio.sleep((minutes % 5) * 60)
    round_active = False
    await channel.send("Round ended!")

@bot.event
async def on_raw_reaction_add(payload):
    global team1_score, team2_score
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = str(payload.emoji)

    if message.id in photo_scores:
        if emoji != '❌':
            return

    author_name = message.author.display_name if hasattr(message.author, 'display_name') else message.author.name

    if emoji == '💎':
        team = get_attacking_team()
        if team == team1_name:
            team1_score += 10
        else:
            team2_score += 10
        photo_scores[message.id] = (team, 10)
        await channel.send(f"💎 Extraction scored by {author_name}! (+10 points to their team)")

    elif emoji == '💲':
        team = get_defending_team()
        if team == team1_name:
            team1_score += 6
        else:
            team2_score += 6
        photo_scores[message.id] = (team, 6)
        await channel.send(f"💲 Recovery scored by {author_name}! (+6 points to their team)")

    elif emoji == '❌':
        if message.id in photo_scores:
            team, points = photo_scores.pop(message.id)
            if team == team1_name:
                team1_score -= points
            else:
                team2_score -= points
            await channel.send(f"❌ Points removed from {team}! (-{points} points)")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is fully ready!")
    await delete_global_commands()
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"❌ Failed to sync commands to guild: {e}")

    guild_obj = bot.get_guild(GUILD_ID)
    if guild_obj:
        for channel in guild_obj.text_channels:
            if channel.permissions_for(guild_obj.me).send_messages:
                await channel.send("🚨 The Fugitive Heist Referee Bot has activated!")
                break

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        print(f"GLOBAL: Slash command detected: /{interaction.command.name} by {interaction.user}")

bot.run(TOKEN)
