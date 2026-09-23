import discord
from discord import app_commands
import os
from datetime import datetime
from keep_alive import keep_alive

# Initialize bot
class AccountBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = AccountBot()
ACCOUNTS_FILE = "accounts.txt"

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command(name="gen", description="Generate a Minecraft account")
async def gen(interaction: discord.Interaction):
    # Check if the file exists and has accounts
    if not os.path.exists(ACCOUNTS_FILE) or os.stat(ACCOUNTS_FILE).st_size == 0:
        await interaction.response.send_message("❌ Out of stock! Please ask an admin to restock.", ephemeral=True)
        return

    # Read all lines
    with open(ACCOUNTS_FILE, "r") as f:
        lines = f.readlines()

    # Find the first valid account line
    account_line = None
    for line in lines:
        if ":" in line:
            account_line = line.strip()
            break

    if not account_line:
        await interaction.response.send_message("❌ Out of stock or invalid file format! Please restock.", ephemeral=True)
        return

    # Remove the selected account from the list
    lines.remove(account_line + "\n" if account_line + "\n" in lines else account_line)
    with open(ACCOUNTS_FILE, "w") as f:
        f.writelines(lines)

    # Split email and password
    email, password = account_line.split(":", 1)

    # Create the embed layout
    embed = discord.Embed(
        title="Minecraft Account Generated",
        color=discord.Color.green()
    )
    embed.add_field(name="📩Email", value=f"`{email}`", inline=True)
    embed.add_field(name="🔓Password", value=f"`{password}`", inline=True)
    
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    embed.set_footer(text=f"Free Account • {current_time}")

    # Send the embed privately to the user who used the command
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="restock", description="Restock accounts using a text file")
@app_commands.describe(file="Upload the txt file containing email:pass accounts")
async def restock(interaction: discord.Interaction, file: discord.Attachment):
    # Ensure it's a text file
    if not file.filename.endswith('.txt'):
        await interaction.response.send_message("❌ Please upload a valid `.txt` file.", ephemeral=True)
        return

    try:
        # Read the attached file content
        content = await file.read()
        text_content = content.decode("utf-8")

        # Append to the local stock file
        with open(ACCOUNTS_FILE, "a") as f:
            f.write(text_content + "\n")

        # Count lines added
        lines_count = len([l for l in text_content.splitlines() if ":" in l])

        await interaction.response.send_message(f"✅ Successfully restocked **{lines_count}** accounts!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to process file: {str(e)}", ephemeral=True)

# Start the web server container for UptimeRobot
keep_alive()

# Run the bot using environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN environment variable not found.")
