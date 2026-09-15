import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv

# Load local environment variables for offline testing
load_dotenv() 

# 1. Setup Bot Intents (Guilds and Manage Channels are required for ticketing)
intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Define the Ticket View with Private Channel Creation Logic
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Keeps the buttons working indefinitely

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        member = interaction.user

        # Acknowledge the interaction immediately to prevent a timeout error
        await interaction.response.defer(ephemeral=True)

        # Find or automatically create the "🎟️ TICKETS" Category
        category = discord.utils.get(guild.categories, name="🎟️ TICKETS")
        if category is None:
            try:
                category = await guild.create_category("🎟️ TICKETS")
            except discord.Forbidden:
                await interaction.followup.send("❌ Error: I do not have permission to create categories.", ephemeral=True)
                return

        # Define specific private channel permissions
        # Blocks @everyone from viewing, allows the ticket creator and the Bot to view/chat
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }

        # Create the private ticket channel inside the category box
        channel_name = f"ticket-{ticket_type}-{member.name}".lower().replace(" ", "-")
        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket opened by {member.mention} for {ticket_type}."
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Error: I do not have permission to create channels.", ephemeral=True)
            return

        # Post a welcome message inside the new private ticket channel
        welcome_embed = discord.Embed(
            title="🎫 Ticket Created",
            description=f"Welcome {member.mention}!\nOur support staff will be with you shortly regarding your **{ticket_type}** issue.",
            color=discord.Color.blue()
        )
        await ticket_channel.send(embed=welcome_embed)

        # Notify the user privately that their ticket channel is ready
        await interaction.followup.send(f"✅ Your ticket has been created here: {ticket_channel.mention}", ephemeral=True)

    # --- Button Assignments ---
    @discord.ui.button(label="Bug Report", style=discord.ButtonStyle.blurple, custom_id="btn_bug_report", emoji="🪁")
    async def bug_report_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Bug Report")

    @discord.ui.button(label="Forgot Password", style=discord.ButtonStyle.danger, custom_id="btn_forgot_password", emoji="🔒")
    async def forgot_password_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Forgot Password")

    @discord.ui.button(label="Something else?", style=discord.ButtonStyle.secondary, custom_id="btn_something_else", emoji="❓")
    async def something_else_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "General Inquiry")


# 3. Lifecycle Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        # Registers the persistent views so buttons work even after the bot restarts
        bot.add_view(TicketPanelView())
        
        # Sync the slash commands globally across Discord
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# 4. Global Slash Command to Deploy Panel
@bot.tree.command(name="ticket_panel", description="Spawns the customized support ticket window panel.")
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔷 Hexoria Support",
        description="Select the type of issue you need help with below.\n\n*Hexoria Network*",
        color=discord.Color.dark_theme()
    )
    
    view = TicketPanelView()
    await interaction.response.send_message(embed=embed, view=view)


# 5. Boot Up Webserver and Bot Execution
if __name__ == "__main__":
    keep_alive() 
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: Missing 'DISCORD_TOKEN' environment variable setup.")
