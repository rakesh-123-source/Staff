import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import asyncio
import json
from flask import Flask
import random
from threading import Thread
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


GUILD_ID = 1270760786817450086  # Replace with your server ID
APPLICATIONS_CHANNEL_ID = 1348759783184011324  # Replace with the applications channel ID
ANNOUNCEMENT_CHANNEL_ID = 1330801025761808416  # Replace with the announcement channel ID
STAFF_ROLE_ID = 1337669415646396518  # Replace with the staff role ID

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# ✅ Admin Check
def is_admin():
    def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# 📌 **Start Application Panel**
class StartApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Never times out

    @discord.ui.button(label="Start Application", style=discord.ButtonStyle.green)
    async def start_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ **Check your DMs to start the application!**", ephemeral=True)
        await start_application_process(interaction.user)

# 📌 **Confirmation View before starting**
class ConfirmView(View):
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.send_message("❌ **Application canceled!**", ephemeral=True)
        self.stop()

# 📌 **Application Process (DMs)**
async def start_application_process(user: discord.User):
    try:
        questions = [
            "What is your real name?",
            "How old are you?",
            "Why do you want to become a staff member?",
            "What experience do you have in moderation?",
            "How many hours can you dedicate daily?",
            "How would you handle a rule-breaker?",
            "Do you agree to follow all staff rules?"
        ]

        answers = []
        dm_channel = await user.create_dm()

        confirm_view = ConfirmView()
        msg = await dm_channel.send(
            embed=discord.Embed(
                title="📝 Staff Application",
                description="Press **Confirm** to start the application process.",
                color=0xffaa00
            ), 
            view=confirm_view
        )
        await confirm_view.wait()

        if not confirm_view.value:
            return

        for question in questions:
            embed = discord.Embed(title="❓ Question", description=question, color=0x00ff00)
            view = CancelView()
            question_msg = await dm_channel.send(embed=embed, view=view)

            try:
                response = await bot.wait_for(
                    "message",
                    check=lambda m: m.author == user and m.channel == dm_channel,
                    timeout=60
                )
                answers.append(response.content)
                await question_msg.edit(embed=discord.Embed(title="✅ Answered", description=f"**{response.content}**", color=0x00ff00), view=None)
            except asyncio.TimeoutError:
                await dm_channel.send("❌ **You took too long to answer! Application canceled.**")
                return

        # Send to applications channel
        app_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
        embed = discord.Embed(title="📩 New Staff Application", color=0x3498db)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="👤 Applicant", value=user.mention, inline=False)

        for i, q in enumerate(questions):
            embed.add_field(name=f"❓ {q}", value=f"**📌 {answers[i]}**", inline=False)

        embed.set_footer(text="React with ✅ or ❌ to vote!")
        app_msg = await app_channel.send(embed=embed)
        await app_msg.add_reaction("✅")
        await app_msg.add_reaction("❌")

    except Exception as e:
        print(f"Error in application process: {e}")

# 📌 **Cancel Button**
class CancelView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Cancel Application", style=discord.ButtonStyle.red)
    async def cancel_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ **Application canceled.**", ephemeral=True)
        self.stop()

# 📌 **Admin Command: Send Application Panel**
@bot.tree.command(name="send_application_panel", description="Sends the application panel in a selected channel.")
async def send_application_panel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
    embed = discord.Embed(
        title="📌 Staff Applications",
        description="Click the **Start Application** button below to apply for a staff position.",
        color=0x3498db
    )
    await channel.send(embed=embed, view=StartApplicationView())
    await interaction.response.send_message(f"✅ **Application panel sent to {channel.mention}!**", ephemeral=True)

# 📌 **Admin Command: Announce Selected Staff**
@bot.tree.command(name="announce_staff", description="Announces a user as selected staff.")
async def announce_staff(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
    staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
    if staff_role:
        await user.add_roles(staff_role)
        ann_channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        embed = discord.Embed(
            title="🎉 New Staff Member!",
            description=f"Congratulations {user.mention} for being selected as a **Staff Member**! 🎊",
            color=0x2ecc71
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        await ann_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ **{user.mention} has been announced as staff!**", ephemeral=True)
    else:
        await interaction.response.send_message("❌ **Staff role not found!**", ephemeral=True)
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
    print(f"✅ Logged in as {bot.user}.")

bot.run('MTM0ODkxNjgyODM0ODM1NDU5MQ.G55qen.4fHaN8acPxlTPbDkDqccB_ck3HRhCPl13oT-kA')
