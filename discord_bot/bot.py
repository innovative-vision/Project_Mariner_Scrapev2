import discord
from discord.ext import commands
from pathlib import Path
from config import Config


class MarinerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=Config.PREFIX, intents=intents)

    async def setup_hook(self):
        cogs_dir = Path(__file__).parent / "cogs"
        for cog_file in sorted(cogs_dir.glob("*.py")):
            if cog_file.stem.startswith("_"):
                continue
            cog_name = f"cogs.{cog_file.stem}"
            try:
                await self.load_extension(cog_name)
                print(f"[+] Loaded cog: {cog_name}")
            except Exception as e:
                print(f"[-] Failed to load {cog_name}: {e}")
        await self.tree.sync()
        print("[+] Slash commands synced globally")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /google",
            )
        )


bot = MarinerBot()

if __name__ == "__main__":
    bot.run(Config.DISCORD_TOKEN)
