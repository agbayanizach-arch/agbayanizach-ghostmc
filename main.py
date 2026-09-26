import asyncio
import os
import discord
from discord.ext import commands
import config
import database
from utils import webserver

class UltimateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await database.init_db()
        for filename in sorted(os.listdir("./cogs")):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            await self.load_extension(f"cogs.{filename[:-3]}")

        guild_id = getattr(config, "GUILD_ID", None)
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {guild_id}: {len(synced)}")
        else:
            synced = await self.tree.sync()
            print(f"Global slash commands synced: {len(synced)}")

        from cogs.generator import GeneratorView, GeneratorSetupView
        from cogs.drops import DropView
        self.add_view(DropView(self))
        self.add_view(GeneratorView(self))
        self.add_view(GeneratorSetupView(self))
        self.loop.create_task(webserver.start_server())

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

async def main():
    bot = UltimateBot()
    async with bot:
        await bot.start(config.TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
