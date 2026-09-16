import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()

# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# FILES
# =========================================================

MESSAGE_FILE = "welcome_msg.txt"
CHANNEL_FILE = "welcome_channel.txt"
AUTORESPONDER_FILE = "autoresponders.json"

DEFAULT_TEMPLATE = (
    "Welcome {mention} to **{server}**! "
    "You are our #{membercount} member. {avatar}"
)

# =========================================================
# WELCOME CONFIG
# =========================================================

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


# =========================================================
# WELCOME MESSAGE FORMATTER
# =========================================================

def format_welcome_message(
    template: str,
    member: discord.Member,
    guild: discord.Guild
) -> discord.Embed:

    formatted_text = (
        template
        .replace("{mention}", member.mention)
        .replace("{user}", member.mention)
        .replace("{username}", member.name)
        .replace("{server}", guild.name)
        .replace("{membercount}", str(guild.member_count))
    )

    embed = discord.Embed(
        description=formatted_text,
        color=0x2b2d31
    )

    if "{avatar}" in template:
        embed.set_thumbnail(url=member.display_avatar.url)

    return embed


# =========================================================
# AUTORESPONDER SYSTEM
# =========================================================

def load_autoresponders():
    """
    Loads all autoresponders from autoresponders.json.
    Structure:
    {
        "guild_id": {
            "trigger": "response"
        }
    }
    """

    if not os.path.exists(AUTORESPONDER_FILE):
        return {}

    try:
        with open(AUTORESPONDER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except (json.JSONDecodeError, OSError):
        return {}


def save_autoresponders(data):
    with open(AUTORESPONDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Load autoresponders when the bot starts
autoresponders = load_autoresponders()


# =========================================================
# TICKET PANEL
# =========================================================

class TicketPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(
        self,
        interaction: discord.Interaction,
        ticket_type: str
    ):

        guild = interaction.guild
        member = interaction.user

        await interaction.response.defer(ephemeral=True)

        category = discord.utils.get(
            guild.categories,
            name="🎟️ TICKETS"
        )

        if category is None:
            try:
                category = await guild.create_category("🎟️ TICKETS")

            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ Error: The bot is missing the "
                    "'Manage Channels' permission to create a Category.",
                    ephemeral=True
                )
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                view_channel=False
            ),

            member: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                view_channel=True
            ),

            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                view_channel=True
            )
        }

        channel_name = (
            f"ticket-{ticket_type}-{member.name}"
            .lower()
            .replace(" ", "-")
        )

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket opened by {member.name} for {ticket_type}."
            )

            welcome_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=(
                    f"Welcome {member.mention}!\n"
                    f"Our team will review your **{ticket_type}** ticket shortly."
                ),
                color=discord.Color.blue()
            )

            await ticket_channel.send(embed=welcome_embed)

            await interaction.followup.send(
                f"✅ Your private ticket has been created: "
                f"{ticket_channel.mention}",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Error: The bot role lacks proper permissions "
                "to build channels here.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"❌ Unknown Error: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Bug Report",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_btn:bug",
        emoji="🪁"
    )
    async def bug_report_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(interaction, "Bug Report")

    @discord.ui.button(
        label="Forgot Password",
        style=discord.ButtonStyle.danger,
        custom_id="persistent_btn:password",
        emoji="🔒"
    )
    async def forgot_password_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(interaction, "Forgot Password")

    @discord.ui.button(
        label="Something else?",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_btn:other",
        emoji="❓"
    )
    async def something_else_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(interaction, "General Inquiry")


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user.name}")

    try:
        bot.add_view(TicketPanelView())

        synced = await bot.tree.sync()

        print(f"Synced {len(synced)} command(s).")
        print(f"Loaded {sum(len(v) for v in autoresponders.values())} autoresponder(s).")

    except Exception as e:
        print(f"Error syncing commands: {e}")


# =========================================================
# TICKET PANEL SLASH COMMAND
# =========================================================

@bot.tree.command(
    name="ticket_panel",
    description="Spawns the customized support ticket window panel."
)
async def ticket_panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🔷 GhostMC Support",
        description=(
            "Select the type of issue you need help with below.\n\n"
            "*GhostMC*"
        ),
        color=discord.Color.dark_theme()
    )

    view = TicketPanelView()

    await interaction.response.send_message(
        embed=embed,
        view=view
    )


# =========================================================
# CUSTOM WELCOME
# =========================================================

@bot.tree.command(
    name="customwelcome",
    description="Saves configuration template and locks greetings to this current channel."
)
@app_commands.describe(
    message=(
        "Set greeting template. Vars: "
        "{mention}, {user}, {username}, {server}, "
        "{membercount}, {avatar}"
    )
)
async def customwelcome(
    interaction: discord.Interaction,
    message: str
):

    save_welcome_config(
        message,
        interaction.channel_id
    )

    preview_embed = format_welcome_message(
        message,
        interaction.user,
        interaction.guild
    )

    await interaction.response.send_message(
        content=(
            f"✅ **Welcome message saved!** "
            f"Greetings are now locked to {interaction.channel.mention}.\n"
            f"Live preview:"
        ),
        embed=preview_embed
    )


# =========================================================
# TEST GREET
# =========================================================

@bot.tree.command(
    name="testgreet",
    description="Tests your saved layout on yourself directly inside this channel."
)
async def testgreet(interaction: discord.Interaction):

    template, _ = load_welcome_config()

    test_embed = format_welcome_message(
        template,
        interaction.user,
        interaction.guild
    )

    await interaction.response.send_message(
        content="⚙️ **Running Welcomer Module Test...**",
        embed=test_embed
    )


# =========================================================
# MEMBER JOIN
# =========================================================

@bot.event
async def on_member_join(member: discord.Member):

    template, target_channel_id = load_welcome_config()

    welcome_channel = (
        member.guild.get_channel(target_channel_id)
        if target_channel_id
        else None
    )

    if not welcome_channel:
        welcome_channel = discord.utils.get(
            member.guild.text_channels,
            name="welcome"
        )

    if welcome_channel:

        join_embed = format_welcome_message(
            template,
            member,
            member.guild
        )

        await welcome_channel.send(
            content=member.mention,
            embed=join_embed
        )

    else:
        print(
            f"CRITICAL: Failed to greet {member.name}. "
            f"Setup a channel first with /customwelcome."
        )


# =========================================================
# !AUTORESPONDER
# =========================================================

@bot.command(
    name="autoresponder",
    help="Creates an automatic response. Usage: !autoresponder <message> <response>"
)
async def autoresponder(
    ctx,
    trigger: str = None,
    *,
    response: str = None
):

    if not trigger or not response:

        embed = discord.Embed(
            title="❌ Invalid Usage",
            description=(
                "Use the command like this:\n\n"
                "`!autoresponder hello Hello there!`\n\n"
                "When someone says `hello`, "
                "the bot will respond with `Hello there!`."
            ),
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)
        return

    guild_id = str(ctx.guild.id)

    if guild_id not in autoresponders:
        autoresponders[guild_id] = {}

    # Save trigger and response
    autoresponders[guild_id][trigger.lower()] = response

    save_autoresponders(autoresponders)

    embed = discord.Embed(
        title="🤖 Autoresponder Added",
        color=discord.Color.green()
    )

    embed.add_field(
        name="📩 Message",
        value=f"`{trigger}`",
        inline=False
    )

    embed.add_field(
        name="💬 Response",
        value=response,
        inline=False
    )

    await ctx.send(embed=embed)


# =========================================================
# AUTORESPONDER MESSAGE LISTENER
# =========================================================

@bot.event
async def on_message(message: discord.Message):

    # Ignore bots
    if message.author.bot:
        return

    # Check autoresponders
    if message.guild:

        guild_id = str(message.guild.id)

        guild_autoresponders = autoresponders.get(
            guild_id,
            {}
        )

        message_content = message.content.strip().lower()

        if message_content in guild_autoresponders:

            response = guild_autoresponders[message_content]

            try:
                await message.channel.send(response)

            except discord.Forbidden:
                print(
                    f"Missing permission to send messages in "
                    f"#{message.channel.name}"
                )

    # IMPORTANT:
    # This allows normal prefix commands such as !delete
    # and !autoresponder to continue working.
    await bot.process_commands(message)


# =========================================================
# !DELETE
# =========================================================

@bot.command(name="delete")
async def delete_ticket(ctx):

    if (
        ctx.channel.category
        and ctx.channel.category.name == "🎟️ TICKETS"
    ) or ctx.channel.name.startswith("ticket-"):

        await ctx.send(
            "🗑️ This ticket channel will be deleted in 5 seconds..."
        )

        await asyncio.sleep(5)

        await ctx.channel.delete()

    else:
        await ctx.send(
            "❌ This command can only be used inside a ticket channel."
        )


# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":

    keep_alive()

    token = os.environ.get("DISCORD_TOKEN")

    if token:
        bot.run(token)

    else:
        print("ERROR: Missing 'DISCORD_TOKEN' variable.")
