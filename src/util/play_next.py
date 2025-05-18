# ruff: noqa: F403 F405
import discord
import asyncio
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
from util.ticket_creator import *
from util.queue import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.music import guild_queues, simple_embed

async def play_next(self, guild, voice_client, interaction):
        queue = guild_queues[guild.id]
        next_song = queue.get_next()

        if next_song:
            source, (title, thumbnail, _, duration, author, song_url, likes, views, upload_date) = next_song
            queue.playing = True

            def after_song(e):
                if e:
                    print(f"Error: {e}")
                pn = play_next(guild, voice_client, interaction)
                asyncio.run_coroutine_threadsafe(pn, self.bot.loop)

            voice_client.play(source, after=after_song)

            def format_time(seconds):
                m, s = divmod(int(seconds), 60)
                return f"{m:02}:{s:02}"
            
            if upload_date and len(str(upload_date)) == 8:
                date = f"{upload_date[6:8]}.{upload_date[4:6]}.{upload_date[0:4]}"
            else:
                date = str(upload_date)
            
            def format_number(n):
                if n is None:
                    return "N/A"
                if n >= 1_000_000:
                    return f"{n/1_000_000:.1f}M"
                elif n >= 1_000:
                    return f"{n/1_000:.1f}K"
                return str(n)

            likes_fmt = format_number(likes)
            views_fmt = format_number(views)

            embed = simple_embed(
                f"{INFO_EMOJI} Now Playing: **{title}** {DANCE_EMOJI}",
                thumbnail=thumbnail
            )
            embed.add_field(name="Duration ⏳", value=f"Started: <t:{int(discord.utils.utcnow().timestamp())}:R> / **{format_time(duration)}** min", inline=False)
            embed.add_field(name="\nStats", value="\n", inline=False)
            embed.add_field(name="Likes 👍", value=likes_fmt, inline=True)
            embed.add_field(name="Views 👁️", value=views_fmt, inline=True)
            embed.add_field(name="Upload Date 📅", value=date, inline=True)
            embed.add_field(name="Song URL", value=f"{song_url}", inline=False)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
            embed.set_footer(text="JabUB.css | by www.ninoio.gay")
            
            msg = await interaction.channel.send(embed=embed)

            async def update_progress():
                await asyncio.sleep(duration)
                embed.set_field_at(0, name="Duration ⏳", value=f"Done playing! / **{format_time(duration)}**", inline=False)
                try:
                    await msg.edit(embed=embed)
                except discord.HTTPException:
                    pass

            asyncio.create_task(update_progress())
        else:
            queue.playing = False
    