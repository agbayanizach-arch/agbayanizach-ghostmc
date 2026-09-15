import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv
import asyncio

load_dotenv() 

# Intents are configured correctly. Make sure BOTH 'Message Content' and 'Server Members'
# are toggled ON in your Discord Developer Portal!
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True 
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# File names for persistent local configuration storage
MESSAGE_FILE = "welcome_msg.txt"
CHANNEL_FILE = "welcome_channel.txt"
DEFAULT_TEMPLATE = "Welcome {mention} to **{server}**! You are our #{membercount} member. {avatar}"

# Persistent data managers
def load_welcome_config():
    msg = DEFAULT_TEMPLATE
    chan_id = None
    
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            msg = f.read()
            
    if os.path.exists(CHANNEL_FILE):
        with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
            try:
                chan_id = int(f.read().strip())
            except ValueError:
                chan_id = None
                
    return msg, chan_id

def save_welcome_config(message, channel_id):
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        f.write(message)
    with open(CHANNEL_FILE, "w", encoding="utf-8") as f:
        f.write(str(channel_id))

# Universal compiler to format custom layouts seamlessly
def format_welcome_message(template: str, member: discord.Member, guild: discord.Guild) -> discord.Embed:
    formatted_text = template.replace("{mention}", member.mention)\
                             .replace("{user}", member.mention)\
                             .replace("{username}", member.name)\
                             .replace("{server}", guild.name)\
                             .replace("{membercount}", str(guild.member_count))
    
    # 0x2b2d31 removes the visible border accent on standard Dark Theme layouts
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


# --- FIXED: /customwelcome now locks and saves the exact active channel context ---
@bot.tree.command(name="customwelcome", description="Saves configuration template and locks greetings to this current channel.")
@app_commands.describe(message="Set greeting template. Vars: {mention}, {user}, {username}, {server}, {membercount}, {avatar}")
async def customwelcome(interaction: discord.Interaction, message: str):
    # Dynamically locks greeting tasks to the channel where you typed this command
    save_welcome_config(message, interaction.channel_id)
    
    preview_embed = format_welcome_message(message, interaction.user, interaction.guild)
    await interaction.response.send_message(
        content=f"✅ **Welcome message saved!** Greetings are now locked to {interaction.channel.mention}. Live preview:", 
        embed=preview_embed
    )


# --- NEW: /testgreet pulls saved layout data ---
@bot.tree.command(name="testgreet", description="Tests your saved layout on yourself directly inside this channel.")
async def testgreet(interaction: discord.Interaction):
    template, _ = load_welcome_config()
    test_embed = format_welcome_message(template, interaction.user, interaction.guild)
    await interaction.response.send_message(content="⚙️ **Running Welcomer Module Test...**", embed=test_embed)


# --- FIXED AUTOMATED LISTENER: Instantly triggers via persistent target ID ---
@bot.event
async def on_member_join(member: discord.Member):
    template, target_channel_id = load_welcome_config()
    
    # Resolves target text delivery terminal dynamically via stored configuration data
    welcome_channel = member.guild.get_channel(target_channel_id) if target_channel_id else None
    
    # Fallback to general safety room array check if file registration lookup fails
    if not welcome_channel:
        welcome_channel = discord.utils.get(member.guild.text_channels, name="welcome")

    if welcome_channel:
        join_embed = format_welcome_message(template, member, member.guild)
        # Directly pings user externally first to register notification, followed by layout panel injection
        await welcome_channel.send(content=member.mention, embed=join_embed)
    else:
        print(f"CRITICAL: Failed to greet {member.name}. Setup a channel first with /customwelcome.")


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
