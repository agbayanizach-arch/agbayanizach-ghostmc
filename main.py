import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv
import asyncio

load_dotenv() 

# 1. Verification of Intents (Ensure both are enabled in Discord Developer Portal)
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True 
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "welcome_config.txt"
DEFAULT_TEMPLATE = "Welcome {mention} to **{server}**! You are our #{membercount} member. {avatar}"

# Helper function to load configuration persistently from a file
def load_welcome_message():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return DEFAULT_TEMPLATE

# Helper function to save configuration persistently to a file
def save_welcome_message(text):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(text)

# Helper function to format the welcome templates cleanly
def format_welcome_message(template: str, member: discord.Member, guild: discord.Guild) -> discord.Embed:
    formatted_text = template.replace("{mention}", member.mention)\
                             .replace("{user}", member.mention)\
                             .replace("{username}", member.name)\
                             .replace("{server}", guild.name)\
                             .replace("{membercount}", str(guild.member_count))
    
    # Clean colorless side-bar overlay color
    embed = discord.Embed(description=formatted_text, color=0x2b2d31)
    
    if "{avatar}" in template:
        embed.set_thumbnail(url=member.display_avatar.url)
        
    return embed

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        member = interaction.user

        await interaction.response.defer(ephemeral=True)

        category = discord.utils.get(guild.categories, name="🎟️ TICKETS")
        if category is None:
            try:
                category = await guild.create_category("🎟️ TICKETS")
            except discord.Forbidden:
                await interaction.followup.send("❌ Error: The bot is missing the 'Manage Channels' permission to create a Category.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }

        channel_name = f"ticket-{ticket_type}-{member.name}".lower().replace(" ", "-")
        
        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket opened by {member.name} for {ticket_type}."
            )
            
            welcome_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=f"Welcome {member.mention}!\nOur team will review your **{ticket_type}** ticket shortly.",
                color=discord.Color.blue()
            )
            await ticket_channel.send(embed=welcome_embed)
            await interaction.followup.send(f"✅ Your private ticket has been created: {ticket_channel.mention}", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ Error: The bot role lacks proper permissions to build channels here.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Unknown Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Bug Report", style=discord.ButtonStyle.blurple, custom_id="persistent_btn:bug", emoji="🪁")
    async def bug_report_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Bug Report")

    @discord.ui.button(label="Forgot Password", style=discord.ButtonStyle.danger, custom_id="persistent_btn:password", emoji="🔒")
    async def forgot_password_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Forgot Password")

    @discord.ui.button(label="Something else?", style=discord.ButtonStyle.secondary, custom_id="persistent_btn:other", emoji="❓")
    async def something_else_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "General Inquiry")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    try:
        bot.add_view(TicketPanelView())
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="ticket_panel", description="Spawns the customized support ticket window panel.")
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔷 GhostMC Support",
        description="Select the type of issue you need help with below.\n\n*GhostMC*",
        color=discord.Color.dark_theme()
    )
    
    view = TicketPanelView()
    await interaction.response.send_message(embed=embed, view=view)


# --- FIXED: /customwelcome configures & persistently saves the format ---
@bot.tree.command(name="customwelcome", description="Sets and saves the greeting format for when new members join.")
@app_commands.describe(message="Set greeting format. Variables: {mention}, {user}, {username}, {server}, {membercount}, {avatar}")
async def customwelcome(interaction: discord.Interaction, message: str):
    save_welcome_message(message)  # Saves it to file configuration storage
    
    preview_embed = format_welcome_message(message, interaction.user, interaction.guild)
    await interaction.response.send_message(
        content="✅ **Welcome message saved permanently!** Here is a live preview of how it will look:", 
        embed=preview_embed
    )


# --- /testgreet triggers a test message instantly ---
@bot.tree.command(name="testgreet", description="Tests your configured welcome layout on yourself inside this channel.")
async def testgreet(interaction: discord.Interaction):
    current_template = load_welcome_message()
    test_embed = format_welcome_message(current_template, interaction.user, interaction.guild)
    await interaction.response.send_message(content="⚙️ **Running Welcomer Module Test...**", embed=test_embed)


# --- FIXED AUTOMATED LISTENER: Loads file template + attempts broader room detection ---
@bot.event
async def on_member_join(member: discord.Member):
    # Bug Check: Find channel named "welcome", "welcomes", or "welcome-log"
    welcome_channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if not welcome_channel:
        welcome_channel = discord.utils.get(member.guild.text_channels, name="welcomes")

    if welcome_channel:
        current_template = load_welcome_message()
        join_embed = format_welcome_message(current_template, member, member.guild)
        
        # Sends text mention message alongside the graphic colorless embed profile sheet
        await welcome_channel.send(content=member.mention, embed=join_embed)
    else:
        print(f"CRITICAL: Could not automatically greet {member.name} because no text channel named 'welcome' was found.")


# --- !delete ---
@bot.command(name="delete")
async def delete_ticket(ctx):
    if ctx.channel.category and ctx.channel.category.name == "🎟️ TICKETS" or ctx.channel.name.startswith("ticket-"):
        await ctx.send("🗑️ This ticket channel will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ This command can only be used inside a ticket channel.")

if __name__ == "__main__":
    keep_alive() 
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: Missing 'DISCORD_TOKEN' variable.")
