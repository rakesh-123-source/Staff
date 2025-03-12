import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
from flask import Flask
from threading import Thread
import re 
import firebase_admin
from firebase_admin import credentials, firestore
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
keep_alive()
GUILD_ID = 1270760786817450086  
APPLICATIONS_CHANNEL_ID = 1348759783184011324  
ANNOUNCEMENT_CHANNEL_ID = 1330801025761808416 
STAFF_ROLE_ID = 1337669415646396518
SAPHIRE_BOT_ID = 678344927997853742
SAPHIRE_LISTENING_CHANNEL_ID = 1335334770980159579
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
cred = credentials.Certificate("server_staffs.json") 
app1 = firebase_admin.initialize_app(cred, name="firebase_app1")
db = firestore.client(app=app1)
APPLICATIONS_COLLECTION = "applications"
NUM_QUESTIONS = 10
DEFAULT_PLACEHOLDER = "** **"
QUESTIONS = [
    "What is your time zone?",
    "Why you want to join our staff team?",
    "Have you ever did moderation before ?",
    "Do you know to use our moderation bots ?",
    "Do you agree our server staff rules ?",
    "What relevant skills  you have that would benefit our staff team?",
    "How would you handle a conflict between community members?",
    "What strategies would you use to maintain our server?",
    "Can you describe a situation where you successfully resolved a challenging issue online?",
    "What are your expectations from our staff team, and how do you see yourself contributing?"
]
def get_application_instructions() -> str:
    instructions = (
        "> You have already received the application form.\n"
        "> Please reply in one message with your answers in order, each on a new line.\n"
        f"> Ensure you provide exactly {NUM_QUESTIONS} answers.\n\n"
        "For example, your reply should be formatted as follows:\n"
        "```\n"
        "1. What is your time zone?\n"
        "> Answer:  GMT+:30\n"
        "** **\n"
        "2. Why you want to join our staff team?\n"
        "> Answer:  I want to make the server more good !\n"
        "** **\n"
        "......\n"
        "10. What are your expectations from our staff team, and how do you see yourself contributing?\n"
        "> Answer:  As a moderator .\n"
        "** **\n"
        "```\n\n"
    )
    return instructions
def parse_application_response(content: str):
    pattern = r'\d+\.\s*.*?\n>\s*Answer:\s*(.*?)(?=\n\d+\.|$)'
    answers = re.findall(pattern, content, re.DOTALL)
    if len(answers) != NUM_QUESTIONS:
        return None
    cleaned_answers = []
    for ans in answers:
        cleaned = ans.strip()
        if cleaned == "" or cleaned == DEFAULT_PLACEHOLDER:
            return None
        cleaned_answers.append(cleaned)
    return cleaned_answers
def user_has_application(user_id: int) -> bool:
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        if data.get("status") in ("in_progress", "submitted", "selected"):
            return True
    return False
def create_application_record(user_id: int):
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    doc_ref.set({"status": "in_progress"})
def update_application_record(user_id: int, status: str, application_text: str = None):
    doc_ref = db.collection(APPLICATIONS_COLLECTION).document(str(user_id))
    update_data = {"status": status}
    if application_text is not None:
        update_data["application_text"] = application_text
    doc_ref.update(update_data)
async def trigger_application_for_user(member: discord.Member):
    try:
        if user_has_application(member.id):
            dm_channel = await member.create_dm()
            await dm_channel.send("❌ You have already filled out or are in the process of filling out an application.")
            return
        create_application_record(member.id)
        dm_channel = await member.create_dm()
        instruction_text = get_application_instructions()
        embed_dm = discord.Embed(
            title="📝 Staff Application",
            description=instruction_text,
            color=discord.Color.orange()
        )
        embed_dm.set_footer(text="Please follow the format exactly!")
        await dm_channel.send(embed=embed_dm)
        response = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == member.id and m.channel.id == dm_channel.id,
            timeout=300
        )
        answers = parse_application_response(response.content)
        if answers is None:
            await dm_channel.send("❌ Your application has **expired** due to incomplete or invalid answers.")
            update_application_record(member.id, "expired")
            return

        await dm_channel.send("✅ Your application has been received. Thank you!")
        update_application_record(member.id, "submitted", response.content)
        description = f"> 📝 **New Apllication **\n> Applicant : {member.mention}\n\n"
        for i in range(NUM_QUESTIONS):
            description += f"{i+1}. {QUESTIONS[i]}\n> Answer:  {answers[i]}\n** **\n"
        description += "\n> **Vote  with  ✅  or  ❌ **"
        embed_app = discord.Embed(
            description=description,
            color=41983 
        )
        embed_app.set_footer(text="From Gamer's Dojo by ÐRΛ✘ITY")
        embed_app.set_thumbnail(url=(member.avatar.url if member.avatar else member.default_avatar.url))
        app_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
        sent_msg = await app_channel.send(embed=embed_app)
        await sent_msg.add_reaction("✅")
        await sent_msg.add_reaction("❌")
    except asyncio.TimeoutError:
        try:
            await dm_channel.send("⌛ You took too long to submit your application. Please contact an admin if you'd like to try again.")
            update_application_record(member.id, "expired")
        except Exception as dm_err:
            print("Error sending DM on timeout:", dm_err)
    except Exception as e:
        print("Error in trigger_application_for_user:", e)
@bot.event
async def on_message(message: discord.Message):
    if (message.channel.id == SAPHIRE_LISTENING_CHANNEL_ID and 
        message.author.id == SAPHIRE_BOT_ID):
        user_ids = re.findall(r'\b\d{17,19}\b', message.content)
        for uid in user_ids:
            try:
                user_id = int(uid)
                guild = message.guild
                if guild:
                    member = guild.get_member(user_id)
                    if member:
                        asyncio.create_task(trigger_application_for_user(member))
            except Exception as e:
                print("Error processing user id from Saphire bot message:", e)
    await bot.process_commands(message)
STATUS_FILE = "status.json"
@bot.tree.command(name="set_status", description="Sets the bot's status message.(admin only)")
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
async def setstatus(interaction: discord.Interaction, status: str, type: app_commands.Choice[str]):
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
bot.run('MTM0ODkxNjgyODM0ODM1NDU5MQ.G55qen.4fHaN8acPxlTPbDkDqccB_ck3HRhCPl13oT-kA')
