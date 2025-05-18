# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import random
import concurrent.futures
from constants import *
from util.queue import *
from util.play_next import play_next
from embeds import *

guild_queues = {}

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="play", description="Plays music")
    @app_commands.describe(song="URL or search term")
    async def play(self, interaction: discord.Interaction, song: str):
        await interaction.response.defer()

        loading_message = await interaction.followup.send(
            embed=simple_embed(f"{LOADING_EMOJI} Loading songs, started: <t:{int(discord.utils.utcnow().timestamp())}:R>")
        )

        search_query = song if song.startswith("http") else f"ytsearch:{song}"
        loop = asyncio.get_running_loop()

        def run_yt():
            with yt_dlp.YoutubeDL(YT_OPTS) as ydl:
                return ydl.extract_info(search_query, download=False)

        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                info = await loop.run_in_executor(pool, run_yt)
        except Exception as e:
            await interaction.followup.send(
                embed=simple_embed(f"Failed to load video/playlist: {e}"),
                ephemeral=True
            )
            return

        if interaction.guild.id not in guild_queues:
            guild_queues[interaction.guild.id] = Queue()
        queue = guild_queues[interaction.guild.id]
        
        if "entries" in info:
            entries = info["entries"]
            entries = [e for e in entries if e]
            for entry in entries:
                try:
                    stream_url = entry["url"]
                    title = entry.get("title", "Unknown title")
                    thumbnail = entry.get("thumbnail")
                    duration = entry.get("duration", 0)
                    author = entry.get("uploader", "Unknown author")
                    song_url = entry.get("webpage_url", "Unknown URL")
                    likes = entry.get("like_count", 0)
                    views = entry.get("view_count", 0)
                    upload_date = entry.get("upload_date", "Unknown date")

                    ffmpeg_args = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn'
                    }
                    source = await discord.FFmpegOpusAudio.from_probe(stream_url, **ffmpeg_args)
                    queue.add(source, (title, thumbnail, None, duration, author, song_url, likes, views, upload_date))
                except Exception:
                    continue
            
            titles_list = "\n".join([f"* {entry.get('title', 'Unknown title')}" for entry in entries])
            await interaction.channel.send(
                embed=simple_embed(f"{INFO_EMOJI} Added {len(entries)} song(s) to queue!\n Song(s):\n{titles_list}", thumbnail=entries[0].get("thumbnail"))
            )
            
        else:
            stream_url = info["url"]
            title = info.get("title", "Unknown title")
            thumbnail = info.get("thumbnail")
            duration = info.get("duration", 0)
            author = info.get("uploader", "Unknown author")
            song_url = info.get("webpage_url", "Unknown URL")
            likes = info.get("like_count", 0)
            views = info.get("view_count", 0)
            upload_date = info.get("upload_date", "Unknown date")

            ffmpeg_args = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            source = await discord.FFmpegOpusAudio.from_probe(stream_url, **ffmpeg_args)
            queue.add(source, (title, thumbnail, None, duration, author, song_url, likes, views, upload_date))
            await interaction.channel.send(
                embed=simple_embed(f"{INFO_EMOJI} Added to queue: **{title}**", thumbnail=thumbnail)
            )

        await loading_message.delete()

        if not interaction.user.voice:
            await interaction.followup.send(
                embed=simple_embed("You have to be in a VC!"),
                ephemeral=True
            )
            return

        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            channel = interaction.user.voice.channel
            await channel.connect()
            voice_client = interaction.guild.voice_client

        if voice_client and voice_client.channel and interaction.user.voice.channel != voice_client.channel:
            await interaction.followup.send(
                embed=simple_embed(f"{INFO_EMOJI} You must be in the same voice channel as the bot to use this command!"),
                ephemeral=True
            )
        else:
            if not queue.playing and not voice_client.is_playing() and not queue.is_empty():
                await play_next(interaction.guild, voice_client, interaction)
                
    @app_commands.command(name="skip", description="skips the current song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} Im not in a VC rn."), ephemeral=True)
            return

        if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
            await interaction.response.send_message(
                embed=simple_embed(f"{INFO_EMOJI} You must be in the same voice channel as the bot to skip!"),
                ephemeral=True
            )
            return

        queue = guild_queues.get(interaction.guild.id)
        if queue:
            queue.playing = False

        voice_client.stop()

        next_song = queue.queue[0] if queue and queue.queue else None

        if next_song:
            source, (title, thumbnail, _, duration, author, song_url, likes, views, upload_date) = next_song
            await interaction.response.send_message(embed=simple_embed(f"Skipped song! {CHECK}\nNow Playing: **{title}**", thumbnail=thumbnail))
        else:
            await interaction.response.send_message(embed=simple_embed(f"Skipped song! {CHECK}\nNo more songs in queue."))

        channel = self.bot.get_channel(i_channel)
        if channel and next_song:
            await channel.send(
                embed=simple_embed(f"Now Playing: **{title}**", thumbnail=thumbnail)
            )

        if queue and not queue.playing:
            await play_next(interaction.guild, voice_client, interaction=interaction)
    
    @app_commands.command(name="queue", description="lists queued songs")
    async def list(self, interaction: discord.Interaction):
        queue = guild_queues.get(interaction.guild.id)
        wait_time = 0

        def format_time(seconds):
            minutes, seconds = divmod(int(seconds), 60)
            return f"{minutes:02}:{seconds:02}"

        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.channel:
            if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
                await interaction.response.send_message(
                    embed=simple_embed(f"{INFO_EMOJI} You must be in the same voice channel as the bot to use this command!"),
                    ephemeral=True
                )
                return

        if not queue or not queue.queue:
            await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} There is no queue"))
            return

        embed = discord.Embed(
            title=f"{INFO_EMOJI} Queue",
            description="Here are all queued songs:",
            color=0x00ff00
        )

        for i, (source, song_data) in enumerate(queue.queue):
            title = song_data[0]
            duration = song_data[3]

            embed.add_field(
                name=f"{i + 1}. Song *in {format_time(wait_time)} min*",
                value=f"**{title}**, *duration: {format_time(duration)} min*",
                inline=False
            )
            wait_time += duration
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.set_footer(text="JabUB.css | by www.ninoio.gay")
        embed.set_thumbnail(url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stop", description="Stops the Bot")
    async def leave(self, i: discord.Interaction):
        voice_client = i.guild.voice_client
        if voice_client and voice_client.channel:
            if not i.user.voice or i.user.voice.channel != voice_client.channel:
                await i.response.send_message(
                    embed=simple_embed(f"{INFO_EMOJI} You must be in the same voice channel as the bot to use this command!"),
                    ephemeral=True
                )
                return
        queue = guild_queues.get(i.guild.id)
        
        def format_time(seconds):
            minutes, seconds = divmod(int(seconds), 60)
            return f"{minutes:02}:{seconds:02}"
        if queue and queue.queue:
            total_duration = sum(song_data[3] for source, song_data in queue.queue)
        else:
            total_duration = int(0)
        
        embed = discord.Embed(
            title=f"{INFO_EMOJI} Stopped!",
            description="The bot has left the voice channel.",
            color=0x00ff00
        )
        embed.add_field(name="Total time left in queue ⏳", value=f"**{format_time(total_duration)}** min", inline=False)
        embed.set_author(name=i.user.name, icon_url=i.user.avatar.url)
        embed.set_footer(text="JabUB.css | by www.ninoio.gay")
        embed.set_thumbnail(url=i.user.avatar.url)
        
        if i.guild.voice_client:
            await i.guild.voice_client.disconnect()
            await i.response.send_message(embed=embed)
        else:
            await i.response.send_message(embed=simple_embed(f"{INFO_EMOJI} You have to be in a VC"))
    
    @app_commands.command(name="shuffle", description="Shuffles the queue")
    async def shuffle(self, interaction: discord.Interaction):
        queue = guild_queues.get(interaction.guild.id)
        wait_time = 0

        def format_time(seconds):
            minutes, seconds = divmod(int(seconds), 60)
            return f"{minutes:02}:{seconds:02}"
        
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.channel:
            if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
                await interaction.response.send_message(
                    embed=simple_embed(f"{INFO_EMOJI} You must be in the same voice channel as the bot to use this command!"),
                    ephemeral=True
                )
                return

        queue = guild_queues.get(interaction.guild.id)
        
        if not queue or not queue.queue:
            await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} There is no queue"), ephemeral=True)
            return
        
        random.shuffle(queue.queue)
        
        embed = discord.Embed(
            title=f"{INFO_EMOJI} Shuffled the queue!",
            description="Here are all queued songs in order:",
            color=0x00ff00
        )

        for i, (source, song_data) in enumerate(queue.queue):
            title = song_data[0]
            duration = song_data[3]

            embed.add_field(
                name=f"{i + 1}. Song *in {format_time(wait_time)} min*",
                value=f"**{title}**, *duration: {format_time(duration)} min*",
                inline=False
            )
            wait_time += duration
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.set_footer(text="JabUB.css | by www.ninoio.gay")
        embed.set_thumbnail(url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    async def cog_load(self):
        self.bot.tree.add_command(self.play, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.skip, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.list, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.leave, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.shuffle, guild=discord.Object(id=SYNC_SERVER))

