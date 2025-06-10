# ruff: noqa: F403 F405
import asyncio
import discord
from discord.ext import commands
from discord import Intents
import logging
from constants import *
from views.ticketviews import *
from cogs.tickets import TicketCog
from cogs.github import GithubCog
from cogs.music import MusicCog
from cogs.radio import RadioCog

# Setup logging
logging.basicConfig(level=logging.INFO, format='\033[32mINFO      \033[97m%(message)s')
logger = logging.getLogger(__name__)

# Get the guilds to sync
GUILD_ID = discord.Object(id=SYNC_SERVER)

# Default intents
intents = Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True
intents.members = True

# Define the bot
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="!", intents=intents, activity=discord.Activity(name="/github • /menu", type=discord.ActivityType.competing), *args, **kwargs)

    async def setup_hook(self):
        # Add the cogs to the bot
        ticket_cog = TicketCog(self)
        await self.add_cog(ticket_cog)
        await self.add_cog(GithubCog(self))
        await self.add_cog(MusicCog(self))
        await self.add_cog(RadioCog(self))

        # Add persistent views
        self.add_view(TicketSetupView(ticketcog=ticket_cog))
        self.add_view(PersistentCloseView(bot=self, ticketcog=ticket_cog))
        self.add_view(CloseThreadView(bot=self, ticketcog=ticket_cog))

        # Slash-Command-Sync beim Setup
        synced = await self.tree.sync(guild=GUILD_ID)
        logger.info(f"Synced {len(synced)} commands to guild: {GUILD_ID.id}")
        for cmd in synced:
            logger.info(f"Synced command: {cmd.name}")
            
    async def on_ready(self):
        logger.info(f'{self.user} is online!')
        logger.info("The Bot is ready!")

# Starting the bot
async def main():
    bot = Bot()
    await bot.start(TOKEN)
    
if __name__ == "__main__":
    asyncio.run(main())