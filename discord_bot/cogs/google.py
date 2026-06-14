"""
Google Search cog — /google <query>

Returns top 10 results as two Discord embeds:
  Embed 1 — #1 result: title, snippet, image, TLDR
  Embed 2 — #2-10: compact list with TLDR per result
"""
from __future__ import annotations
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from utils.search import search_google
from utils.ai_providers import get_provider, AIProvider

EMBED_COLOUR = discord.Colour(0x5865F2)  # Discord blurple
MAX_SNIPPET = 400
MAX_TLDR = 220


class GoogleCog(commands.Cog, name="Google"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ai: AIProvider = get_provider()

    # ── /google ───────────────────────────────────────────────────────────────
    @app_commands.command(
        name="google",
        description="Search Google — top 10 results with AI TLDRs",
    )
    @app_commands.describe(query="What do you want to search for?")
    async def google(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)

        try:
            results = await search_google(query, num_results=10)
        except Exception as exc:
            await interaction.followup.send(
                f"Search failed: `{exc}`", ephemeral=True
            )
            return

        if not results:
            await interaction.followup.send("No results found.", ephemeral=True)
            return

        # Generate all TLDRs concurrently to minimise latency
        tldr_tasks = [
            self._ai.tldr(r["title"], r["snippet"], r["url"])
            for r in results
        ]
        try:
            tldrs: list[str] = list(await asyncio.gather(*tldr_tasks))
        except Exception:
            tldrs = ["TLDR unavailable."] * len(results)

        embeds = [
            self._build_top_embed(query, results[0], tldrs[0]),
            self._build_list_embed(results[1:], tldrs[1:]),
        ]
        await interaction.followup.send(embeds=embeds)

    # ── Embed builders ────────────────────────────────────────────────────────
    @staticmethod
    def _build_top_embed(
        query: str, result: dict, tldr: str
    ) -> discord.Embed:
        embed = discord.Embed(
            title=result["title"][:256],
            url=result["url"],
            description=result["snippet"][:MAX_SNIPPET],
            colour=EMBED_COLOUR,
        )
        embed.set_author(name=f"\U0001f50d  Google: {query[:90]}")
        if result.get("image"):
            embed.set_image(url=result["image"])
        embed.add_field(
            name="\U0001f4a1 TLDR",
            value=tldr[:MAX_TLDR],
            inline=False,
        )
        embed.set_footer(text="Result 1 of 10  •  Powered by Serper.dev")
        return embed

    @staticmethod
    def _build_list_embed(
        results: list[dict], tldrs: list[str]
    ) -> discord.Embed:
        embed = discord.Embed(title="More Results", colour=EMBED_COLOUR)
        for i, (result, tldr) in enumerate(zip(results, tldrs), start=2):
            embed.add_field(
                name=f"#{i} — {result['title'][:80]}",
                value=(
                    f"[\U0001f517 Link]({result['url']})\n"
                    f"\U0001f4a1 {tldr[:MAX_TLDR]}"
                ),
                inline=False,
            )
        embed.set_footer(text="Results 2 – 10 of 10")
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GoogleCog(bot))
