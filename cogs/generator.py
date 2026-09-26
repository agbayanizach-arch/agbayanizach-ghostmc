import os

import discord
from discord import app_commands
from discord.ext import commands

from utils import checks


class GeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

        self.add_item(
            discord.ui.Button(
                label="Free Generator",
                style=discord.ButtonStyle.link,
                url="https://discord.com",
                emoji="<:links:1473568567290232945>",
            )
        )

    @discord.ui.button(
        label="Scan Live Stock",
        style=discord.ButtonStyle.primary,
        custom_id="scan_stock",
        emoji="<a:stock2:1473339178652663959>",
    )
    async def scan_stock(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.response.defer(ephemeral=True)

            stock_root = "stock_files"
            categories = {
                "free": {
                    "emoji": "<:plants:1473339664424501417>",
                    "item_emoji": "<:iron:1473339698746490972>",
                    "title": "Free Generator",
                },
                "premium": {
                    "emoji": "<a:1427689167638499448:1473339630995902718>",
                    "item_emoji": "<:diamonds:1473339493456023683>",
                    "title": "Premium Generator",
                },
            }

            embed = discord.Embed(
                title="<a:stock2:1473339178652663959> Live Stock Status",
                description="Current unit availability in the **Yet Cloud** system.",
                color=0x3498DB,
            )

            for cat_key, config in categories.items():
                dir_path = os.path.join(stock_root, cat_key)
                total_units = 0
                items = []

                if os.path.isdir(dir_path):
                    for filename in sorted(os.listdir(dir_path)):
                        if not filename.endswith(".txt"):
                            continue

                        file_path = os.path.join(dir_path, filename)
                        try:
                            with open(file_path, "r", encoding="utf-8") as file:
                                count = sum(1 for line in file if line.strip())

                            total_units += count
                            service_name = filename[:-4].capitalize()
                            items.append(
                                f"{config['item_emoji']} {service_name}: {count} units"
                            )
                        except OSError:
                            items.append(
                                f"❌ {filename[:-4].capitalize()}: Error"
                            )

                items_text = "\n".join(items) if items else "No stock available."
                cat_value = f"**❯ Total:** {total_units} units\n{items_text}"

                embed.add_field(
                    name=f"{config['emoji']} {config['title']}",
                    value=cat_value,
                    inline=True,
                )

            guild_icon = (
                interaction.guild.icon.url
                if interaction.guild and interaction.guild.icon
                else None
            )
            embed.set_footer(
                text="[🔹] Yet Cloud | #1 Generator Server",
                icon_url=guild_icon,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in scan_stock: {e}")
            message = f"An error occurred while scanning stock: `{e}`"

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    message, ephemeral=True
                )
            else:
                await interaction.followup.send(message, ephemeral=True)


class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.restock_channel_id = 1472555118800142420
        self.stock_log_channel_id = 1472555176584810641
        self.stock_root = "stock_files"

    def get_stock_count(self, category):
        dir_path = os.path.join(self.stock_root, category)

        if not os.path.isdir(dir_path):
            return {}, 0

        counts = {}
        total = 0

        for filename in sorted(os.listdir(dir_path)):
            if not filename.endswith(".txt"):
                continue

            file_path = os.path.join(dir_path, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    count = sum(1 for line in file if line.strip())

                name = filename[:-4].capitalize()
                counts[name] = count
                total += count
            except OSError:
                continue

        return counts, total

    @app_commands.command(
        name="restock",
        description="Post a restock announcement to the designated channel",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Free", value="free"),
            app_commands.Choice(name="Premium", value="premium"),
        ]
    )
    @app_commands.describe(
        category="The category that was restocked",
        service_name="The specific service that was restocked (e.g. Minecraft)",
        file="Optional .txt file to upload/update the stock for this service",
    )
    @checks.is_owner_or_admin()
    async def restock(
        self,
        interaction: discord.Interaction,
        category: str = None,
        service_name: str = None,
        file: discord.Attachment = None,
    ):
        await interaction.response.defer(ephemeral=True)

        channel = self.bot.get_channel(self.restock_channel_id)
        if channel is None:
            return await interaction.followup.send(
                f"Error: Could not find restock channel with ID "
                f"`{self.restock_channel_id}`.",
                ephemeral=True,
            )

        if file:
            if not category or not service_name:
                return await interaction.followup.send(
                    "Please specify both `category` and `service_name` "
                    "when uploading a stock file!",
                    ephemeral=True,
                )

            if not file.filename.lower().endswith(".txt"):
                return await interaction.followup.send(
                    "Please upload only `.txt` files!",
                    ephemeral=True,
                )

            target_dir = os.path.join(self.stock_root, category)
            os.makedirs(target_dir, exist_ok=True)

            clean_name = "".join(
                c
                for c in service_name
                if c.isalnum() or c in (" ", "-", "_")
            ).strip().lower()

            if not clean_name:
                return await interaction.followup.send(
                    "Invalid service name.",
                    ephemeral=True,
                )

            target_path = os.path.join(target_dir, f"{clean_name}.txt")

            try:
                await file.save(target_path)

                with open(target_path, "r", encoding="utf-8") as stock_file:
                    added_count = sum(1 for line in stock_file if line.strip())

                _, cat_total = self.get_stock_count(category)

                log_channel = self.bot.get_channel(self.stock_log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="📥 Inventory Update: Stock Added",
                        description="A service's inventory has been replenished.",
                        color=0x2ECC71,
                        timestamp=discord.utils.utcnow(),
                    )
                    log_embed.add_field(
                        name="<a:staff1:1473339328246321282> **Authorized By:**",
                        value=interaction.user.mention,
                        inline=True,
                    )
                    log_embed.add_field(
                        name="<:folder1:1472852636603531274> **Service Identity:**",
                        value=f"{service_name.capitalize()} "
                        f"({category.capitalize()})",
                        inline=True,
                    )
                    log_embed.add_field(
                        name="<:box1:1472855146957754388> **Inventory Data:**",
                        value=(
                            f"❯ Items Added: `{added_count}`\n"
                            f"❯ New Category Total: `{cat_total}`"
                        ),
                        inline=False,
                    )
                    log_embed.add_field(
                        name="<a:file2:1473340156948529193> **Source Control:**",
                        value=f"`{clean_name}.txt`",
                        inline=False,
                    )

                    if interaction.guild and interaction.guild.icon:
                        log_embed.set_thumbnail(
                            url=interaction.guild.icon.url
                        )

                    log_embed.set_footer(
                        text="[🔹] Yet Cloud | Security & Audit System"
                    )
                    await log_channel.send(embed=log_embed)

            except Exception as e:
                return await interaction.followup.send(
                    f"Failed to save stock file: `{e}`",
                    ephemeral=True,
                )

        free_stock, free_total = self.get_stock_count("free")
        premium_stock, premium_total = self.get_stock_count("premium")

        if service_name:
            restock_msg = f"{service_name.capitalize()} Has Been Restocked!!"
        elif category:
            restock_msg = (
                f"The {category.capitalize()} Generator "
                "Has Been Restocked!!"
            )
        else:
            restock_msg = "The Generator Has Been Restocked!!"

        ping_role_id = 1472554999052636474
        ping_content = f"<@&{ping_role_id}> | **{restock_msg}**"

        embed = discord.Embed(
            title=f"**| {restock_msg}** "
            "<a:bell:1472906474643787786>",
            description=(
                "System fully restocked! Generate accounts quickly "
                "before they're gone! "
                "<a:star2:1473340889982930985>"
            ),
            color=0x00FFFF,
        )

        service_emojis = {}

        free_value = (
            f"<:arrmor2:1473339428675256320> Total Units: {free_total}\n"
        )
        if free_stock:
            for name, count in free_stock.items():
                emoji = service_emojis.get(
                    name, "<:iron:1473339698746490972>"
                )
                free_value += f"{emoji} {name}: {count} units\n"
        else:
            free_value += "No stock available."

        embed.add_field(
            name="<:plants:1473339664424501417> Free Generator",
            value=free_value,
            inline=True,
        )

        premium_value = (
            f"<:arrmor2:1473339428675256320> Total Units: {premium_total}\n"
        )
        if premium_stock:
            for name, count in premium_stock.items():
                emoji = service_emojis.get(
                    name, "<:diamonds:1473339493456023683>"
                )
                premium_value += f"{emoji} {name}: {count} units\n"
        else:
            premium_value += "No stock available."

        embed.add_field(
            name="<a:1427689167638499448:1473339630995902718> Premium Generator",
            value=premium_value,
            inline=True,
        )

        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.set_footer(
                text="[🔹] Yet Cloud | #1 Generator Server",
                icon_url=interaction.guild.icon.url,
            )
        else:
            embed.set_footer(text="[🔹] Yet Cloud | #1 Generator Server")

        view = GeneratorView(self.bot)
        await channel.send(
            content=ping_content,
            embed=embed,
            view=view,
        )

        await interaction.followup.send(
            f"Restock announcement sent to {channel.mention}!",
            ephemeral=True,
        )

    @app_commands.command(
        name="remove_stock",
        description="Remove a specific service and its stock file from a category",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Free", value="free"),
            app_commands.Choice(name="Premium", value="premium"),
        ]
    )
    @app_commands.describe(
        category="The category to remove the stock from",
        service_name="The name of the service to remove (e.g. Minecraft)",
    )
    @checks.is_owner_or_admin()
    async def remove_stock(
        self,
        interaction: discord.Interaction,
        category: str,
        service_name: str,
    ):
        clean_name = "".join(
            c
            for c in service_name
            if c.isalnum() or c in (" ", "-", "_")
        ).strip().lower()

        target_path = os.path.join(
            self.stock_root, category, f"{clean_name}.txt"
        )

        if not os.path.exists(target_path):
            return await interaction.response.send_message(
                f"Could not find a service named {service_name} "
                f"in the {category} category.",
                ephemeral=True,
            )

        try:
            os.remove(target_path)

            _, remaining_total = self.get_stock_count(category)

            log_channel = self.bot.get_channel(self.stock_log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="📤 Inventory Update: Service Removed",
                    description=(
                        "A service has been permanently removed "
                        "from the system."
                    ),
                    color=0xE74C3C,
                    timestamp=discord.utils.utcnow(),
                )
                log_embed.add_field(
                    name="<a:staff1:1473339328246321282> Authorized By:",
                    value=interaction.user.mention,
                    inline=True,
                )
                log_embed.add_field(
                    name="<:folder1:1472852636603531274> Service Identity:",
                    value=f"{service_name.capitalize()} "
                    f"({category.capitalize()})",
                    inline=True,
                )
                log_embed.add_field(
                    name="<:box1:1472855146957754388> Inventory Impact:",
                    value=(
                        f"❯ Remaining Category Stock: "
                        f"{remaining_total} items"
                    ),
                    inline=False,
                )

                if interaction.guild and interaction.guild.icon:
                    log_embed.set_thumbnail(
                        url=interaction.guild.icon.url
                    )

                log_embed.set_footer(
                    text="[🔹] Yet Cloud | Security & Audit System"
                )
                await log_channel.send(embed=log_embed)

            embed = discord.Embed(
                title="✅ Service Removed",
                description=(
                    f"Successfully removed {service_name.capitalize()} "
                    f"from the {category.capitalize()} generator."
                ),
                color=0x00FF00,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

        except Exception as e:
            await interaction.response.send_message(
                f"Failed to remove stock file: `{e}`",
                ephemeral=True,
            )

    @app_commands.command(
        name="generator",
        description="Setup the professional generator interface",
    )
    @checks.is_owner_or_admin()
    async def setup_generator(self, interaction: discord.Interaction):
        guild_icon = (
            interaction.guild.icon.url
            if interaction.guild and interaction.guild.icon
            else None
        )

        embed = discord.Embed(
            title=(
                "<a:star2:1473340889982930985> "
                "Welcome to Yet Cloud Generator "
                "<a:star2:1473340889982930985>"
            ),
            description=(
                "<a:arrow:1472906559024664750> "
                "Unlock a World of Services! "
                "<a:arrow:1472906559024664750>\n\n"
                "<a:gift:1472852654471512145> "
                "Free Generator: Access a variety of free accounts with ease. "
                "Perfect for casual users looking to explore.\n"
                "<:diamonds:1473339493456023683> "
                "Premium Generator: Dive into exclusive premium accounts "
                "for a top-tier experience.\n"
                "<a:stock2:1473339178652663959> "
                "View Stock: Check the current stock levels of free and "
                "premium services."
            ),
            color=0x00FFFF,
        )

        embed.add_field(
            name="💡 How to Use:",
            value=(
                "Select an option below to proceed. "
                "Ensure your DMs are enabled to receive credentials!"
            ),
            inline=False,
        )
        embed.add_field(
            name="📸 Vouch Reminder:",
            value=(
                "Vouch in <#1472555127054405774> within 10 minutes "
                "to avoid a 1-hour ban!"
            ),
            inline=False,
        )

        if guild_icon:
            embed.set_thumbnail(url=guild_icon)
            embed.set_footer(
                text="[🔹] Yet Cloud | #1 Generator Server",
                icon_url=guild_icon,
            )
        else:
            embed.set_footer(text="[🔹] Yet Cloud | #1 Generator Server")

        await interaction.response.send_message(
            embed=embed,
            view=GeneratorSetupView(self.bot),
        )


class GeneratorSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        options = [
            discord.SelectOption(
                label="Free Generator",
                description="Access our collection of free services",
                emoji="<a:gift:1472852654471512145>",
                value="free",
            ),
            discord.SelectOption(
                label="Premium Generator",
                description="Access exclusive high-tier accounts",
                emoji="<:diamonds:1473339493456023683>",
                value="premium",
            ),
            discord.SelectOption(
                label="View Stock",
                description="Check current availability of all services",
                emoji="<a:stock2:1473339178652663959>",
                value="stock",
            ),
        ]

        super().__init__(
            placeholder="💪 | Select Generator Type",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="gen_select",
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        if selected == "stock":
            await GeneratorView(self.bot).scan_stock.callback(
                GeneratorView(self.bot), interaction, None
            )
            return

        if selected == "free":
            supporter_role_id = 1472554985483931648
            get_role_channel_id = 1472555117369622620

            member = interaction.guild.get_member(interaction.user.id)
            has_role = member and any(
                role.id == supporter_role_id for role in member.roles
            )

            if not has_role:
                embed = discord.Embed(
                    title=(
                        "🚫 You need the Supporter role "
                        "to use the free generator! 👑"
                    ),
                    description=(
                        f"### Get It In <#{get_role_channel_id}>\n\n"
                        "🚫 Access Denied"
                    ),
                    color=0xFF0000,
                )

                if interaction.guild and interaction.guild.icon:
                    embed.set_author(
                        name=f"{interaction.guild.name} Ultimate Generator",
                        icon_url=interaction.guild.icon.url,
                    )
                    embed.set_footer(
                        text="[🔹] Yet Cloud | #1 Generator Server",
                        icon_url=interaction.guild.icon.url,
                    )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)

            embed = discord.Embed(
                title="<a:gift:1472852654471512145> Free Service Selection",
                description=(
                    "<a:arrow:1472906559024664750> "
                    "Welcome to the Free Generator! "
                    "<a:arrow:1472906559024664750>\n\n"
                    "<a:gift:1472852654471512145> "
                    "Select a service from the dropdown to receive "
                    "your credentials!\n"
                    "👀 Your credentials will be sent via DM. "
                    "Ensure your DMs are enabled!"
                ),
                color=0x00FFFF,
            )

            guild_icon = (
                interaction.guild.icon.url
                if interaction.guild and interaction.guild.icon
                else None
            )

            if guild_icon:
                embed.set_author(
                    name=f"{interaction.guild.name} Ultimate Generator",
                    icon_url=guild_icon,
                )
                embed.set_thumbnail(url=guild_icon)
                embed.set_footer(
                    text="[🔹] Yet Cloud | #1 Generator Server",
                    icon_url=guild_icon,
                )

            embed.add_field(
                name="💡 Tip:",
                value=(
                    "Vouch in <#1472555127054405774> within 10 minutes "
                    "to avoid a 1-hour ban!"
                ),
                inline=False,
            )

            view = FreeGeneratorView(self.bot)

            if not view.select_ready:
                await interaction.followup.send(
                    "No free services are currently available. "
                    "Please check back later!",
                    ephemeral=True,
                )
                return

            await interaction.followup.send(
                embed=embed,
                view=view,
                ephemeral=True,
            )
            return

        if selected == "premium":
            embed = discord.Embed(
                title="<:diamonds:1473339493456023683> Premium Generator Access",
                description=(
                    "You have selected the Premium Network. "
                    "Access to these high-tier assets is restricted "
                    "to authorized subscribers.\n\n"
                    "👑 How to Access:\n"
                    "1. Purchase a subscription in "
                    "<#1472555117369622620>\n"
                    "2. Open a ticket to verify your transaction.\n"
                    "3. Enjoy unlimited premium generation!"
                ),
                color=0x00FFFF,
            )
            embed.set_footer(text="[🔹] Yet Cloud | Elite Tier")

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )


class FreeGeneratorSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        stock_dir = os.path.join("stock_files", "free")

        if os.path.isdir(stock_dir):
            for filename in sorted(os.listdir(stock_dir)):
                if not filename.endswith(".txt"):
                    continue

                count = 0
                try:
                    with open(
                        os.path.join(stock_dir, filename),
                        "r",
                        encoding="utf-8",
                    ) as file:
                        count = sum(1 for line in file if line.strip())
                except OSError:
                    pass

                name = filename[:-4].capitalize()
                options.append(
                    discord.SelectOption(
                        label=name,
                        description=f"Available Units: {count}",
                        emoji="<a:gift:1472852654471512145>",
                        value=filename,
                    )
                )

        if not options:
            options.append(
                discord.SelectOption(
                    label="No services available",
                    value="none",
                )
            )
            self.disabled = True
            self.select_ready = False
        else:
            self.select_ready = True

        super().__init__(
            placeholder="🧤 | Select a Free Service",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="free_select",
            disabled=getattr(self, "disabled", False),
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "No services are currently available.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        filename = self.values[0]
        service_name = filename[:-4].upper()
        stock_file = os.path.join("stock_files", "free", filename)

        if not os.path.exists(stock_file):
            embed = discord.Embed(
                title="❌ Error",
                description=(
                    f"The service {service_name} is currently out of stock."
                ),
                color=0xFF0000,
            )
            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )
            return

        try:
            with open(stock_file, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]

            if not lines:
                embed = discord.Embed(
                    title="❌ Error",
                    description=(
                        f"The service {service_name} is currently out of stock."
                    ),
                    color=0xFF0000,
                )
                await interaction.followup.send(
                    embed=embed,
                    ephemeral=True,
                )
                return

            account = lines.pop(0)

            with open(stock_file, "w", encoding="utf-8") as file:
                if lines:
                    file.write("\n".join(lines) + "\n")

            try:
                await interaction.user.send(
                    f"Your **{service_name}** account:\n```{account}```"
                )
            except discord.Forbidden:
                # Put the account back if DMs are closed.
                with open(stock_file, "w", encoding="utf-8") as file:
                    file.write("\n".join([account] + lines) + "\n")

                await interaction.followup.send(
                    "I couldn't DM you. Please enable your DMs and try again.",
                    ephemeral=True,
                )
                return

            await interaction.followup.send(
                f"✅ Your **{service_name}** account was sent to your DMs.",
                ephemeral=True,
            )

        except OSError as e:
            await interaction.followup.send(
                f"Failed to read/update stock: `{e}`",
                ephemeral=True,
            )


class GeneratorSetupView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(GeneratorSelect(bot))


class FreeGeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.select = FreeGeneratorSelect(bot)
        self.add_item(self.select)
        self.select_ready = self.select.select_ready


async def setup(bot):
    """Required by discord.py when loading this cog as an extension."""
    await bot.add_cog(Generator(bot))
