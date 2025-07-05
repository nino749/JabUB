# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
from typing import Optional
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
from util.ticket_creator import *
from util.queue import *
from embeds import *
from texts import *

if TYPE_CHECKING:
    from cogs.music import play_next

class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        
    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        self.bot.tree.add_command(self.radio_command, guild=discord.Object(id=SYNC_SERVER))
        
    async def cog_unload(self):
        if self.session:
            await self.session.close()
        
    @app_commands.command(name="radio", description="Play a radio stream")
    @app_commands.describe(choice="Choose a Radio sender, or type in your own!")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Charts, WW", value="http://streams.bigfm.de/bigfm-charts-128-aac?usid=0-0-H-A-D-30"),
        app_commands.Choice(name="DLF, Ger", value="https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3?aggregator=web"),
        app_commands.Choice(name="NDR, Ger", value="http://icecast.ndr.de/ndr/ndr1radiomv/rostock/mp3/128/stream.mp3"),
        app_commands.Choice(name="RBB, Ger", value="http://antennebrandenburg.de/livemp3"),
        app_commands.Choice(name="RADIO BOB!, Ger", value="http://streams.radiobob.de/bob-live/mp3-192/mediaplayer"),
        app_commands.Choice(name="88vier, Ger", value="http://ice.rosebud-media.de:8000/88vier-low"),
        app_commands.Choice(name="bigFM, Ger", value="http://streams.bigfm.de/bigfm-deutschland-128-aac?usid=0-0-H-A-D-30"),
        app_commands.Choice(name="1 Live, Ger", value="http://wdr-1live-live.icecast.wdr.de/wdr/1live/live/mp3/128/stream.mp3"),
        app_commands.Choice(name="WDR 3, Ger", value="http://wdr-wdr3-live.icecast.wdr.de/wdr/wdr3/live/mp3/256/stream.mp3"),
        app_commands.Choice(name="BBC, GB", value="http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"),
        app_commands.Choice(name="BFBS, GB", value="http://tx.sharp-stream.com/icecast.php?i=ssvcbfbs1.aac"),
        app_commands.Choice(name="ENERGY98, USA", value="http://mp3tx.duplexfx.com:8800"),
        app_commands.Choice(name="Jazz24, USA", value="http://live.streamtheworld.com/JAZZ24AAC.aac"),
        app_commands.Choice(name="Classical, USA", value="http://streams.publicradio.org/classical.m3u"),
        app_commands.Choice(name="Lounge FM, Int", value="http://www.lounge-radio.com/listen/lounge128.pls"),
        app_commands.Choice(name="Smooth Jazz, USA", value="http://smoothjazz.cdnstream1.com/2640_128.mp3"),
        app_commands.Choice(name="Classic Rock, USA", value="http://198.178.123.5:8058/stream.nsv"),
        app_commands.Choice(name="Chill Out, Int", value="http://media-ice.musicradio.com/ChillMP3.m3u"),
        app_commands.Choice(name="Ambient, Int", value="http://uk3.internet-radio.com:8405/stream.ogg"),
        app_commands.Choice(name="Electronic, Int", value="http://streams.electronic-radio.com/electronic128.aac"),
    ])
    @app_commands.describe(url="URL of the radio stream, a list: (https://wiki.ubuntuusers.de/Internetradio/Stationen/)")
    async def radio_command(self, interaction: discord.Interaction, url: Optional[str] = None, choice: Optional[app_commands.Choice[str]] = None):
        if not interaction.user.voice:
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

        if voice_client and voice_client.is_playing():
            voice_client.stop()

        if choice:
            stream_url = choice.value
            radio_name = choice.name
        elif url:
            stream_url = url
            radio_name = "Custom Radio"
        else:
            await interaction.response.send_message(
                embed=simple_embed(f"{INFO_EMOJI} Please select a radio or provide a URL."), 
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            f"Loading the radio stream: {radio_name} {LOADING_EMOJI}", 
            ephemeral=True
        )

        try:
            processed_url = await self._process_stream_url(stream_url)
            if not processed_url:
                await interaction.followup.send(
                    embed=simple_embed(f"{INFO_EMOJI} Failed to process the stream URL."),
                    ephemeral=True
                )
                return
                
            stream_url = processed_url
            
        except Exception as e:
            await interaction.followup.send(
                embed=simple_embed(f"{INFO_EMOJI} Error processing stream URL: {str(e)}"),
                ephemeral=True
            )
            return
        
        await interaction.delete_original_response()
        
        try:
            voice_client = await self._connect_to_voice(voice_channel, voice_client)
            await self._play_radio_stream(voice_client, stream_url)
            
            embed = self._create_radio_embed(interaction.user, radio_name, stream_url)
            await interaction.followup.send(embed=embed)
            
        except discord.ClientException as e:
            await interaction.followup.send(
                embed=simple_embed(f"{INFO_EMOJI} Error playing the radio stream: {e}")
            )
            await self._cleanup_voice_client(voice_client)
                
        except FileNotFoundError:
            await interaction.followup.send(
                embed=simple_embed(f"{INFO_EMOJI} FFmpeg not found. Make sure it is installed and added to PATH.")
            )
            await self._cleanup_voice_client(voice_client)
                
        except Exception as e:
            await interaction.followup.send(
                embed=simple_embed(f"{INFO_EMOJI} An unexpected error occurred: {e}")
            )
            await self._cleanup_voice_client(voice_client)

    async def _process_stream_url(self, url: str) -> Optional[str]:
        url_lower = url.lower()
        
        if url_lower.endswith(('.pls', '.m3u', '.m3u8', '.asx', '.xspf')):
            return await self._parse_playlist_file(url)
        
        if url_lower.endswith(('.mp3', '.aac', '.ogg', '.flac', '.opus')):
            return url
            
        if any(url_lower.startswith(proto) for proto in ['http://', 'https://', 'rtmp://', 'rtmps://']):
            return url
            
        if re.search(r':\d+(/|$)', url):
            return url
            
        return url

    async def _parse_playlist_file(self, url: str) -> Optional[str]:
        if not self.session:
            return None
            
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                    
                content = await response.text()
                url_lower = url.lower()
                
                if url_lower.endswith('.pls'):
                    return self._parse_pls_content(content)
                elif url_lower.endswith(('.m3u', '.m3u8')):
                    return self._parse_m3u_content(content)
                elif url_lower.endswith('.asx'):
                    return self._parse_asx_content(content)
                elif url_lower.endswith('.xspf'):
                    return self._parse_xspf_content(content)
                    
        except Exception:
            return None
            
        return None

    def _parse_pls_content(self, content: str) -> Optional[str]:
        for line in content.splitlines():
            line = line.strip()
            if line.lower().startswith('file1='):
                return line.split('=', 1)[1].strip()
        return None

    def _parse_m3u_content(self, content: str) -> Optional[str]:
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                return line
        return None

    def _parse_asx_content(self, content: str) -> Optional[str]:
        match = re.search(r'href\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        return match.group(1) if match else None

    def _parse_xspf_content(self, content: str) -> Optional[str]:
        match = re.search(r'<location>([^<]+)</location>', content, re.IGNORECASE)
        return match.group(1) if match else None

    async def _connect_to_voice(self, voice_channel, voice_client) -> discord.VoiceClient:
        if voice_client is None or not voice_client.is_connected():
            return await voice_channel.connect()
        return voice_client

    async def _play_radio_stream(self, voice_client: discord.VoiceClient, stream_url: str):
        ffmpeg_options = {
            'before_options': (
                '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
                '-analyzeduration 0 -probesize 32768 -fflags +discardcorrupt'
            ),
            'options': '-vn -bufsize 512k -maxrate 128k'
        }

        source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
        voice_client.play(source)

    def _create_radio_embed(self, user: discord.Member, radio_name: str, stream_url: str) -> discord.Embed:
        embed = discord.Embed(
            title="📻 Radio",
            description=f"Now playing **{radio_name}** live radio! {DANCE_EMOJI}",
            color=0x00FF00
        )
        embed.add_field(name="**Radio Station:**", value=radio_name, inline=False)
        embed.add_field(name="**Stream URL:**", value=f"```{stream_url[:100]}{'...' if len(stream_url) > 100 else ''}```", inline=False)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    async def _cleanup_voice_client(self, voice_client: Optional[discord.VoiceClient]):
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()