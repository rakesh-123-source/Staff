import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
from flask import Flask, request, render_template_string
from threading import Thread
import re
import firebase_admin
from firebase_admin import credentials, firestore
import secrets
from datetime import datetime
app = Flask(__name__)
SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;600&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Montserrat', sans-serif;
      background: {{ bgColor }};
      background: linear-gradient(135deg, {{ bgColor }}, #27293d);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    .container {
      text-align: center;
      padding: 40px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 15px;
      box-shadow: 0 0 20px rgba(0,0,0,0.7);
      max-width: 600px;
      margin: 20px;
    }
    h1 {
      font-size: 3rem;
      margin-bottom: 20px;
      color: #5cb85c;
    }
    p {
      font-size: 1.3rem;
      margin-bottom: 20px;
    }
    .cool-button {
      display: inline-block;
      padding: 12px 25px;
      background: #5cb85c;
      color: #fff;
      border: none;
      border-radius: 50px;
      text-decoration: none;
      font-size: 1rem;
      transition: background 0.3s ease, transform 0.2s ease;
    }
    .cool-button:hover {
      background: #4cae4c;
      transform: scale(1.05);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    {% if buttonText and buttonLink %}
      <a href="{{ buttonLink }}" class="cool-button">{{ buttonText }}</a>
    {% endif %}
  </div>
</body>
</html>
"""
ERROR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;600&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Montserrat', sans-serif;
      background: {{ bgColor }};
      background: linear-gradient(135deg, {{ bgColor }}, #27293d);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    .container {
      text-align: center;
      padding: 40px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 15px;
      box-shadow: 0 0 20px rgba(0,0,0,0.7);
      max-width: 600px;
      margin: 20px;
    }
    h1 {
      font-size: 3rem;
      margin-bottom: 20px;
      color: #d9534f;
    }
    p {
      font-size: 1.3rem;
      margin-bottom: 20px;
    }
    .cool-button {
      display: inline-block;
      padding: 12px 25px;
      background: #d9534f;
      color: #fff;
      border: none;
      border-radius: 50px;
      text-decoration: none;
      font-size: 1rem;
      transition: background 0.3s ease, transform 0.2s ease;
    }
    .cool-button:hover {
      background: #c9302c;
      transform: scale(1.05);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    {% if buttonText and buttonLink %}
      <a href="{{ buttonLink }}" class="cool-button">{{ buttonText }}</a>
    {% endif %}
  </div>
</body>
</html>
"""
@app.route('/')
def home_route():
    return "Bot is running!"
@app.route('/apply_staff', methods=['POST'])
def apply_staff():
    auth_token = request.form.get('auth_token')
    discord_id = request.form.get('discord_id')
    q1 = request.form.get('q1')
    q2 = request.form.get('q2')
    q3 = request.form.get('q3')
    q4 = request.form.get('q4')
    q5 = request.form.get('q5')
    q6 = request.form.get('q6')
    q7 = request.form.get('q7')
    q8 = request.form.get('q8')
    q9 = request.form.get('q9')
    q10 = request.form.get('q10')
    if not all([auth_token, discord_id, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]):
        return render_template_string(ERROR_HTML,
                                      title="Error",
                                      message="Please fill out all fields.",
                                      bgColor="#d9534f",
                                      buttonText="Return Home",
                                      buttonLink="https://gamersdojo.netlify.app/appication"), 400
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(discord_id))
    doc = doc_ref.get()
    if not doc.exists:
        return render_template_string(ERROR_HTML,
                                      title="Error",
                                      message="No pending application record found. Please get an application token from the Discord bot first.",
                                      bgColor="#d9534f",
                                      buttonText="Return Home",
                                      buttonLink="https://gamersdojo.netlify.app/appication"), 400
    record = doc.to_dict()
    stored_token = record.get("auth_token")
    if stored_token != auth_token:
        return render_template_string(ERROR_HTML,
                                      title="Error",
                                      message="The provided token does not match our records.",
                                      bgColor="#d9534f",
                                      buttonText="Return Home",
                                      buttonLink="https://gamersdojo.netlify.app/appication"), 400
    application_data = {
        "auth_token": auth_token,
        "discord_id": discord_id,
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "q4": q4,
        "q5": q5,
        "q6": q6,
        "q7": q7,
        "q8": q8,
        "q9": q9,
        "q10": q10,
        "status": "submitted",
        "submitted_at": datetime.utcnow().isoformat()
    }
    doc_ref.set(application_data)
    future = asyncio.run_coroutine_threadsafe(
        notify_application(application_data),
        bot.loop
    )
    try:
        future.result()
    except Exception as e:
        print("Error notifying Discord:", e)

    return render_template_string(SUCCESS_HTML,
                                  title="Success!",
                                  message="Your application has been submitted successfully!",
                                  bgColor="#5cb85c",
                                  buttonText="See Applicatin",
                                  buttonLink="https://discord.com/channels/1270760786817450086/1348759783184011324"), 200
def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
cred = credentials.Certificate("server_staffs.json") 
firebase_admin.initialize_app(cred, name="firebase_app1")
db = firestore.client(app=firebase_admin.get_app("firebase_app1"))
APPLICATIONS_COLLECTION = "applications"
def save_panel_id(panel_id: str):
    db.collection("panels").document("current").set({
        "panel_id": panel_id,
        "started_at": datetime.utcnow().isoformat()
    })
def get_panel_id() -> str:
    doc = db.collection("panels").document("current").get()
    if doc.exists:
        return doc.to_dict().get("panel_id")
    return None
def clear_panel_id():
    db.collection("panels").document("current").delete()
GUILD_ID = 1270760786817450086  
APPLICATIONS_CHANNEL_ID = 1348759783184011324  
PANEL_CHANNEL_ID = 1330801025761808416
PANEL_CHANNEL_ID2 = 1335334770980159579
NUM_QUESTIONS = 10
QUESTIONS = [
    "What is your time zone?",
    "Why do you want to join our staff team?",
    "Have you ever moderated before?",
    "Do you know how to use our moderation bots?",
    "Do you agree with our server staff rules?",
    "What relevant skills do you have that would benefit our staff team?",
    "How would you handle a conflict between community members?",
    "What strategies would you use to maintain our server?",
    "Can you describe a situation where you successfully resolved a challenging issue online?",
    "What are your expectations from our staff team, and how do you see yourself contributing?"
]
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
STATUS_FILE = "status.json"
class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="View Application", url="https://gamersdojo.netlify.app/appication", style=discord.ButtonStyle.url))
def user_has_application(user_id: int) -> bool:
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        if data.get("status") in ("pending", "in_progress", "submitted", "selected"):
            return True
    return False
def create_application_record(user_id: int, auth_token: str):
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    doc_ref.set({
        "status": "pending",
        "auth_token": auth_token,
        "generated_at": datetime.utcnow().isoformat()
    })
def update_application_record(user_id: int, status: str, application_text: str = None):
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    update_data = {"status": status}
    if application_text is not None:
        update_data["application_text"] = application_text
    doc_ref.update(update_data)
async def process_application_in_channel(interaction: discord.Interaction):
    user = interaction.user

    if user_has_application(user.id):
        await interaction.response.send_message(
            "❌ You have already received an application token or are in the process of applying.",
            ephemeral=True
        )
        return

    # Generate a unique token and create the application record in Firebase
    auth_token = secrets.token_hex(4)
    create_application_record(user.id, auth_token)

    # Build the embed with instructions
    embed = discord.Embed(
        title="📝 Staff Application Token",
        description=(
            f"Hello {user.name},\n\n"
            "Thank you for your interest in joining Gamer's Dojo staff!\n\n"
            "Please follow these steps:\n"
            "**Step 1:** Click the **View Application** button below to open the online application form.\n"
            "**Step 2:** Enter the following unique token into the form:\n"
            f"`{auth_token}`\n\n"
            "This token is one-time use. Keep it confidential and contact an admin if you have any issues."
        ),
        color=discord.Color.blue()
    )

    # Set a thumbnail based on the user's avatar
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    else:
        embed.set_thumbnail(url=user.default_avatar.url)
    embed.set_footer(text="Gamer's Dojo - Best of luck with your application!")

    view = ApplicationView()

    # Send the embed and token as ephemeral messages in the channel
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await interaction.followup.send(f"Token: `{auth_token}`", ephemeral=True)

    # Also send the token in DMs so the user can retrieve it later if needed
    try:
        await user.send(
            f"Hello {user.name}, here is your application token: `{auth_token}`.\n"
            "Keep it safe and use it on the application form at your convenience."
        )
    except Exception as e:
        print(f"Failed to send DM to {user.name}: {e}")

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.green, custom_id="panel_apply_id")
    async def apply_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Ensure the button is not used in DMs
        if interaction.guild is None:
            await interaction.response.send_message("This command cannot be used in DMs.", ephemeral=True)
            return

        # Process the application with both an ephemeral message in channel and a DM
        await process_application_in_channel(interaction)

async def notify_application(application_data):
    guild = bot.get_guild(GUILD_ID)
    discord_id = application_data.get("discord_id")
    try:
        member = guild.get_member(int(discord_id))
    except Exception:
        member = None
    applicant_str = member.mention if member else f"Discord ID: {discord_id}"
    description = f"> 📝 **New Application**\n> Applicant: {applicant_str}\n\n"
    answers = [
        application_data.get("q1"),
        application_data.get("q2"),
        application_data.get("q3"),
        application_data.get("q4"),
        application_data.get("q5"),
        application_data.get("q6"),
        application_data.get("q7"),
        application_data.get("q8"),
        application_data.get("q9"),
        application_data.get("q10")
    ]
    for i in range(NUM_QUESTIONS):
        description += f"{i+1}. {QUESTIONS[i]}\n> Answer: {answers[i]}\n** **\n"
    description += "\n> **Vote with ✅ or ❌ **"
    embed_app = discord.Embed(
        description=description,
        color=41983
    )
    embed_app.set_footer(text="From Gamer's Dojo by ÐRΛ✘ITY")
    if member:
        if member.avatar:
            embed_app.set_thumbnail(url=member.avatar.url)
        else:
            embed_app.set_thumbnail(url=member.default_avatar.url)
    else:
        embed_app.set_thumbnail(url="https://via.placeholder.com/150")
    app_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
    if app_channel:
        sent_msg = await app_channel.send(embed=embed_app)
        await sent_msg.add_reaction("✅")
        await sent_msg.add_reaction("❌")
    else:
        print("Applications channel not found.")
@bot.tree.command(name="start_panel", description="Creates a staff application panel.(admin only)")
async def start_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    embed = discord.Embed(
        title="📋 Staff Application Panel",
        description="Applications are now OPEN!\nClick the button below to apply for a staff position.",
        color=discord.Color.green()
    )
    embed.set_footer(text="Gamer's Dojo - Application Panel")
    channel = bot.get_channel(PANEL_CHANNEL_ID)
    if not channel:
        return await interaction.response.send_message("Panel channel not found.", ephemeral=True)
    panel_msg = await channel.send(embed=embed, view=PanelView())
    save_panel_id(panel_msg.id)
    await interaction.response.send_message("Staff application panel started.", ephemeral=True)

@bot.tree.command(name="end_applications", description="Ends the current staff applications.(admin only)")
async def end_applications(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    panel_id = get_panel_id()
    if not panel_id:
        return await interaction.response.send_message("No active panel found.", ephemeral=True)
    channel = bot.get_channel(PANEL_CHANNEL_ID)
    if not channel:
        return await interaction.response.send_message("Panel channel not found.", ephemeral=True)
    try:
        panel_msg = await channel.fetch_message(panel_id)
        embed = panel_msg.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "📋 Staff Application Panel - CLOSED"
        embed.description = "Applications are now CLOSED. Thank you for your interest!"
        await panel_msg.edit(embed=embed,view=None)
        clear_panel_id()
        await interaction.response.send_message("Applications have been ended.", ephemeral=True)
    except Exception as e:
        print("Error ending applications:", e)
        await interaction.response.send_message("Error ending applications.", ephemeral=True)
@bot.tree.command(name="set_status", description="Sets the bot's status message (admin only)")
@app_commands.describe(
    status="The status message to display",
    type="The type of status to display"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Playing", value="playing"),
    app_commands.Choice(name="Streaming", value="streaming"),
    app_commands.Choice(name="Listening", value="listening"),
    app_commands.Choice(name="Watching", value="watching"),
    app_commands.Choice(name="Competing", value="competing"),
])
async def set_status(interaction: discord.Interaction, status: str, type: app_commands.Choice[str]):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
    status_type = type.value
    if status_type == "playing":
        activity = discord.Game(name=status)
    elif status_type == "streaming":
        activity = discord.Streaming(name=status, url="https://www.youtube.com/@DRAXITY_official")
    elif status_type == "listening":
        activity = discord.Activity(type=discord.ActivityType.listening, name=status)
    elif status_type == "watching":
        activity = discord.Activity(type=discord.ActivityType.watching, name=status)
    elif status_type == "competing":
        activity = discord.Activity(type=discord.ActivityType.competing, name=status)
    else:
        activity = discord.Game(name=status)
    await interaction.client.change_presence(activity=activity)
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({"status": status, "type": status_type}, f)
    except Exception as e:
        print("Error saving status:", e)
    await interaction.response.send_message(f"Bot status updated to: {status} ({status_type.capitalize()})", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
    # Restore Panel if exists
    panel_id = get_panel_id()
    if panel_id:
        print(f"Restored active panel with ID: {panel_id}")
    else:
        print("No active panel found.")
    # Restore bot status from file
    try:
        with open(STATUS_FILE, "r") as f:
            status_data = json.load(f)
            status = status_data.get("status")
            status_type = status_data.get("type")
            if status and status_type:
                if status_type == "playing":
                    activity = discord.Game(name=status)
                elif status_type == "streaming":
                    activity = discord.Streaming(name=status, url="https://www.youtube.com/@DRAXITY_official")
                elif status_type == "listening":
                    activity = discord.Activity(type=discord.ActivityType.listening, name=status)
                elif status_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=status)
                elif status_type == "competing":
                    activity = discord.Activity(type=discord.ActivityType.competing, name=status)
                else:
                    activity = discord.Game(name=status)
                await bot.change_presence(activity=activity)
                print(f"Restored bot status: {status} ({status_type})")
    except Exception as e:
        print("No status file found or error restoring status:", e)

keep_alive()
bot.run('MTM0ODkxNjgyODM0ODM1NDU5MQ.G55qen.4fHaN8acPxlTPbDkDqccB_ck3HRhCPl13oT-kA') 
