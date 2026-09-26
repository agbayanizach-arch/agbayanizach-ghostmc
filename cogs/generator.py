import os
import discord
from discord import app_commands
from discord.ext import commands


def _safe_name(value: str) -> str:
    return "".join(c for c in value if c.isalnum() or c in " -_").strip().lower()


def _count_file(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


class GeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Scan Live Stock", style=discord.ButtonStyle.primary,
                       custom_id="generator:scan_stock", emoji="📦")
    async def scan_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_stock_embed(interaction, ephemeral=True)


class GeneratorSetupView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Free Generator", style=discord.ButtonStyle.success,
                       custom_id="generator:free", emoji="🎁")
    async def free(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FreeGeneratorView(self.bot)
        if not view.select_ready:
            return await interaction.response.send_message("No free services are currently available.", ephemeral=True)
        embed = discord.Embed(title="🎁 Free Service Selection",
                              description="Select a service below. Your account will be sent to your Discord DMs.",
                              color=0x00FFFF)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Premium Generator", style=discord.ButtonStyle.primary,
                       custom_id="generator:premium", emoji="💎")
    async def premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "💎 Premium Generator is currently unavailable until premium stock/access is configured.",
            ephemeral=True)

    @discord.ui.button(label="View Stock", style=discord.ButtonStyle.secondary,
                       custom_id="generator:stock", emoji="📊")
    async def stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_stock_embed(interaction, ephemeral=True)


class FreeGeneratorView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.select_ready = True
        self.add_item(FreeGeneratorSelect(bot))


class FreeGeneratorSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        stock_dir = os.path.join("stock_files", "free")
        os.makedirs(stock_dir, exist_ok=True)

        for filename in sorted(os.listdir(stock_dir)):
            if not filename.endswith(".txt"):
                continue
            count = _count_file(os.path.join(stock_dir, filename))
            if count <= 0:
                continue
            label = filename[:-4].replace("_", " ").replace("-", " ").title()[:100]
            options.append(discord.SelectOption(label=label,
                                                description=f"Available units: {count}"[:100],
                                                value=filename, emoji="🎁"))

        self.select_ready = bool(options)
        if not options:
            options = [discord.SelectOption(label="No stock available", value="none",
                                            description="There are currently no free accounts.")]

        super().__init__(placeholder="Select a free service", min_values=1, max_values=1,
                         options=options[:25], custom_id="generator:free_select",
                         disabled=not self.select_ready)

    async def callback(self, interaction: discord.Interaction):
        filename = self.values[0]
        if filename == "none":
            return await interaction.response.send_message("No stock is available right now.", ephemeral=True)

        path = os.path.join("stock_files", "free", filename)
        if not os.path.isfile(path):
            return await interaction.response.send_message("That service is no longer available.", ephemeral=True)

        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except OSError as e:
            return await interaction.response.send_message(f"Could not read stock: `{e}`", ephemeral=True)

        if not lines:
            return await interaction.response.send_message("That service is out of stock.", ephemeral=True)

        account = lines.pop(0)
        try:
            with open(path, "w", encoding="utf-8") as f:
                if lines:
                    f.write("\n".join(lines) + "\n")
        except OSError as e:
            return await interaction.response.send_message(f"Could not update stock: `{e}`", ephemeral=True)

        try:
            await interaction.user.send(
                f"🎁 **Your generated account**\nService: `{filename[:-4]}`\n```text\n{account}\n```"
            )
            await interaction.response.send_message("✅ Generated successfully. Check your DMs.", ephemeral=True)
        except discord.Forbidden:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(account + "\n" + "\n".join(lines) + ("\n" if lines else ""))
            except OSError:
                pass
            await interaction.response.send_message(
                "❌ I couldn't DM you. Please enable DMs and try again.", ephemeral=True
            )


async def send_stock_embed(interaction: discord.Interaction, ephemeral: bool = True):
    embed = discord.Embed(title="📦 Live Stock Status", description="Current available units.", color=0x3498DB)
    for category, title, emoji in (("free", "Free Generator", "🎁"), ("premium", "Premium Generator", "💎")):
        directory = os.path.join("stock_files", category)
        os.makedirs(directory, exist_ok=True)
        rows, total = [], 0
        for filename in sorted(os.listdir(directory)):
            if filename.endswith(".txt"):
                count = _count_file(os.path.join(directory, filename))
                total += count
                rows.append(f"• {filename[:-4].replace('_', ' ').title()}: `{count}`")
        value = f"**Total:** `{total}` units\n" + ("\n".join(rows) if rows else "No stock available.")
        embed.add_field(name=f"{emoji} {title}", value=value[:1024], inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)


class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_root = "stock_files"

    def get_stock_count(self, category):
        directory = os.path.join(self.stock_root, category)
        os.makedirs(directory, exist_ok=True)
        counts, total = {}, 0
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                count = _count_file(os.path.join(directory, filename))
                counts[filename[:-4].replace("_", " ").title()] = count
                total += count
        return counts, total

    @app_commands.command(name="generator", description="Open the generator interface")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_generator(self, interaction: discord.Interaction):
        embed = discord.Embed(title="☁️ Yet Cloud Generator",
                              description="Choose an option below.\n\n🎁 Free Generator\n💎 Premium Generator\n📊 View Stock",
                              color=0x00FFFF)
        await interaction.response.send_message(embed=embed, view=GeneratorSetupView(self.bot))

    @app_commands.command(name="stock", description="Show current stock")
    async def stock(self, interaction: discord.Interaction):
        await send_stock_embed(interaction, ephemeral=False)

    @app_commands.command(name="restock", description="Upload or replace a service stock file")
    @app_commands.choices(category=[app_commands.Choice(name="Free", value="free"),
                                   app_commands.Choice(name="Premium", value="premium")])
    @app_commands.describe(category="Stock category", service_name="Service name", file=".txt file with one account per line")
    @app_commands.checks.has_permissions(administrator=True)
    async def restock(self, interaction: discord.Interaction, category: str, service_name: str, file: discord.Attachment):
        if not file.filename.lower().endswith(".txt"):
            return await interaction.response.send_message("❌ Please upload a `.txt` file.", ephemeral=True)
        clean_name = _safe_name(service_name)
        if not clean_name:
            return await interaction.response.send_message("❌ Invalid service name.", ephemeral=True)
        directory = os.path.join(self.stock_root, category)
        os.makedirs(directory, exist_ok=True)
        target = os.path.join(directory, f"{clean_name}.txt")
        try:
            await file.save(target)
        except Exception as e:
            return await interaction.response.send_message(f"❌ Failed to save stock: `{e}`", ephemeral=True)
        added = _count_file(target)
        _, total = self.get_stock_count(category)
        await interaction.response.send_message(
            f"✅ **{service_name}** restocked in **{category}**.\nAdded: `{added}` units\nCategory total: `{total}` units.",
            ephemeral=True)

    @app_commands.command(name="remove_stock", description="Remove a service stock file")
    @app_commands.choices(category=[app_commands.Choice(name="Free", value="free"),
                                   app_commands.Choice(name="Premium", value="premium")])
    @app_commands.describe(category="Stock category", service_name="Service to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_stock(self, interaction: discord.Interaction, category: str, service_name: str):
        clean_name = _safe_name(service_name)
        target = os.path.join(self.stock_root, category, f"{clean_name}.txt")
        if not os.path.isfile(target):
            return await interaction.response.send_message(
                f"❌ No stock file found for `{service_name}` in `{category}`.", ephemeral=True)
        try:
            os.remove(target)
        except OSError as e:
            return await interaction.response.send_message(f"❌ Failed to remove stock: `{e}`", ephemeral=True)
        await interaction.response.send_message(f"✅ Removed `{service_name}` from `{category}`.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You need Administrator permission to use this command."
        else:
            print(f"Generator command error: {error!r}")
            message = f"❌ Command error: `{error}`"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Generator(bot))
