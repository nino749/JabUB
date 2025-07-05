# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import random
import concurrent.futures
from typing import List
import time
from constants import *
from util.queue import *
from embeds import *
from texts import *
from views.ticketviews import ActionsView

guild_queues = {}

class PreloadedSong:
    def __init__(self, source, metadata):
        self.source = source
        self.metadata = metadata
        self.is_ready = True
        self.preload_time = time.time()

class AsyncSongLoader:
    def __init__(self, max_workers=4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.preload_cache = {}
        self.max_cache_size = 50
        
    def cleanup_cache(self):
        if len(self.preload_cache) > self.max_cache_size:
            sorted_items = sorted(self.preload_cache.items(), 
                                key=lambda x: x[1].preload_time)
            for key, _ in sorted_items[:10]:
                del self.preload_cache[key]
    
    async def extract_info_async(self, url: str, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
            
        def run_yt():
            with yt_dlp.YoutubeDL(YT_OPTS) as ydl:
                return ydl.extract_info(url, download=False)
        
        return await loop.run_in_executor(self.executor, run_yt)
    
    async def preload_audio_source(self, stream_url: str, loop=None):
        if loop is None:
            loop = asyncio.get_running_loop()
            
        def create_source():
            ffmpeg_args = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn -bufsize 512k'
            }
            return discord.FFmpegOpusAudio(stream_url, **ffmpeg_args)
        
        return await loop.run_in_executor(self.executor, create_source)

song_loader = AsyncSongLoader()

class OptimizedQueue:
    def __init__(self):
        self.queue = []
        self.playing = False
        self.preload_tasks = []
        self.lock = asyncio.Lock()
    
    def add(self, song_data):
        self.queue.append(song_data)
    
    def get_next(self):
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def is_empty(self):
        return len(self.queue) == 0
    
    def clear(self):
        self.queue.clear()
        for task in self.preload_tasks:
            if not task.done():
                task.cancel()
        self.preload_tasks.clear()

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.background_tasks = set()
        
    def create_background_task(self, coro):
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return task
        
    async def send_static_message(self):
        try:
            actions_embed = discord.Embed(
                title="Music Bot Control Panel",
                description="Available music commands",
                color=0x9b59b6
            )
            actions_embed.add_field(
                name="Core Commands",
                value="```\n/play     - Play music from URL or search\n/radio    - Play live radio\n/skip     - Skip current song\n/queue    - View song queue\n/stop     - Stop music and leave\n/shuffle  - Shuffle the queue\n/chart    - Play random chart song\n```",
                inline=False
            )
            actions_embed.add_field(
                name="Bot Status",
                value=f"```\nConnected Servers: {len(self.bot.guilds)}\nTotal Users: {len(self.bot.users)}\nStatus: Ready\n```",
                inline=True
            )
            actions_embed.add_field(
                name="Tips",
                value="```\n• Join a voice channel first\n• Use playlists for bulk adding\n• Supports YouTube links\n```",
                inline=True
            )
            actions_embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            actions_embed.set_footer(
                text=f"Music Bot • Serving {len(self.bot.users)} users",
                icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )
            actions_embed.timestamp = discord.utils.utcnow()

            channel = await self.bot.fetch_channel(I_CHANNEL)
            if channel:
                async for message in channel.history(limit=100):
                    if (message.author == self.bot.user and 
                        message.embeds and
                        message.embeds[0].description and
                        "Available music commands" in message.embeds[0].description):
                        await message.delete()
                        break
                
                await channel.send(embed=actions_embed, view=ActionsView(bot=self.bot))
        except Exception as e:
            print(f"Error sending disconnect message: {e}")
    
    async def preload_next_songs(self, guild_id: int, count: int = 3):
        if guild_id not in guild_queues:
            return
            
        queue = guild_queues[guild_id]
        
        for i, song_data in enumerate(queue.queue[:count]):
            if i >= count:
                break
                
            if hasattr(song_data, 'source') and song_data.source:
                continue
                
            try:
                if not hasattr(song_data, 'stream_url'):
                    continue
                    
                source = await song_loader.preload_audio_source(song_data.stream_url)
                song_data.source = source
                
            except Exception as e:
                print(f"Fehler beim Vorladen: {e}")
                continue
    
    async def play_next(self, guild, voice_client, interaction):
        if guild.id not in guild_queues:
            return
            
        queue = guild_queues[guild.id]
        next_song = queue.get_next()

        if next_song:
            self.create_background_task(self.preload_next_songs(guild.id))
            
            source, metadata = next_song
            title, thumbnail, _, duration, author, song_url, likes, views, upload_date = metadata
            queue.playing = True

            def after_song(e):
                if e:
                    print(f"Error: {e}")
                queue.playing = False
                pn = self.play_next(guild, voice_client, interaction)
                asyncio.run_coroutine_threadsafe(pn, self.bot.loop)

            voice_client.play(source, after=after_song)
            
            embed = self.create_now_playing_embed(metadata, interaction)
            msg = await interaction.channel.send(embed=embed)
            
            self.create_background_task(self.update_progress(msg, embed, duration))
        else:
            queue.playing = False

    def create_now_playing_embed(self, metadata, interaction):
        title, thumbnail, _, duration, author, song_url, likes, views, upload_date = metadata
        
        def format_time(seconds):
            m, s = divmod(int(seconds), 60)
            return f"{m:02}:{s:02}"
        
        def format_number(n):
            if n is None:
                return "N/A"
            if n >= 1_000_000:
                return f"{n/1_000_000:.1f}M"
            elif n >= 1_000:
                return f"{n/1_000:.1f}K"
            return str(n)
        
        if upload_date and len(str(upload_date)) == 8:
            date = f"{upload_date[6:8]}.{upload_date[4:6]}.{upload_date[0:4]}"
        else:
            date = str(upload_date)
        
        embed = discord.Embed(
            title="📖 Queue",
            description=f"🎵 Now Playing: **{title}**",
            color=0xe91e63
        )
        embed.add_field(
            name="🧑‍🎤 **Author**",
            value=f"```{author}```",
            inline=False
        )
        embed.add_field(
            name="⏱️ **Duration**", 
            value=f"```\n▶️ Started: ✅\n⏳ Total: {format_time(duration)}\n```", 
            inline=False
        )
        embed.add_field(
            name="📊 **Statistics**",
            value=f"```\n👍 Likes: {format_number(likes)}\n👁️ Views: {format_number(views)}\n📅 Upload: {date}\n```",
            inline=True
        )
        embed.add_field(
            name="🔗 **Links**",
            value=f"[Watch on YouTube]({song_url})\n[More from {author}](https://youtube.com/results?search_query={author.replace(' ', '+')})",
            inline=True
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_author(
            name=f"🎧 Requested by {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url
        )
        embed.set_footer(
            text="🎵 Music Bot • Enjoy the music! 🎶",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    async def update_progress(self, message, embed, duration):
        await asyncio.sleep(duration)
        embed.color = 0x95a5a6
        embed.set_field_at(0, name="⏹️ **Finished**", value=f"```\n✅ Completed: {self.format_time(duration)}\n🎵 Song ended\n```", inline=False)
        try:
            await message.edit(embed=embed)
        except discord.HTTPException:
            pass
    
    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"
    
    async def process_song_entries(self, entries: List[dict], guild_id: int):
        if guild_id not in guild_queues:
            guild_queues[guild_id] = OptimizedQueue()
        
        queue = guild_queues[guild_id]
        processed_songs = []
        
        batch_size = 5
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i+batch_size]
            
            tasks = []
            for entry in batch:
                if entry:
                    tasks.append(self.process_single_entry(entry))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"Fehler bei der Verarbeitung: {result}")
                        continue
                    if result:
                        processed_songs.append(result)
                        queue.add(result)
        
        return processed_songs
    
    async def process_single_entry(self, entry: dict):
        try:
            if not entry or "url" not in entry:
                print(f"Fehler beim Verarbeiten des Eintrags: Missing 'url' key in entry")
                return None
                
            stream_url = entry["url"]
            title = entry.get("title", "Unknown title")
            thumbnail = entry.get("thumbnail")
            duration = entry.get("duration", 0)
            author = entry.get("uploader", "Unknown author")
            song_url = entry.get("webpage_url", "Unknown URL")
            likes = entry.get("like_count", 0)
            views = entry.get("view_count", 0)
            upload_date = entry.get("upload_date", "Unknown date")
            
            metadata = (title, thumbnail, None, duration, author, song_url, likes, views, upload_date)
            
            source = await song_loader.preload_audio_source(stream_url)
            
            return (source, metadata)
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten des Eintrags: {e}")
            return None
        
    @app_commands.command(name="chart", description="Plays a random song from the YouTube Music charts")
    async def play_chart(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        loading_embed = discord.Embed(
            title="📊 Fetching Chart Songs",
            description="🔍 **Searching through YouTube Music charts...**\n\n⏳ *This might take a moment*",
            color=0xf39c12
        )
        loading_embed.set_thumbnail(url="https://i.imgur.com/ZKwSz4A.gif")
        loading_embed.add_field(
            name="🎯 **Sources**",
            value="```\n📈 Top 50 Global\n🔥 Trending Music\n🎵 Billboard Hot 100\n```",
            inline=False
        )
        loading_embed.timestamp = discord.utils.utcnow()
        
        loading_message = await interaction.followup.send(embed=loading_embed)
        
        try:
            chart_urls = [
                "https://music.youtube.com/playlist?list=RDCLAK5uy_kmPRjHDECIcuVwnKsx5w4UBCp9jSEMzM",  # Top 50 Global
                "https://music.youtube.com/playlist?list=RDCLAK5uy_k8jhb5wP3rUqLOWFzVQNE_YdIcF7O4BN",  # Trending
                "https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI",  # Billboard Hot 100
            ]
            
            playlist_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': '1-20',
            }
            
            trending_songs = []
            
            for chart_url in chart_urls:
                try:
                    def extract_playlist_info():
                        with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                            return ydl.extract_info(chart_url, download=False)
                    
                    chart_info = await asyncio.get_running_loop().run_in_executor(
                        song_loader.executor, extract_playlist_info
                    )
                    
                    if "entries" in chart_info and chart_info["entries"]:
                        for entry in chart_info["entries"][:15]:
                            if entry and entry.get("title"):
                                title = entry["title"]
                                uploader = entry.get("uploader", "")
                                if uploader and uploader.lower() not in title.lower():
                                    song_query = f"{title} {uploader}"
                                else:
                                    song_query = title
                                trending_songs.append(song_query)
                        
                        if trending_songs:
                            break
                            
                except Exception as e:
                    print(f"Fehler beim Laden der Playlist {chart_url}: {e}")
                    continue
            
            if not trending_songs:
                try:
                    search_queries = [
                        "ytsearch5:music charts 2024",
                        "ytsearch5:trending music now", 
                        "ytsearch5:top songs 2024"
                    ]
                    
                    for search_query in search_queries:
                        try:
                            search_results = await song_loader.extract_info_async(search_query)
                            if "entries" in search_results:
                                for entry in search_results["entries"][:5]:
                                    if entry and entry.get("title"):
                                        title = entry["title"]
                                        uploader = entry.get("uploader", "")
                                        if uploader and uploader.lower() not in title.lower():
                                            song_query = f"{title} {uploader}"
                                        else:
                                            song_query = title
                                        trending_songs.append(song_query)
                                
                                if trending_songs:
                                    break
                        except Exception as e:
                            print(f"Fehler bei der Suche {search_query}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Fehler bei der Fallback-Suche: {e}")
            
            if not trending_songs:
                trending_songs = [
                    "Flowers Miley Cyrus",
                    "As It Was Harry Styles", 
                    "Bad Habit Steve Lacy",
                    "About Damn Time Lizzo",
                    "Heat Waves Glass Animals",
                    "Stay The Kid LAROI Justin Bieber",
                    "Ghost Justin Bieber",
                    "Industry Baby Lil Nas X",
                    "Good 4 U Olivia Rodrigo",
                    "Levitating Dua Lipa"
                ]
            
            random_chart_song = random.choice(trending_songs)
            
            loading_embed.title = "🎵 Loading Chart Song"
            loading_embed.description = f"**Selected:** {random_chart_song}\n\n⏳ *Preparing your music...*"
            loading_embed.color = 0x3498db
            await loading_message.edit(embed=loading_embed)
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Charts: {e}")
            fallback_songs = [
                "Flowers Miley Cyrus",
                "As It Was Harry Styles", 
                "Bad Habit Steve Lacy",
                "About Damn Time Lizzo",
                "Heat Waves Glass Animals"
            ]
            random_chart_song = random.choice(fallback_songs)
            
            loading_embed.title = "🎵 Loading Fallback Song"
            loading_embed.description = f"**Selected:** {random_chart_song}\n\n⏳ *Using fallback charts...*"
            loading_embed.color = 0xe67e22
            await loading_message.edit(embed=loading_embed)
        
        search_query = f"ytsearch:{random_chart_song}"
        
        try:
            info = await song_loader.extract_info_async(search_query)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"**Failed to load chart song**\n\n```\n{e}\n```",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        if interaction.guild.id not in guild_queues:
            guild_queues[interaction.guild.id] = OptimizedQueue()
        
        queue = guild_queues[interaction.guild.id]
        
        if "entries" in info and info["entries"]:
            entry = info["entries"][0]
        else:
            entry = info
        
        processed_song = await self.process_single_entry(entry)
        if processed_song:
            queue.add(processed_song)
            title = processed_song[1][0]
            thumbnail = processed_song[1][1]
            
            success_embed = discord.Embed(
                title="📊 Chart Song Added!",
                description=f"**{title}**\n\n✅ *Added to queue successfully*",
                color=0x27ae60
            )
            success_embed.set_thumbnail(url=thumbnail)
            success_embed.add_field(
                name="🎯 **Source**",
                value="```\n📈 YouTube Music Charts\n🔥 Trending Now\n```",
                inline=True
            )
            success_embed.add_field(
                name="📋 **Queue Position**",
                value=f"```\n#{len(queue.queue)}\n```",
                inline=True
            )
            success_embed.timestamp = discord.utils.utcnow()
            
            await interaction.channel.send(embed=success_embed)
        
        await loading_message.delete()
        
        if not interaction.user.voice:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Voice Channel Required",
                    description="**You need to be in a voice channel!**\n\n🎧 *Join a voice channel and try again*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return
        
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            channel = interaction.user.voice.channel
            await channel.connect(self_deaf=True)
            voice_client = interaction.guild.voice_client
            voice_channel = voice_client.channel

            if SET_VC_STATUS_TO_MUSIC_PLAYING:
                current_song = processed_song[1][0] if processed_song else "Music"
                await voice_channel.edit(status=f"Listening to: {current_song}")
        
        if voice_client and voice_client.channel and interaction.user.voice.channel != voice_client.channel:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Wrong Voice Channel",
                    description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
        else:
            if not queue.playing and not voice_client.is_playing() and not queue.is_empty():
                await self.play_next(guild=interaction.guild, voice_client=voice_client, interaction=interaction)
    
    async def insipre_me(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        random_songs = [
            "Never Gonna Give You Up Rick Astley",
            "Bohemian Rhapsody Queen",
            "Imagine Dragons Believer",
            "The Weeknd Blinding Lights",
            "Dua Lipa Levitating",
            "Ed Sheeran Shape of You",
            "Billie Eilish bad guy",
            "Post Malone Circles",
            "Ariana Grande 7 rings",
            "Drake God's Plan",
            "Taylor Swift Anti-Hero",
            "Harry Styles As It Was",
            "Olivia Rodrigo good 4 u",
            "Doja Cat Kiss Me More",
            "The Kid LAROI Stay",
            "Lil Nas X Industry Baby",
            "Glass Animals Heat Waves",
            "Måneskin Beggin",
            "Adele Easy On Me",
            "Bruno Mars Uptown Funk",
            "Queen Don't Stop Me Now",
            "Journey Don't Stop Believin'",
            "Michael Jackson Billie Jean",
            "A-ha Take On Me",
            "Whitney Houston I Wanna Dance with Somebody (Who Loves Me)",
            "Toto Africa",
            "Eurythmics Sweet Dreams (Are Made of This)",
            "Guns N' Roses Sweet Child O' Mine",
            "AC/DC Back In Black",
            "Nirvana Smells Like Teen Spirit",
            "The Police Every Breath You Take",
            "Linkin Park In The End",
            "The Killers Mr. Brightside",
            "Arctic Monkeys Do I Wanna Know?",
            "Coldplay Viva La Vida",
            "Coldplay Yellow",
            "OneRepublic Counting Stars",
            "Lewis Capaldi Someone You Loved",
            "James Arthur Say You Won't Let Go",
            "Shawn Mendes Señorita",
            "Miley Cyrus Flowers",
            "SZA Kill Bill",
            "Jung Kook Seven",
            "Elton John Cold Heart",
            "The Neighbourhood Sweater Weather",
            "Hozier Take Me to Church",
            "Lord Huron The Night We Met",
            "Vance Joy Riptide",
            "Tones And I Dance Monkey",
            "Post Malone Rockstar",
            "The Chainsmokers Closer",
            "Justin Bieber Sorry",
            "Shawn Mendes Treat You Better",
            "Khalid Better",
            "Cardi B WAP"
        ]
        
        random_song = random.choice(random_songs)
        
        loading_embed = discord.Embed(
            title="✨ Inspiration Mode",
            description=f"✨ **Inspired Pick:** {random_song}\n\n⏳ *Preparing your surprise...*",
            color=0x9b59b6
        )
        loading_embed.set_thumbnail(url="https://i.imgur.com/ZKwSz4A.gif")
        loading_embed.add_field(
            name="🎯 **What's This?**",
            value="```\n✨ Random song selection\n🎵 Curated playlist\n🎲 Surprise me feature\n```",
            inline=False
        )
        loading_embed.timestamp = discord.utils.utcnow()
        
        loading_message = await interaction.followup.send(embed=loading_embed)
        
        search_query = f"ytsearch:{random_song}"
        
        try:
            info = await song_loader.extract_info_async(search_query)
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"**Failed to load song**\n\n```\n{e}\n```",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return
        
        if interaction.guild.id not in guild_queues:
            guild_queues[interaction.guild.id] = OptimizedQueue()
        
        queue = guild_queues[interaction.guild.id]
        
        if "entries" in info and info["entries"]:
            entry = info["entries"][0]
        else:
            entry = info
        
        processed_song = await self.process_single_entry(entry)
        if processed_song:
            queue.add(processed_song)
            title = processed_song[1][0]
            thumbnail = processed_song[1][1]
            
            success_embed = discord.Embed(
                title="✨ Inspiration Delivered!",
                description=f"🎵 **{title}**\n\n🎲 *Your random musical surprise*",
                color=0x9b59b6
            )
            success_embed.set_thumbnail(url=thumbnail)
            success_embed.add_field(
                name="🎯 **Mode**",
                value="```\n✨ Inspiration\n🎲 Random Pick\n```",
                inline=True
            )
            success_embed.add_field(
                name="📋 **Queue Position**",
                value=f"```\n#{len(queue.queue)}\n```",
                inline=True
            )
            success_embed.timestamp = discord.utils.utcnow()
            
            await interaction.channel.send(embed=success_embed)
        
        await loading_message.delete()
        
        if not interaction.user.voice:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Voice Channel Required",
                    description="**You need to be in a voice channel!**\n\n🎧 *Join a voice channel and try again*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return
        
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            channel = interaction.user.voice.channel
            await channel.connect(self_deaf=True)
            voice_client = interaction.guild.voice_client
            voice_channel = voice_client.channel
            
            if SET_VC_STATUS_TO_MUSIC_PLAYING:
                current_song = processed_song[1][0] if processed_song else "Music"
                await voice_channel.edit(status=f"Listening to: {current_song}")
        
        if voice_client and voice_client.channel and interaction.user.voice.channel != voice_client.channel:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Wrong Voice Channel",
                    description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
        else:
            if not queue.playing and not voice_client.is_playing() and not queue.is_empty():
                await self.play_next(guild=interaction.guild, voice_client=voice_client, interaction=interaction)
    
    async def mostplayed_callback(self, interaction: discord.Interaction, song: str):
        await interaction.response.defer()

        loading_embed = discord.Embed(
            title="🎵 Loading Most Played",
            description=f"🎯 **Song:** {song}\n\n⏳ *Preparing your favorite...*",
            color=0x3498db
        )
        loading_embed.set_thumbnail(url="https://i.imgur.com/ZKwSz4A.gif")
        loading_embed.add_field(
            name="🏆 **Category**",
            value="```\n🎵 Most Played\n🔥 Popular Choice\n⭐ Fan Favorite\n```",
            inline=False
        )
        loading_embed.timestamp = discord.utils.utcnow()

        loading_message = await interaction.followup.send(embed=loading_embed)

        search_query = f"ytsearch:{song}"

        try:
            info = await song_loader.extract_info_async(search_query)
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"**Failed to load song**\n\n```\n{e}\n```",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        if interaction.guild.id not in guild_queues:
            guild_queues[interaction.guild.id] = OptimizedQueue()

        queue = guild_queues[interaction.guild.id]

        if "entries" in info and info["entries"]:
            entry = info["entries"][0]
        else:
            entry = info

        processed_song = await self.process_single_entry(entry)
        if processed_song:
            queue.add(processed_song)
            title = processed_song[1][0]
            thumbnail = processed_song[1][1]
            
            success_embed = discord.Embed(
                title="🏆 Most Played Song Added!",
                description=f"🎵 **{title}**\n\n⭐ *Popular choice added to queue*",
                color=0xf39c12
            )
            success_embed.set_thumbnail(url=thumbnail)
            success_embed.add_field(
                name="🏆 **Category**",
                value="```\n🎵 Most Played\n🔥 Fan Favorite\n```",
                inline=True
            )
            success_embed.add_field(
                name="📋 **Queue Position**",
                value=f"```\n#{len(queue.queue)}\n```",
                inline=True
            )
            success_embed.timestamp = discord.utils.utcnow()
            
            await interaction.channel.send(embed=success_embed)

        await loading_message.delete()

        if not interaction.user.voice:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Voice Channel Required",
                    description="**You need to be in a voice channel!**\n\n🎧 *Join a voice channel and try again*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            channel = interaction.user.voice.channel
            await channel.connect(self_deaf=True)
            voice_client = interaction.guild.voice_client
            voice_channel = voice_client.channel
            
            if SET_VC_STATUS_TO_MUSIC_PLAYING:
                current_song = processed_song[1][0] if processed_song else "Music"
                await voice_channel.edit(status=f"Listening to: {current_song}")

        if voice_client and voice_client.channel and interaction.user.voice.channel != voice_client.channel:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Wrong Voice Channel",
                    description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
        else:
            if not queue.playing and not voice_client.is_playing() and not queue.is_empty():
                await self.play_next(guild=interaction.guild, voice_client=voice_client, interaction=interaction)
    
    @app_commands.command(name="play", description="Plays music")
    @app_commands.describe(song="URL or search term")
    async def play(self, interaction: discord.Interaction, song: str):
        await interaction.response.defer()
        
        if interaction.guild.id not in guild_queues:
            guild_queues[interaction.guild.id] = OptimizedQueue()
        queue = guild_queues[interaction.guild.id]
        voice_client = interaction.guild.voice_client
        
        if voice_client and voice_client.channel and interaction.user.voice.channel != voice_client.channel:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Wrong Voice Channel",
                    description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )

        if not interaction.user.voice:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Voice Channel Required",
                    description="**You need to be in a voice channel!**\n\n🎧 *Join a voice channel and try again*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        loading_embed = discord.Embed(
            title="🎵 Loading Music",
            description=f"🔍 **Searching for:** {song}\n\n⏳ *Processing your request...*",
            color=0x3498db
        )
        loading_embed.set_thumbnail(url="https://i.pinimg.com/564x/bc/0b/c2/bc0bc24abc32472c8d726c7bd0fc8f59.jpg")

        loading_embed.timestamp = discord.utils.utcnow()
        loading_message = await interaction.followup.send(embed=loading_embed)
        search_query = song if song.startswith("http") else f"ytsearch:{song}"
        
        try:
            info = await song_loader.extract_info_async(search_query)
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"**Failed to load video/playlist**\n\n```\n{e}\n```",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        if "entries" in info:
            entries = [e for e in info["entries"] if e]
            
            processing_embed = discord.Embed(
                title="🎵 Processing Playlist...",
                description=f"📋 **Found {len(entries)} songs**\n\n⏳ *Adding to queue...*",
                color=0xf39c12
            )
            processing_embed.set_thumbnail(url="https://i.imgur.com/ZKwSz4A.gif")
            processing_embed.add_field(
                name="📊 **Progress**",
                value="```\n🔄 Processing songs...\n📋 Building queue...\n```",
                inline=False
            )
            processing_embed.timestamp = discord.utils.utcnow()
            
            processing_message = await interaction.channel.send(embed=processing_embed)
            
            processed_songs = await self.process_song_entries(entries, interaction.guild.id)
            
            titles_list = "\n".join([f"🎵 {song[1][0]}" for song in processed_songs[:10]])
            if len(processed_songs) > 10:
                titles_list += f"\n\n*... and {len(processed_songs) - 10} more songs*"
            
            success_embed = discord.Embed(
                title="📋 Playlist Added Successfully!",
                description=f"✅ **{len(processed_songs)} songs added to queue**\n\n{titles_list}",
                color=0x27ae60
            )
            success_embed.set_thumbnail(url=entries[0].get("thumbnail") if entries else None)
            success_embed.add_field(
                name="📊 **Queue Stats**",
                value=f"```\n📋 Total Songs: {len(processed_songs)}\n⏳ Estimated Time: {sum(song[1][3] for song in processed_songs) // 60} min\n```",
                inline=False
            )
            success_embed.timestamp = discord.utils.utcnow()
            
            await interaction.channel.send(embed=success_embed)
            
        else:
            processed_song = await self.process_single_entry(info)
            if processed_song:
                queue.add(processed_song)
                title = processed_song[1][0]
                thumbnail = processed_song[1][1]
                duration = processed_song[1][3]
                
                success_embed = discord.Embed(
                    title="🎵 Song Added to Queue!",
                    description=f"**{title}**\n\n✅ *Successfully added to queue*",
                    color=0x27ae60
                )
                success_embed.set_thumbnail(url=thumbnail)
                success_embed.add_field(
                    name="⏱️ **Duration**",
                    value=f"```\n{self.format_time(duration)}\n```",
                    inline=True
                )
                success_embed.add_field(
                    name="📋 **Queue Position**",
                    value=f"```\n#{len(queue.queue)}\n```",
                    inline=True
                )
                success_embed.timestamp = discord.utils.utcnow()
                
                await interaction.channel.send(embed=success_embed)

        await processing_message.delete()
        await loading_message.delete()

        if not voice_client or not voice_client.is_connected():
            channel = interaction.user.voice.channel
            await channel.connect(self_deaf=True)
            voice_client = interaction.guild.voice_client
            voice_channel = voice_client.channel
            processed_song = await self.process_single_entry(info)
            
            if SET_VC_STATUS_TO_MUSIC_PLAYING:
                current_song = processed_song[1][0] if processed_song else "Music"
                await voice_channel.edit(status=f"Listening to: {current_song}")
        
        if not queue.playing and not voice_client.is_playing() and not queue.is_empty():
            await self.play_next(guild=interaction.guild, voice_client=voice_client, interaction=interaction)

    @app_commands.command(name="skip", description="skips the current song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Nothing Playing",
                    description="**No music is currently playing**\n\n🎵 *Use `/play` to start playing music*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Wrong Voice Channel",
                    description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        queue = guild_queues.get(interaction.guild.id)
        if queue:
            queue.playing = False

        voice_client.stop()

        next_song = queue.queue[0] if queue and queue.queue else None

        if next_song:
            source, metadata = next_song
            title, thumbnail = metadata[0], metadata[1]
            
            skip_embed = discord.Embed(
                title="⏭️ Song Skipped!",
                description=f"🎵 **Now Playing:** {title}\n\n✅ *Successfully skipped to next song*",
                color=0x3498db
            )
            skip_embed.set_thumbnail(url=thumbnail)
            skip_embed.add_field(
                name="📋 **Queue Info**",
                value=f"```\n📋 Songs Left: {len(queue.queue) - 1}\n⏭️ Action: Skip\n```",
                inline=False
            )
            skip_embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=skip_embed)
        else:
            skip_embed = discord.Embed(
                title="⏭️ Song Skipped!",
                description="**No more songs in queue**\n\n🎵 *Use `/play` to add more music*",
                color=0x95a5a6
            )
            skip_embed.add_field(
                name="📋 **Queue Status**",
                value="```\n📋 Songs Left: 0\n⏭️ Action: Skip\n🎵 Queue Empty\n```",
                inline=False
            )
            skip_embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=skip_embed)

        if queue and not queue.playing:
            await self.play_next(interaction.guild, voice_client, interaction=interaction)
    
    @app_commands.command(name="queue", description="lists queued songs")
    async def list(self, interaction: discord.Interaction):
        queue = guild_queues.get(interaction.guild.id)
        wait_time = 0

        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.channel:
            if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Wrong Voice Channel",
                        description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return

        if not queue or not queue.queue:
            empty_embed = discord.Embed(
                title="📋 Queue is Empty",
                description="**No songs in queue**\n\n🎵 *Use `/play` to add some music*",
                color=0x95a5a6
            )
            empty_embed.add_field(
                name="💡 **Quick Start**",
                value="```\n🎵 /play <song name>\n📊 /chart - Play trending\n✨ /inspire - Random song\n```",
                inline=False
            )
            empty_embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=empty_embed)
            return

        embed = discord.Embed(
            title="📋 Music Queue",
            description=f"🎵 **{len(queue.queue)} songs in queue**\n\n*Here's what's coming up next:*",
            color=0x9b59b6
        )
        
        display_count = min(15, len(queue.queue))
        for i, (source, song_data) in enumerate(queue.queue[:display_count]):
            title = song_data[0]
            duration = song_data[3]

            embed.add_field(
                name=f"🎵 **{i + 1}.** {title}",
                value=f"```\n⏱️ Duration: {self.format_time(duration)}\n🕒 Starts in: {self.format_time(wait_time)}\n```",
                inline=False
            )
            wait_time += duration
        
        if len(queue.queue) > display_count:
            embed.add_field(
                name="🎵 **More Songs...**", 
                value=f"```\n📋 +{len(queue.queue) - display_count} more songs\n⏱️ Total Duration: {self.format_time(sum(song[1][3] for song in queue.queue))}\n```", 
                inline=False
            )
        
        embed.add_field(
            name="📊 **Queue Statistics**",
            value=f"```\n📋 Total Songs: {len(queue.queue)}\n⏱️ Total Duration: {self.format_time(sum(song[1][3] for song in queue.queue))}\n🎵 Status: {'Playing' if queue.playing else 'Ready'}\n```",
            inline=False
        )
        
        embed.set_author(
            name=f"🎧 Requested by {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url
        )
        embed.set_footer(
            text="🎵 Music Bot • Use /skip to skip current song",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stop", description="Stops the Bot")
    async def leave(self, i: discord.Interaction):
        voice_client = i.guild.voice_client
        if voice_client and voice_client.channel:
            if not i.user.voice or i.user.voice.channel != voice_client.channel:
                await i.response.send_message(
                    embed=discord.Embed(
                        title="❌ Wrong Voice Channel",
                        description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return
                
        queue = guild_queues.get(i.guild.id)
        
        if queue and queue.queue:
            total_duration = sum(song_data[3] for source, song_data in queue.queue)
            queue.clear()
        else:
            total_duration = 0
        
        embed = discord.Embed(
            title="🛑 Music Bot Stopped",
            description="**Successfully disconnected from voice channel**\n\n👋 *Thanks for using the music bot!*",
            color=0xe74c3c
        )
        embed.add_field(
            name="📊 **Session Stats**",
            value=f"```\n⏱️ Time Left in Queue: {self.format_time(total_duration)}\n🎵 Songs Cleared: {len(queue.queue) if queue else 0}\n🛑 Action: Stop\n```",
            inline=False
        )
        embed.add_field(
            name="💡 **Quick Restart**",
            value="```\n🎵 /play <song> - Start playing\n📊 /chart - Play trending\n✨ /inspire - Random song\n```",
            inline=False
        )
        embed.set_author(
            name=f"🎧 Stopped by {i.user.display_name}",
            icon_url=i.user.avatar.url
        )
        embed.set_footer(
            text="🎵 Music Bot • See you next time!",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        embed.set_thumbnail(url=i.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        if i.guild.voice_client:
            voice_channel = voice_client.channel
            await voice_channel.edit(status=None)
            await i.guild.voice_client.disconnect()
            await i.response.send_message(embed=embed)
            await self.send_static_message()
        else:
            await i.response.send_message(
                embed=discord.Embed(
                    title="❌ Not Connected",
                    description="**Bot is not connected to a voice channel**\n\n🎧 *Nothing to disconnect from*",
                    color=0xe74c3c
                )
            )
    
    @app_commands.command(name="shuffle", description="Shuffles the queue")
    async def shuffle(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.channel:
            if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Wrong Voice Channel",
                        description="**You must be in the same voice channel as the bot!**\n\n🎧 *Join the bot's voice channel to use this command*",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return

        queue = guild_queues.get(interaction.guild.id)
        
        if not queue or not queue.queue:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📋 Queue is Empty",
                    description="**No songs to shuffle**\n\n🎵 *Use `/play` to add some music first*",
                    color=0x95a5a6
                ),
                ephemeral=True
            )
            return
        
        random.shuffle(queue.queue)
        
        embed = discord.Embed(
            title="🔀 Queue Shuffled!",
            description=f"🎲 **{len(queue.queue)} songs shuffled**\n\n*Here's the new order:*",
            color=0x9b59b6
        )

        wait_time = 0
        display_count = min(10, len(queue.queue))
        for i, (source, song_data) in enumerate(queue.queue[:display_count]):
            title = song_data[0]
            duration = song_data[3]

            embed.add_field(
                name=f"🎵 **{i + 1}.** {title}",
                value=f"```\n⏱️ Duration: {self.format_time(duration)}\n🕒 Starts in: {self.format_time(wait_time)}\n```",
                inline=False
            )
            wait_time += duration
            
        if len(queue.queue) > display_count:
            embed.add_field(
                name="🎵 **More Songs...**", 
                value=f"```\n📋 +{len(queue.queue) - display_count} more songs\n⏱️ Total Duration: {self.format_time(sum(song[1][3] for song in queue.queue))}\n```", 
                inline=False
            )
        
        embed.add_field(
            name="📊 **Shuffle Stats**",
            value=f"```\n🔀 Action: Shuffle\n📋 Songs: {len(queue.queue)}\n⏱️ Total Time: {self.format_time(sum(song[1][3] for song in queue.queue))}\n```",
            inline=False
        )
        
        embed.set_author(
            name=f"🎧 Shuffled by {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url
        )
        embed.set_footer(
            text="🎵 Music Bot • Enjoy your shuffled playlist!",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel and before.channel != after.channel:
            voice_client = before.channel.guild.voice_client
            if voice_client and voice_client.channel == before.channel:
                members_in_channel = [m for m in before.channel.members if not m.bot]
                if len(members_in_channel) == 0:
                    await asyncio.sleep(5)
                    
                    if voice_client.is_connected():
                        current_members = [m for m in voice_client.channel.members if not m.bot]
                        if len(current_members) == 0:
                            guild_id = before.channel.guild.id
                            queue = guild_queues.get(guild_id)
                            if queue:
                                queue.clear()
                                queue.playing = False
                                del guild_queues[guild_id]
                            voice_channel = voice_client.channel
                            voice_channel.edit(status=None)
                            await voice_client.disconnect(force=True)
                            try:
                                channel = await self.bot.fetch_channel(I_CHANNEL)
                                if channel:
                                    await self.send_static_message()
                                else:
                                    print(f"Error: Channel with ID {I_CHANNEL} not found after fetch.")
                            except Exception as e:
                                print(f"Error sending auto-disconnect message: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update_bot_kick(self, member, before, after):
        if member.id == self.bot.user.id and before.channel is not None and after.channel is None:
            guild_id = before.channel.guild.id
            if guild_id in guild_queues:
                queue = guild_queues[guild_id]
                queue.clear()
                queue.playing = False
                del guild_queues[guild_id]
            try:
                channel = await self.bot.fetch_channel(I_CHANNEL)
                if channel:
                    await self.send_static_message()
            except Exception as e:
                print(f"Error sending disconnect message: {e}")

    async def cog_load(self):
        self.bot.tree.add_command(self.play, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.skip, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.list, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.leave, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.shuffle, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.play_chart, guild=discord.Object(id=SYNC_SERVER))
        
    async def cog_unload(self):
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        song_loader.executor.shutdown(wait=False)