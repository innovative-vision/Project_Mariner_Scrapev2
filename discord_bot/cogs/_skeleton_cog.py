"""
Skeleton cog — template for new features.

To add a new cog:
  1. Copy this file to cogs/your_feature.py  (no leading underscore)
  2. Rename SkeletonCog → YourFeatureCog and update Cog name=
  3. Add your slash commands / listeners inside the class
  4. The bot auto-discovers and loads all non-_ cogs on startup — no registration needed
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands


class SkeletonCog(commands.Cog, name="Skeleton"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Slash command example ─────────────────────────────────────────────────
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! `{latency_ms}ms`", ephemeral=True
        )

    # ── Context menu example (right-click a message) ──────────────────────────
    @app_commands.context_menu(name="Inspect Message")
    async def inspect_message(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        await interaction.response.send_message(
            f"Message ID: `{message.id}` | Author: `{message.author}`",
            ephemeral=True,
        )

    # ── Event listener example ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # Add message handling logic here


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SkeletonCog(bot))
