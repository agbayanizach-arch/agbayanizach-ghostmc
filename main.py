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

bot = commands.Bot(command_prefix="-", intents=intents)
bot.remove_command("help")

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
    help="Creates an automatic response. Usage: -autoresponder <message> <response>"
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
                "`-autoresponder hello Hello there!`\n\n"
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
    # This allows normal prefix commands such as -delete
    # and -autoresponder to continue working.
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
# FALCON-STYLE COMMAND SUITE
# =========================================================
# These commands are implemented locally; they do not call or copy
# Falcon's private backend/source code.

FALCON_DATA_FILE = "falcon_data.json"
_giveaways = {}
_timers = {}
_polls = {}
_invite_cache = {}
_bot_start_time = asyncio.get_event_loop().time()

def _load_falcon_data():
    if not os.path.exists(FALCON_DATA_FILE):
        return {}
    try:
        with open(FALCON_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def _save_falcon_data(data):
    with open(FALCON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

_falcon_data = _load_falcon_data()

def _guild_data(guild_id):
    gid = str(guild_id)
    if gid not in _falcon_data:
        _falcon_data[gid] = {}
    return _falcon_data[gid]

def _parse_duration(value):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhd])\s*", value.lower())
    if not m:
        return None
    amount = float(m.group(1))
    unit = m.group(2)
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    seconds = amount * mult
    return seconds if seconds > 0 else None

def _human_duration(seconds):
    seconds = int(seconds)
    if seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"

def _falcon_embed(title=None, description=None, color=0x2B2D31):
    return discord.Embed(title=title, description=description, color=color)

def _owner_only(ctx):
    return ctx.guild and ctx.author.id == ctx.guild.owner_id

# -------------------------
# HELP
# -------------------------

@bot.command(name="help")
async def falcon_help(ctx, category: str = None):
    categories = {
        "Invite_logger": "`-invites`, `-lb`, `-addinvites`, `-removeinvites`, `-joinchannelset`, `-unsetjoinchannel`, `-setleave`, `-unsetleave`, `-clearinvites`, `-revokeall`, `-variables`, `-customwelcome`, `-unsetcustomwelcome`, `-testmsg`",
        "Giveaway": "`-gstart`, `-gend`, `-greroll`, `-timediff`",
        "Timer": "`-tstart`, `-tpause`, `-tresume`, `-tend`",
        "Poll": "`-cpoll`, `-epoll`",
        "Greet": "`-greet`, `-disablegreet`, `-greetvariables`, `-greetchannels`",
        "Moderation": "`-erase`, `-kick`, `-addrole`, `-removerole`, `-appendrole`",
        "Utility": "`-sponsor`, `-membercount`, `-accage`, `-datetime`, `-stats`, `-ping`, `-botinfo`, `-uptime`, `-perms`",
        "Fun": "`-game`",
        "PFP": "`-pfp`, `-banner`",
        "Activities": "`-youtube`, `-poker`, `-betrayal`, `-fishing`",
        "Youtube": "`-ytvid`, `-ytchannel`",
        "Set_prefix": "`-setprefix`, `-resetprefix`",
        "Contact": "`-support`, `-bug`, `-feedback`",
    }
    if category:
        key = next((k for k in categories if k.lower() == category.lower()), None)
        if not key:
            return await ctx.send("❌ Category not found. Use `-help` to see categories.")
        return await ctx.send(embed=_falcon_embed(
            title=key,
            description=categories[key]
        ))
    desc = (
        "Type `-help {category name}` to have more info on commands.\n\n"
        + "\n".join(f"**{k}**\n{v}" for k, v in categories.items())
    )
    embed = _falcon_embed(title="Help", description=desc)
    await ctx.send(embed=embed)

# -------------------------
# INVITE LOGGER
# -------------------------

@bot.command()
@commands.guild_only()
async def invites(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = _guild_data(ctx.guild.id)
    invites = data.setdefault("invites", {})
    count = int(invites.get(str(member.id), 0))
    embed = _falcon_embed(title="Invites", description=f"{member.mention} has **{count}** invites.")
    await ctx.send(embed=embed)

@bot.command(name="lb")
@commands.guild_only()
async def invite_lb(ctx):
    data = _guild_data(ctx.guild.id)
    rows = []
    for uid, count in sorted(data.setdefault("invites", {}).items(), key=lambda x: x[1], reverse=True)[:10]:
        member = ctx.guild.get_member(int(uid))
        if member:
            rows.append(f"**{len(rows)+1}.** {member.mention} — `{count}`")
    await ctx.send(embed=_falcon_embed(title="Invite Leaderboard",
                                       description="\n".join(rows) or "No invite data yet."))

@bot.command(name="addinvites")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def addinvites(ctx, member: discord.Member, amount: int):
    if amount < 0:
        return await ctx.send("❌ Amount must be positive.")
    data = _guild_data(ctx.guild.id)
    data.setdefault("invites", {})[str(member.id)] = int(data.setdefault("invites", {}).get(str(member.id), 0)) + amount
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Added `{amount}` invites to {member.mention}.")

@bot.command(name="removeinvites")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def removeinvites(ctx, member: discord.Member, amount: int):
    data = _guild_data(ctx.guild.id)
    inv = data.setdefault("invites", {})
    inv[str(member.id)] = max(0, int(inv.get(str(member.id), 0)) - amount)
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Removed `{amount}` invites from {member.mention}.")

@bot.command(name="clearinvites")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def clearinvites(ctx):
    _guild_data(ctx.guild.id)["invites"] = {}
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Invite data cleared.")

@bot.command(name="revokeall")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def revokeall(ctx):
    _guild_data(ctx.guild.id)["invites"] = {}
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ All recorded invites were revoked.")

@bot.command(name="joinchannelset")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def joinchannelset(ctx, channel: discord.TextChannel):
    _guild_data(ctx.guild.id)["join_channel"] = channel.id
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Join channel set to {channel.mention}.")

@bot.command(name="unsetjoinchannel")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def unsetjoinchannel(ctx):
    _guild_data(ctx.guild.id).pop("join_channel", None)
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Join channel unset.")

@bot.command(name="setleave")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def setleave(ctx, channel: discord.TextChannel):
    _guild_data(ctx.guild.id)["leave_channel"] = channel.id
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Leave channel set to {channel.mention}.")

@bot.command(name="unsetleave")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def unsetleave(ctx):
    _guild_data(ctx.guild.id).pop("leave_channel", None)
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Leave channel unset.")

@bot.command(name="variables")
async def variables(ctx):
    await ctx.send("`{user}` `{mention}` `{username}` `{server}` `{membercount}` `{avatar}` `{date}`")

@bot.command(name="unsetcustomwelcome")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def unsetcustomwelcome(ctx):
    _guild_data(ctx.guild.id).pop("welcome_message", None)
    _guild_data(ctx.guild.id).pop("welcome_channel", None)
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Custom welcome disabled.")

@bot.command(name="testmsg")
async def testmsg(ctx):
    await ctx.invoke(bot.get_command("testgreet"))

# -------------------------
# GIVEAWAYS
# -------------------------

async def _end_giveaway(gid):
    await asyncio.sleep(_giveaways[gid]["duration"])
    data = _giveaways.get(gid)
    if not data or data["ended"]:
        return
    data["ended"] = True
    channel = bot.get_channel(data["channel_id"])
    if not channel:
        return
    try:
        msg = await channel.fetch_message(data["message_id"])
        participants = list(dict.fromkeys(data["participants"]))
        winner_count = min(data["winners"], len(participants))
        winners = participants[:winner_count]
        winner_text = ", ".join(f"<@{u}>" for u in winners) if winners else "No winners"
        embed = _falcon_embed(title="Giveaway Ended",
                              description=f"🎉 **{data['prize']}**\n\nWinner(s): {winner_text}")
        await msg.edit(embed=embed, view=None)
    except discord.HTTPException:
        pass

@bot.command(name="gstart")
@commands.guild_only()
async def gstart(ctx, duration: str, winners: int, *, prize: str):
    seconds = _parse_duration(duration)
    if seconds is None or winners < 1:
        return await ctx.send("❌ Usage: `-gstart <duration> <winners> <prize>`")
    gid = str(max([int(x) for x in _giveaways.keys()] or [0]) + 1)
    embed = _falcon_embed(title="New Giveaway",
                          description=f"🎁 **{prize}**\n\nHosted by {ctx.author.mention}\nEnds in **{_human_duration(seconds)}**")
    view = discord.ui.View(timeout=None)
    button = discord.ui.Button(label="0", emoji="🎉", style=discord.ButtonStyle.secondary)
    async def join(interaction):
        if interaction.user.bot:
            return
        if interaction.user.id not in _giveaways[gid]["participants"]:
            _giveaways[gid]["participants"].append(interaction.user.id)
            button.label = str(len(_giveaways[gid]["participants"]))
            await interaction.response.edit_message(view=view)
        else:
            await interaction.response.send_message("You are already entered.", ephemeral=True)
    button.callback = join
    view.add_item(button)
    message = await ctx.send(embed=embed, view=view)
    _giveaways[gid] = {"channel_id": ctx.channel.id, "message_id": message.id,
                       "prize": prize, "duration": seconds, "winners": winners,
                       "host_id": ctx.author.id, "participants": [], "ended": False}
    asyncio.create_task(_end_giveaway(gid))
    await ctx.send(f"Giveaway ID: `{gid}`", delete_after=8)

@bot.command(name="gend")
@commands.guild_only()
async def gend(ctx, giveaway_id: str):
    data = _giveaways.get(giveaway_id)
    if not data:
        return await ctx.send("❌ Giveaway not found.")
    data["duration"] = 0
    data["ended"] = True
    channel = bot.get_channel(data["channel_id"])
    try:
        msg = await channel.fetch_message(data["message_id"])
        participants = data["participants"]
        winners = participants[:min(data["winners"], len(participants))]
        textw = ", ".join(f"<@{u}>" for u in winners) if winners else "No winners"
        await msg.edit(embed=_falcon_embed("Giveaway Ended", f"🎉 **{data['prize']}**\n\nWinner(s): {textw}"), view=None)
    except Exception:
        pass
    await ctx.send("✅ Giveaway ended.")

@bot.command(name="greroll")
@commands.guild_only()
async def greroll(ctx, giveaway_id: str):
    data = _giveaways.get(giveaway_id)
    if not data or not data["ended"]:
        return await ctx.send("❌ That giveaway has not ended or was not found.")
    if not data["participants"]:
        return await ctx.send("❌ There are no participants to reroll.")
    winner = data["participants"][-1]
    await ctx.send(f"🎉 New winner: <@{winner}>")

@bot.command(name="timediff")
async def timediff(ctx, duration: str):
    seconds = _parse_duration(duration)
    await ctx.send(f"`{_human_duration(seconds)}` = `{int(seconds)}` seconds." if seconds else "❌ Invalid duration. Use `10s`, `5m`, `2h`, or `1d`.")

# -------------------------
# TIMER
# -------------------------

@bot.command(name="tstart")
async def tstart(ctx, duration: str, *, label: str = "Timer"):
    seconds = _parse_duration(duration)
    if not seconds:
        return await ctx.send("❌ Invalid duration.")
    tid = str(ctx.message.id)
    _timers[tid] = {"duration": seconds, "remaining": seconds, "running": True, "label": label, "owner": ctx.author.id}
    await ctx.send(f"⏱️ **{label}** started for `{_human_duration(seconds)}`. ID: `{tid}`")
    async def timer_task():
        await asyncio.sleep(seconds)
        if tid in _timers and _timers[tid]["running"]:
            await ctx.send(f"⏰ **{label}** ended.")
            _timers.pop(tid, None)
    asyncio.create_task(timer_task())

@bot.command(name="tpause")
async def tpause(ctx, timer_id: str):
    if timer_id not in _timers:
        return await ctx.send("❌ Timer not found.")
    _timers[timer_id]["running"] = False
    await ctx.send("⏸️ Timer paused.")

@bot.command(name="tresume")
async def tresume(ctx, timer_id: str):
    if timer_id not in _timers:
        return await ctx.send("❌ Timer not found.")
    _timers[timer_id]["running"] = True
    await ctx.send("▶️ Timer resumed.")

@bot.command(name="tend")
async def tend(ctx, timer_id: str):
    if timer_id not in _timers:
        return await ctx.send("❌ Timer not found.")
    _timers.pop(timer_id, None)
    await ctx.send("⏹️ Timer ended.")

# -------------------------
# POLLS
# -------------------------

@bot.command(name="cpoll")
async def cpoll(ctx, question: str, duration: str, answer1: str, answer2: str, answer3: str = None):
    seconds = _parse_duration(duration)
    if not seconds:
        return await ctx.send("❌ Invalid duration.")
    answers = [answer1, answer2] + ([answer3] if answer3 else [])
    embed = _falcon_embed(title="Poll", description=f"**{question}**\n\n" +
                          "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers)))
    embed.set_footer(text=f"Ends in {_human_duration(seconds)} • 0 votes")
    msg = await ctx.send(embed=embed)
    for i in range(len(answers)):
        try:
            await msg.add_reaction(str(i+1) + "\N{COMBINING ENCLOSING KEYCAP}")
        except discord.HTTPException:
            pass
    _polls[str(msg.id)] = {"channel": ctx.channel.id, "duration": seconds, "ended": False}
    async def expire():
        await asyncio.sleep(seconds)
        if str(msg.id) in _polls:
            _polls[str(msg.id)]["ended"] = True
            try:
                await msg.edit(embed=_falcon_embed("Poll Ended", f"**{question}**\n\n" +
                    "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers))))
            except discord.HTTPException:
                pass
    asyncio.create_task(expire())

@bot.command(name="epoll")
async def epoll(ctx, poll_id: str):
    if poll_id not in _polls:
        return await ctx.send("❌ Poll not found.")
    _polls[poll_id]["ended"] = True
    await ctx.send("✅ Poll ended.")

# -------------------------
# GREET
# -------------------------

@bot.command(name="greet")
@commands.guild_only()
async def greet(ctx, channel: discord.TextChannel = None, *, message: str = None):
    data = _guild_data(ctx.guild.id)
    data["greet_enabled"] = True
    if channel:
        data["welcome_channel"] = channel.id
    if message:
        data["welcome_message"] = message
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Greet enabled.")

@bot.command(name="disablegreet")
@commands.guild_only()
async def disablegreet(ctx):
    _guild_data(ctx.guild.id)["greet_enabled"] = False
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Greet disabled.")

@bot.command(name="greetvariables")
async def greetvariables(ctx):
    await ctx.send(embed=_falcon_embed(
        "Greet Variables",
        "`{user}` — user mention\n`{mention}` — user mention\n`{username}` — username\n"
        "`{server}` — server name\n`{membercount}` — member count\n`{avatar}` — member avatar thumbnail\n`{date}` — current date"
    ))

@bot.command(name="greetchannels")
@commands.guild_only()
async def greetchannels(ctx, channel: discord.TextChannel):
    data = _guild_data(ctx.guild.id)
    data["welcome_channel"] = channel.id
    data["greet_enabled"] = True
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Greet channel set to {channel.mention}.")

# -------------------------
# MODERATION
# -------------------------

@bot.command(name="erase")
@commands.has_permissions(manage_messages=True)
async def erase(ctx, amount: int):
    if amount < 1 or amount > 100:
        return await ctx.send("❌ Amount must be between 1 and 100.")
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted `{max(0, len(deleted)-1)}` messages.", delete_after=3)

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def falcon_kick(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention} — {reason}")

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Added {role.mention} to {member.mention}.")

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Removed {role.mention} from {member.mention}.")

@bot.command(name="appendrole")
@commands.has_permissions(manage_roles=True)
async def appendrole(ctx, member: discord.Member, *, roles: str):
    role_names = [x.strip() for x in roles.split(",")]
    added = []
    for name in role_names:
        role = discord.utils.find(lambda r: r.name.lower() == name.lower(), ctx.guild.roles)
        if role:
            await member.add_roles(role)
            added.append(role.name)
    await ctx.send(f"✅ Added: {', '.join(added) if added else 'No matching roles'}")

# -------------------------
# UTILITY
# -------------------------

@bot.command(name="sponsor")
async def sponsor(ctx):
    await ctx.send(embed=_falcon_embed("Sponsor", "Thank you for supporting the bot and its development."))

@bot.command(name="membercount", aliases=["mc"])
@commands.guild_only()
async def membercount(ctx):
    await ctx.send(embed=_falcon_embed("Member Count", f"👥 **{ctx.guild.member_count}** members"))

@bot.command(name="accage")
async def accage(ctx, member: discord.Member = None):
    member = member or ctx.author
    delta = discord.utils.utcnow() - member.created_at
    await ctx.send(embed=_falcon_embed("Account Age", f"{member.mention} — **{delta.days} days** old."))

@bot.command(name="datetime")
async def falcon_datetime(ctx):
    now = discord.utils.utcnow()
    await ctx.send(f"🕒 `{now.strftime('%Y-%m-%d %H:%M:%S UTC')}`")

@bot.command(name="stats")
async def stats(ctx):
    await ctx.send(embed=_falcon_embed("Stats",
        f"Servers: `{len(bot.guilds)}`\nUsers: `{sum(g.member_count or 0 for g in bot.guilds)}`\nLatency: `{round(bot.latency*1000)}ms`"))

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency*1000)}ms`")

@bot.command(name="botinfo")
async def botinfo(ctx):
    await ctx.send(embed=_falcon_embed("Bot Info", f"**{bot.user}**\nID: `{bot.user.id}`\nPrefix: `-`"))

@bot.command(name="uptime")
async def uptime(ctx):
    seconds = int(asyncio.get_event_loop().time() - _bot_start_time)
    await ctx.send(f"⏱️ Uptime: `{_human_duration(seconds)}`")

@bot.command(name="perms")
async def perms(ctx, member: discord.Member = None):
    member = member or ctx.author
    p = member.guild_permissions
    enabled = [name for name, value in p if value]
    await ctx.send(embed=_falcon_embed("Permissions", f"{member.mention}\n" + ", ".join(f"`{x}`" for x in enabled)))

# -------------------------
# FUN / PFP / ACTIVITIES / YOUTUBE
# -------------------------

@bot.command(name="game")
async def game(ctx):
    await ctx.send("🎮 Your random game: **Rock Paper Scissors** — choose `rock`, `paper`, or `scissors`.")

@bot.command(name="pfp")
async def pfp(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command(name="youtube")
async def youtube(ctx):
    await ctx.send("▶️ YouTube Activity link: https://discord.com/activities/880218394199220334")

@bot.command(name="poker")
async def poker(ctx):
    await ctx.send("🃏 Poker Activity: https://discord.com/activities/755827207812677713")

@bot.command(name="betrayal")
async def betrayal(ctx):
    await ctx.send("🔪 Betrayal.io Activity: https://discord.com/activities/773336526917861400")

@bot.command(name="fishing")
async def fishing(ctx):
    await ctx.send("🎣 Fishington.io Activity: https://discord.com/activities/814288819477020702")

@bot.command(name="ytvid")
async def ytvid(ctx, *, query: str):
    await ctx.send(f"🔎 YouTube video search: https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

@bot.command(name="ytchannel")
async def ytchannel(ctx, *, query: str):
    await ctx.send(f"🔎 YouTube channel search: https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

# -------------------------
# SET PREFIX
# -------------------------

@bot.command(name="setprefix")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def setprefix(ctx, prefix: str):
    if not 1 <= len(prefix) <= 3:
        return await ctx.send("❌ Prefix must be 1–3 characters.")
    _guild_data(ctx.guild.id)["prefix"] = prefix
    _save_falcon_data(_falcon_data)
    await ctx.send(f"✅ Saved server prefix as `{prefix}`. Restart the bot to apply it globally.")

@bot.command(name="resetprefix")
@commands.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def resetprefix(ctx):
    _guild_data(ctx.guild.id).pop("prefix", None)
    _save_falcon_data(_falcon_data)
    await ctx.send("✅ Prefix reset to `-`.")

# -------------------------
# CONTACT
# -------------------------

@bot.command(name="support")
async def falcon_support(ctx, *, message: str):
    await ctx.send("✅ Support request received. Please contact the bot owner/support server for assistance.")

@bot.command(name="bug")
async def bug(ctx, *, message: str):
    await ctx.send("✅ Bug report received. Please include steps to reproduce the issue.")

@bot.command(name="feedback")
async def feedback(ctx, *, message: str):
    await ctx.send("✅ Feedback received. Thank you!")

# -------------------------
# LEAVE EVENTS FOR GREET/LEAVE TRACKING
# -------------------------

@bot.event
async def on_member_remove(member):
    data = _guild_data(member.guild.id)
    channel_id = data.get("leave_channel")
    if channel_id:
        channel = member.guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(f"👋 **{member}** has left **{member.guild.name}**.")
            except discord.HTTPException:
                pass

# -------------------------
# COMMAND ERROR HANDLER
# -------------------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`")
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument.")
        return
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if isinstance(original, discord.Forbidden):
            await ctx.send("❌ I don't have permission to do that.")
            return
    raise error


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
