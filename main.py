import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv() 

# Setup Bot Intents (Explicitly requiring Guilds to manage structural channels)
intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the Ticket View with Private Channel Creation Logic
class TicketPanelView(discord.ui.View):
    def __init__(self):
        # timeout=None makes the view persistent so buttons stay active forever
        super().__init__(timeout=None) 

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        member = interaction.user

        # 1. Immediately defer to give Render enough time to process channel creation
        await interaction.response.defer(ephemeral=True)

        # 2. Find or create the "🎟️ TICKETS" Category
        category = discord.utils.get(guild.categories, name="🎟️ TICKETS")
        if category is None:
            try:
                category = await guild.create_category("🎟️ TICKETS")
            except discord.Forbidden:
                await interaction.followup.send("❌ Error: The bot is missing the 'Manage Channels' permission to create a Category.", ephemeral=True)
                return

        # 3. Define permission overwrites: lock out @everyone, allow user & bot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }

        # 4. Generate clean channel name
        channel_name = f"ticket-{ticket_type}-{member.name}".lower().replace(" ", "-")
        
        try:
            # 5. Create the private text channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket opened by {member.name} for {ticket_type}."
            )
            
            # 6. Post welcome message inside the newly opened private channel
            welcome_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=f"Welcome {member.mention}!\nOur team will review your **{ticket_type}** ticket shortly.",
                color=discord.Color.blue()
            )
            await ticket_channel.send(embed=welcome_embed)

            # 7. Edit the original temporary defer status to show the clean shortcut link
            await interaction.followup.send(f"✅ Your private ticket has been created: {ticket_channel.mention}", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ Error: The bot role lacks proper permissions to build channels here.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Unknown Error: {str(e)}", ephemeral=True)

    # --- Button Assignments with explicit custom_ids ---
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
        # Register the view during boot-up so existing panels in channels attach cleanly
        bot.add_view(TicketPanelView())
        
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.tree.command(name="ticket_panel", description="Spawns the customized support ticket window panel.")
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔷 GhostMC Support",
        description="Select the type of issue you need help with below.\n\n*Hexoria Network*",
        color=discord.Color.dark_theme()
    )
    
    view = TicketPanelView()
    await interaction.response.send_message(embed=embed, view=view)


if __name__ == "__main__":
    keep_alive() 
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("ERROR: Missing 'DISCORD_TOKEN' variable.")
