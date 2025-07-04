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
from cogs.counting import CountingCog
from cogs.guess_the_number import GuessNumberCog
import colorlog

# Setup colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(name_log_color)s%(name)s%(reset)s: [%(levelname)s] %(message_log_color)s%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={
        'message': {
            'DEBUG': 'white',
            'INFO': 'white',
            'WARNING': 'white',
            'ERROR': 'white',
            'CRITICAL': 'white',
        },
        'name': {
            'DEBUG': 'light_black',
            'INFO': 'light_black',
            'WARNING': 'light_black',
            'ERROR': 'light_black',
            'CRITICAL': 'light_black',
        }
    }
))
logging.basicConfig(level=logging.INFO, handlers=[handler])
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
        await self.add_cog(CountingCog(self))
        await self.add_cog(GuessNumberCog(self))

        # Add persistent views
        self.add_view(TicketSetupView(ticketcog=ticket_cog))
        self.add_view(PersistentCloseView(bot=self, ticketcog=ticket_cog))
        self.add_view(CloseThreadView(bot=self, ticketcog=ticket_cog))

        # Slash-Command-Sync while Setup
        synced = await self.tree.sync(guild=GUILD_ID)
        for cmd in synced:
            logger.info(f"---> Synced: {cmd.name} *cog / cmd")
            
    async def on_ready(self):
        logger.info("""
                   へ   JabUB   ╱|、
                ૮ - ՛)         (` - 7
                /  ⁻ |         |、⁻ 〵
            乀 (ˍ,ل ل          じしˍ, )ノ
        """)
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"---------------------------------------------------")

# Starting the bot
async def main():
    bot = Bot()
    await bot.start(TOKEN)
    
if __name__ == "__main__":
    asyncio.run(main())