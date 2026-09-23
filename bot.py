import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime

# CONFIGURATION: Replace with your actual Vouch Channel ID
VOUCH_CHANNEL_ID = 123456789012345678  

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read messages and mentions
        intents.members = True          # Required for timeouts
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Syncs the slash commands globally across all your servers
        await self.tree.sync()

bot = MyBot()

# Dictionary to track payouts: { Target_User_ID: { "payouter_id": ID, "completed": False } }
pending_payouts = {}

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user.name}')

@bot.tree.command(name="gen", description="Generate a payout and send credentials via DM.")
@app_commands.describe(
    target_user="The member receiving the payout",
    credentials="The login details in email:pass format"
)
async def gen(interaction: discord.Interaction, target_user: discord.Member, credentials: str):
    # 1. Validate credentials format
    if ":" not in credentials or len(credentials.split(":")) != 2:
        await interaction.response.send_message("❌ **Invalid Format.** Use `email:pass` without spaces.", ephemeral=True)
        return

    email, password = credentials.split(":")
    formatted_payload = f"{email}:{password}"

    # 2. Try sending the credentials to the user's DMs
    try:
        await target_user.send(
            f"📦 **Your Account Has Been Generated!**\n"
            f"Format: `email:pass`\n\n"
            f"`{formatted_payload}`\n\n"
            f"⚠️ **IMPORTANT:** You have **5 minutes** to leave a vouch mentioning your payouter in <#{VOUCH_CHANNEL_ID}>, or you will be automatically timed out for 1 hour!"
        )
        
        # 3. Save tracking details (pings the staff member who used the slash command)
        pending_payouts[target_user.id] = {
            "payouter_id": interaction.user.id,
            "completed": False
        }
        
        # Public hidden confirmation message (only visible to the staff who typed the command)
        await interaction.response.send_message(f"✅ Credentials securely DM'd to {target_user.mention}. Countdown started.", ephemeral=True)
        
        # 4. Start the 5-minute background countdown task (300 seconds)
        asyncio.create_task(payout_timeout_timer(interaction.channel, target_user))
        
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ **Error:** Cannot DM {target_user.mention}. Their DMs are closed.", ephemeral=True)

async def payout_timeout_timer(channel, target_user: discord.Member):
    """Waits 5 minutes, then checks if the user vouched in the designated channel."""
    await asyncio.sleep(300)  
    
    if target_user.id in pending_payouts and not pending_payouts[target_user.id]["completed"]:
        payouter_id = pending_payouts[target_user.id]["payouter_id"]
        vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
        
        vouch_found = False
        
        # Check back in the vouch channel history to double check if they tagged you
        if vouch_channel:
            try:
                async for message in vouch_channel.history(limit=50):
                    if message.author.id == target_user.id:
                        if any(mention.id == payouter_id for mention in message.mentions):
                            vouch_found = True
                            break
            except Exception as e:
                print(f"Error checking channel history: {e}")

        # If they left a valid vouch tagging you, close cleanly
        if vouch_found:
            del pending_payouts[target_user.id]
            await channel.send(
                f"🔒 **Transaction Closed!**\n"
                f"User {target_user.mention} successfully vouched in <#{VOUCH_CHANNEL_ID}>.\n"
                f"Generator Staff: <@{payouter_id}>"
            )
            return

        # If they failed to vouch, apply the 1-hour timeout
        del pending_payouts[target_user.id]
        try:
            duration = datetime.timedelta(hours=1)
            await target_user.timeout(duration, reason="Failed to vouch in the designated channel within 5 minutes of /gen.")
            
            await channel.send(
                f"⏰ **Time's Up!**\n"
                f"User {target_user.mention} did not vouch in <#{VOUCH_CHANNEL_ID}> within 5 minutes.\n"
                f"They have been **timed out for 1 hour**.\n"
                f"Staff Notified: <@{payouter_id}>"
            )
        except discord.Forbidden:
            await channel.send(
                f"⏰ **Time's Up!**\n"
                f"User {target_user.mention} failed to vouch, but the bot lacks permission to timeout this user.\n"
                f"Staff Notified: <@{payouter_id}>"
            )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    # If they type directly in the Vouch Channel and tag the payouter, close it immediately
    if message.channel.id == VOUCH_CHANNEL_ID and user_id in pending_payouts:
        payouter_id = pending_payouts[user_id]["payouter_id"]
        
        if any(mention.id == payouter_id for mention in message.mentions):
            pending_payouts[user_id]["completed"] = True
            del pending_payouts[user_id]
            
            await message.channel.send(
                f"🔒 **Transaction Closed!**\n"
                f"Vouch confirmed for {message.author.mention}.\n"
                f"Generator Staff: <@{payouter_id}>"
            )
            try:
                await message.add_reaction("✅")
            except discord.Forbidden:
                pass

    await bot.process_commands(message)

# Replace with your actual secure bot token
bot.run('YOUR_BOT_TOKEN_HERE')
