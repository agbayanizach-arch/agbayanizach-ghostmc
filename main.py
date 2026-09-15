import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv() 

# Enabled message_content intent so prefix commands like !delete work perfectly
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

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

# New Feature: /customwelcome <message>
@bot.tree.command(name="customwelcome", description="Sends a welcome embed message to the current channel without a color border.")
@app_commands.describe(message="The message content to display inside the welcome embed")
async def customwelcome(interaction: discord.Interaction, message: str):
    # Setting color=0x2b2d31 matches the default Discord dark mode background, hiding the left border color
    embed = discord.Embed(
        description=message,
        color=0x2b2d31
    )
    await interaction.response.send_message(embed=embed)

# New Feature: !delete
@bot.command(name="delete")
async def delete_ticket(ctx):
    # Optional safety check: ensures it only deletes channels within the TICKETS category or named ticket-*
    if ctx.channel.category and ctx.channel.category.name == "🎟️ TICKETS" or ctx.channel.name.startswith("ticket-"):
        await ctx.send("🗑️ This ticket channel will be deleted in 5 seconds...")
        import asyncio
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
