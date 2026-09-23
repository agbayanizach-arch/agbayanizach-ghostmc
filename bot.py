import discord
from discord import app_commands
import os
from datetime import datetime
import asyncio
from keep_alive import keep_alive

class AccountBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
        self.vanity_string = None
        self.vanity_role_id = None

    async def setup_hook(self):
        await self.tree.sync()
        self.loop.create_task(self.check_vanity_statuses())

    async def check_vanity_statuses(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.vanity_string and self.vanity_role_id:
                for guild in self.guilds:
                    role = guild.get_role(self.vanity_role_id)
                    if not role:
                        continue
                    
                    for member in guild.members:
                        if member.bot:
                            continue
                        
                        has_vanity = False
                        for activity in member.activities:
                            if isinstance(activity, discord.CustomActivity) and activity.name:
                                if self.vanity_string in activity.name:
                                    has_vanity = True
                                    break
                        
                        try:
                            if has_vanity and role not in member.roles:
                                await member.add_roles(role)
                                print(f"Added vanity role to {member.name}")
                            elif not has_vanity and role in member.roles:
                                await member.remove_roles(role)
                                print(f"Removed vanity role from {member.name}")
                        except discord.Forbidden:
                            print(f"Missing permissions to manage roles in {guild.name}")
                        except Exception as e:
                            print(f"Error updating role for {member.name}: {e}")
            
            await asyncio.sleep(10)

client = AccountBot()
ACCOUNTS_FILE = "accounts.txt"

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

def has_vanity_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not client.vanity_role_id:
            raise app_commands.AppCommandError("Vanity system is not set up by the admin yet.")
            
        role = interaction.guild.get_role(client.vanity_role_id)
        if role in interaction.user.roles:
            return True
            
        raise app_commands.AppCommandError("Missing Vanity")
    return app_commands.check(predicate)

# ALLOWED FOR EVERYONE: Check stock
@client.tree.command(name="stock", description="Check the number of available accounts in stock")
async def stock(interaction: discord.Interaction):
    if not os.path.exists(ACCOUNTS_FILE) or os.stat(ACCOUNTS_FILE).st_size == 0:
        count = 0
    else:
        with open(ACCOUNTS_FILE, "r") as f:
            lines = f.readlines()
        count = len([line for line in lines if ":" in line])

    embed = discord.Embed(
        title="📦 Current Account Stock",
        description=f"There are currently **{count}** Minecraft accounts available to generate!",
        color=discord.Color.blue() if count > 0 else discord.Color.red()
    )
    embed.set_footer(text="Use /gen to get an account")
    await interaction.response.send_message(embed=embed)

# RESTRICTED: Requires vanity status role + 2-minute cooldown
@client.tree.command(name="gen", description="Generate a Minecraft account sent directly to your DM")
@has_vanity_role()
@app_commands.checks.cooldown(1, 120.0, key=lambda i: i.user.id)
async def gen(interaction: discord.Interaction):
    if not os.path.exists(ACCOUNTS_FILE) or os.stat(ACCOUNTS_FILE).st_size == 0:
        await interaction.response.send_message("❌ Out of stock! Please ask an admin to restock.", ephemeral=True)
        return

    with open(ACCOUNTS_FILE, "r") as f:
        lines = f.readlines()

    account_line = None
    for line in lines:
        if ":" in line:
            account_line = line.strip()
            break

    if not account_line:
        await interaction.response.send_message("❌ Out of stock or invalid file format! Please restock.", ephemeral=True)
        return

    lines.remove(account_line + "\n" if account_line + "\n" in lines else account_line)
    with open(ACCOUNTS_FILE, "w") as f:
        f.writelines(lines)

    email, password = account_line.split(":", 1)

    embed = discord.Embed(
        title="Minecraft Account Generated",
        color=discord.Color.green()
    )
    embed.add_field(name="📩Email", value=f"`{email}`", inline=True)
    embed.add_field(name="🔓Password", value=f"`{password}`", inline=True)
    
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    embed.set_footer(text=f"Free Account • {current_time}")

    try:
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("📬 Your account has been sent to your DMs!", ephemeral=True)
    except discord.Forbidden:
        with open(ACCOUNTS_FILE, "a") as f:
            f.write(account_line + "\n")
        await interaction.response.send_message("❌ I couldn't DM you! Please open your privacy settings / DMs and try again.", ephemeral=True)

@gen.error
async def gen_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Slow down! You can generate another account in **{error.retry_after:.1f}** seconds.", ephemeral=True)
    elif "Missing Vanity" in str(error):
        status_text = f"`{client.vanity_string}`" if client.vanity_string else "the server vanity"
        await interaction.response.send_message(f"❌ **Access Denied!** You must put {status_text} in your custom status to unlock this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ {str(error)}", ephemeral=True)

# OWNER ONLY: Restock system
@client.tree.command(name="restock", description="Restock accounts using a text file")
@app_commands.describe(file="Upload the txt file containing email:pass accounts")
@app_commands.checks.has_permissions(administrator=True)
async def restock(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith('.txt'):
        await interaction.response.send_message("❌ Please upload a valid `.txt` file.", ephemeral=True)
        return

    try:
        content = await file.read()
        text_content = content.decode("utf-8")

        with open(ACCOUNTS_FILE, "a") as f:
            f.write(text_content + "\n")

        lines_count = len([l for l in text_content.splitlines() if ":" in l])
        await interaction.response.send_message(f"✅ Successfully restocked **{lines_count}** accounts!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to process file: {str(e)}", ephemeral=True)

# PUBLIC EMBED SETUP: Setup vanity string and display public layout info
@client.tree.command(name="vanity", description="Set up the custom status string and reward role")
@app_commands.describe(vanityname="The text required in their status (e.g., .gg/myserver)", role="The role to give them")
@app_commands.checks.has_permissions(administrator=True)
async def vanity(interaction: discord.Interaction, vanityname: str, role: discord.Role):
    client.vanity_string = vanityname
    client.vanity_role_id = role.id
    
    # Custom public layout requested
    embed = discord.Embed(
        title="⚙️ Vanity System",
        description=f"🔹 **Add this on your status for /gen access**\n\"{vanityname}\"\n\n🔹 **Reward Role :** {role.mention}",
        color=discord.Color.purple()
    )
    
    # Sends it publicly so all members can read it
    await interaction.response.send_message(embed=embed, ephemeral=False)

@restock.error
@vanity.error
async def admin_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Only server administrators/owners can use this configuration command.", ephemeral=True)

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN environment variable not found.")
