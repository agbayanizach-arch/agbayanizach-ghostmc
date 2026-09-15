import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive

# 1. Setup Bot Intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Define the Interactive Ticket View Buttons
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # persistent view so buttons work after restarts

    @discord.ui.button(label="Bug Report", style=discord.ButtonStyle.blurple, custom_id="btn_bug_report", emoji="🪁")
    async def bug_report_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Acknowledge button press and write your ticket logic here
        await interaction.response.send_message("Creating a Bug Report ticket...", ephemeral=True)

    @discord.ui.button(label="Forgot Password", style=discord.ButtonStyle.danger, custom_id="btn_forgot_password", emoji="🔒")
    async def forgot_password_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Creating a Forgot Password ticket...", ephemeral=True)

    @discord.ui.button(label="Something else?", style=discord.ButtonStyle.secondary, custom_id="btn_something_else", emoji="❓")
    async def something_else_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Opening a general inquiry ticket...", ephemeral=True)

# 3. Lifecycle Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        # Sync the slash commands globally
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# 4. Slash Command to Deploy Panel
@bot.tree.command(name="ticket_panel", description="Spawns the customized support ticket window panel.")
async def ticket_panel(interaction: discord.Interaction):
    # Constructing matching embed properties from reference UI layout
    embed = discord.Embed(
        title="🔷 GhostMC Support",
        description="Select the type of issue you need help with below.\n\n*Hexoria Network*",
        color=discord.Color.dark_theme()
    )
    
    # Send panel to the channel where command is executed
    view = TicketPanelView()
    await interaction.response.send_message(embed=embed, view=view)

# 5. Boot Up Webserver and Bot Execution
if __name__ == "__main__":
    # Starts background web framework for UptimeRobot monitoring
    keep_alive() 
    
    # Runs the application using token stored securely in your deployment variables
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: Missing 'DISCORD_TOKEN' environment variable setup.")
