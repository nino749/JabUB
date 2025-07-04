# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
from util.ticket_creator import *
from util.queue import *
from util.play_next import *
from embeds import *
from texts import *

class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="radio", description="Play a radio stream")
    @app_commands.describe(choice="Choose a Radio sender, or type in your own!")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Charts, WW", value="http://streams.bigfm.de/bigfm-charts-128-aac?usid=0-0-H-A-D-30"),
        app_commands.Choice(name="DLF, Ger", value="https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3?aggregator=web"),
        app_commands.Choice(name="NDR, Ger", value="http://icecast.ndr.de/ndr/ndr1radiomv/rostock/mp3/128/stream.mp3 "),
        app_commands.Choice(name="RBB, Ger", value="http://antennebrandenburg.de/livemp3"),
        app_commands.Choice(name="RADIO BOB!, Ger", value="http://streams.radiobob.de/bob-live/mp3-192/mediaplayer"),
        app_commands.Choice(name="88vier, Ger", value="http://ice.rosebud-media.de:8000/88vier-low"),
        app_commands.Choice(name="bigFM, Ger", value="http://streams.bigfm.de/bigfm-deutschland-128-aac?usid=0-0-H-A-D-30"),
        app_commands.Choice(name="1 Live, Ger", value="http://wdr-1live-live.icecast.wdr.de/wdr/1live/live/mp3/128/stream.mp3"),
        app_commands.Choice(name="WDR 3, Ger", value="http://wdr-wdr3-live.icecast.wdr.de/wdr/wdr3/live/mp3/256/stream.mp3"),
        app_commands.Choice(name="BBC, GB", value="http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"),
        app_commands.Choice(name="BFBS, GB", value="http://tx.sharp-stream.com/icecast.php?i=ssvcbfbs1.aac"),
        app_commands.Choice(name="ENERGY98, USA", value="http://mp3tx.duplexfx.com:8800"),
    ])
    @app_commands.describe(url="URL of the radio stream, a list: (https://wiki.ubuntuusers.de/Internetradio/Stationen/)")
    async def radio_command(self, interaction: discord.Interaction, url: str | None = None, choice: app_commands.Choice[str] | None = None):
        if interaction.user.voice is None:
            await interaction.response.send_message(
                embed=simple_embed(f"{INFO_EMOJI} You must be in a voice channel!"),
                ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected() and voice_client.channel != voice_channel:
            await interaction.response.send_message(
                embed=simple_embed(f"{INFO_EMOJI} I'm already in another voice channel."),
                ephemeral=True
            )
            return
        elif voice_client and voice_client.is_playing():
            voice_client.stop()

        if choice:
            stream_url = choice.value
        elif url:
            stream_url = url
        else:
            await interaction.followup.send(embed=simple_embed(f"{INFO_EMOJI} Please select a radio."), ephemeral=True)
            return
        
        await interaction.response.send_message(f"Loading the radio stream: {url} {LOADING_EMOJI}", ephemeral=True)

        if stream_url.lower().endswith(".pls"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(stream_url) as response:
                        if response.status == 200:
                            pls_content = await response.text()
                            for line in pls_content.splitlines():
                                if line.lower().startswith("file1="):
                                    stream_url = line.split("=", 1)[1]
                                    break
                        else:
                            await interaction.followup.send(
                                embed=simple_embed(f"Failed to load PLS file: HTTP {response.status}"),
                                ephemeral=True
                            )
                            return
                        
            except aiohttp.ClientError as e:
                await interaction.followup.send(
                    embed=simple_embed(f"Error while fetching the PLS file: {e}"),
                    ephemeral=True
                )
                return
        
        await interaction.delete_original_response()
        
        try:
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)

            voice_client = await voice_channel.connect() if voice_client is None or not voice_client.is_connected() else voice_client
            voice_client.play(source)
            
            embed = discord.Embed(
                title="Radio",
                description=f"Now playing live radio! {DANCE_EMOJI}",
                color=0x00FF00
            )
            embed.add_field(name="**Radio-URL:**", value=f"{stream_url}")
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
            embed.set_footer(text="JabUB.css | by www.ninoio.gay")
            
            await interaction.channel.send(embed=embed)
        
        except discord.ClientException as e:
            await interaction.channel.send(
                embed=simple_embed(f"{INFO_EMOJI} Error playing the radio stream: {e}"),
                ephemeral=True
            )
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                
        except FileNotFoundError:
            await interaction.channel.send(
                embed=simple_embed("FFmpeg not found. Make sure it is installed and added to PATH."),
                ephemeral=True
            )
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                
        except Exception as e:
            await interaction.channel.send(
                embed=simple_embed(f"An unexpected error occurred: {e}"),
                ephemeral=True
            )
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
        
    async def cog_load(self):
        self.bot.tree.add_command(self.radio_command, guild=discord.Object(id=SYNC_SERVER))