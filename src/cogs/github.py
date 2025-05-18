# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
from util.ticket_creator import *

class GithubCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # The /github command
    @app_commands.command(name="github", description="Github of this bot")
    async def github(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Github Repository",
            description="The github repo of the bot: [github.com/nino749/JabUB](https://github.com/nino749/JabUB)",
            color=0x00ff00
        )
        embed.set_author(name="Github", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
        embed.set_footer(text="JabUB.css | by www.ninoio.gay")
        embed.set_thumbnail(url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    async def cog_load(self):
        self.bot.tree.add_command(self.github, guild=discord.Object(id=SYNC_SERVER))