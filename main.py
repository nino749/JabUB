import discord
from discord.ext import commands
from discord import Intents, TextStyle
from discord.ui import Modal, TextInput, View, Button, Select
from discord import app_commands
from dotenv import dotenv_values
import logging
import yt_dlp
from collections import deque
import asyncio
import random
import aiohttp
from jinja2 import Environment, FileSystemLoader
import io
import json
import markdown

logging.basicConfig(level=logging.INFO, format='\033[32mINFO      \033[97m%(message)s')
logger = logging.getLogger(__name__)

config = dotenv_values(".env")
TOKEN = config.get('DISCORD_TOKEN')
SYNC_SERVER = config.get('SERVER')
I_CHANNEL_ID = config.get('I_CHANNEL')
TRANS_CHANNEL_ID = config.get('TRANS_CHANNEL')
TEAM_ROLE = config.get('TEAM_ROLE')
SUPPORT_ROLE_NAME = config.get('SUPPORT_ROLE_NAME')
SUPPORTHILFE_ROLE_NAME = config.get('SUPPORTHILFE_ROLE_NAME')

GUILD_ID = discord.Object(id=SYNC_SERVER)
i_channel = I_CHANNEL_ID

TICKET_SETUP_FILE = 'ticket_setup_message.json'
DELETE_USER = ""

TICKET_CREATED_EMOJI = "<:check:1368203772123283506>"
LOCK_EMOJI = "<:lock:1368203397467082823>"
TRASHCAN_EMOJI = "<:bin:1368203374092353627>"
ARCHIVE_EMOJI = "<:save:1368203337337540648>"
DELETE_EMOJI = "<:bin:1368203374092353627>"
TICKET_OPEN_EMOJI = "<:creation:1368203348066439190>"
TRANSCRIPT_EMOJI = "<:transcript:1368207338162491513>"
REOPEN_EMOJI = "<:unlock:1368203388231094373>"
INFO_EMOJI = "<:info:1369730231924953169>"
LOADING_EMOJI = "<a:2923printsdark:1367119727763259533>"
DANCE_EMOJI = "<a:dance:1369716119073587290>"

danger = discord.ButtonStyle.danger
secondary = discord.ButtonStyle.secondary
green = discord.ButtonStyle.green

intents = Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True
intents.members = True

def load_ticket_setup_message_id():
    try:
        with open(TICKET_SETUP_FILE, 'r') as f:
            data = json.load(f)
            return data.get('channel_id'), data.get('message_id')
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None

def save_ticket_setup_message_id(channel_id, message_id):
    data = {'channel_id': channel_id, 'message_id': message_id}
    with open(TICKET_SETUP_FILE, 'w') as f:
        json.dump(data, f)

class ThreadModalRename(Modal, title='Archiviere das Ticket'):
    name_TextInput = TextInput(label="Soll das Ticket einen anderen Namen haben?", placeholder="Der neue Name des Tickets", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name_TextInput.value
        await interaction.response.send_message(f"Der Name des Threads {interaction.channel.name} aka. {interaction.channel.id} wird zu '{new_name}' geändert.", ephemeral=False)
        try:
            await interaction.channel.edit(name=new_name, archived=True)
            await interaction.edit_original_response(content=f"> Das Ticket wurde archiviert.")
        except discord.HTTPException as e:
            await interaction.channel.send(f"Fehler beim Archivieren des Tickets: {e}")

class ThreadCreationModal(Modal, title='Ticket erstellen'):
    choice_TextInput = TextInput(label="Worum geht es? [1] Discord [2] Minecraft", placeholder="Discord (1) oder Minecraft (2)", style=TextStyle.short, required=False)
    reason_TextInput = TextInput(label="Worum geht es genau?", placeholder='Dein Grund für das Ticket z.B.: "Etwas sichern"', style=TextStyle.short, required=False)
    coords_TextInput = TextInput(label="Koordinaten (Falls es um Sichern geht)", placeholder='160 20 160 bis 260 20 260', required=False, style=TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_TextInput.value
        coords = self.coords_TextInput.value
        choice = self.choice_TextInput.value

        reason_display = ""
        if reason:
            reason_display = reason
        else:
            reason_display = "Keine Angabe"

        choice_display = ""
        if choice and choice.lower() in ["1", "[1]", "discord"]:
            choice_display = "Discord"
        elif choice and choice.lower() in ["2", "[2]", "minecraft"]:
            choice_display = "Minecraft"
        else:
            choice_display = "Keine Angabe"

        coords_display = "Keine Angabe"
        if coords:
            coords_display = str(coords)

        guild = interaction.guild
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        supporthilfe_role = discord.utils.get(guild.roles, name=SUPPORTHILFE_ROLE_NAME)
        ticket_creator = interaction.user

        try:
            thread = await interaction.channel.create_thread(name=f'Ticket von {interaction.user.name}')
            
            if interaction.user not in thread.members:
                await thread.add_user(interaction.user)
            
            await thread.edit(invitable=False)
            logger.info(f"Set invitable=False for thread {thread.id}")

            thread_embed = discord.Embed(
                title=f"Ticket erstellt! {TICKET_CREATED_EMOJI}",
                description=f'Um das Ticket zu schließen drücke "{LOCK_EMOJI}" und danach auf **"Ja"**. (Wenn du es doch nicht schließen möchtest, klicke auf **"Nein"**.)',
                color=0x00ff00
            )
            thread_embed.add_field(name="Grund für das Ticket", value=reason_display, inline=True)
            thread_embed.add_field(name="Koordinaten des Gebietes", value=coords_display, inline=True)
            thread_embed.add_field(name="Aufgaben Bereich", value=choice_display, inline=True)

            async def delete_thread_confirmation(interaction: discord.Interaction):
                if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
                    await interaction.response.send_message("Du hast keine Berechtigung, diese Aktion auszuführen.", ephemeral=True)
                    return

                async def delete_yes_callback(interaction: discord.Interaction):
                    await interaction.response.send_message(f"Lösche den Thread {DELETE_EMOJI}")

                async def delete_no_callback(interaction: discord.Interaction):
                    await interaction.message.delete()

                delete_button_yes = Button(emoji=TRASHCAN_EMOJI, label="Ja, löschen", style=danger)
                delete_button_no = Button(label="Nein", style=secondary)

                delete_button_yes.callback = delete_yes_callback
                delete_button_no.callback = delete_no_callback

                view = View()
                view.add_item(delete_button_yes)
                view.add_item(delete_button_no)

                await interaction.response.send_message(view=view, content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket **löschen** möchtest?", ephemeral=False)

            async def archive_thread_callback(interaction: discord.Interaction):
                if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
                    await interaction.response.send_message("Du hast keine Berechtigung, diese Aktion auszuführen.", ephemeral=True)
                    return

                await interaction.response.send_modal(ThreadModalRename())

            async def trans_button_callback(interaction: discord.Interaction):
                if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
                    await interaction.response.send_message("Du hast keine Berechtigung, diese Aktion auszuführen.", ephemeral=True)
                    return

                await interaction.response.send_message(f"> {INFO_EMOJI} Erstelle das Transkript {LOADING_EMOJI}")

                channel = interaction.channel
                render_messages = []

                async for msg in channel.history(limit=None):
                    embed_data = []
                    for e in msg.embeds:
                        embed_dict = {
                            "title": e.title,
                            "description": e.description,
                            "color": f"#{e.color.value:06x}" if e.color else "#4f545c",
                            "image_url": e.image.url if e.image else None,
                            "thumbnail_url": e.thumbnail.url if e.thumbnail else None,
                            "fields": [
                                {"name": field.name, "value": field.value, "inline": field.inline}
                                for field in e.fields
                            ]
                        }
                        embed_data.append(embed_dict)

                    html_content = markdown.markdown(msg.clean_content)

                    render_messages.append({
                        "author_name": msg.author.display_name,
                        "avatar_url": msg.author.display_avatar.url,
                        "timestamp": msg.created_at.strftime('%d-%m-%Y %H:%M'),
                        "content": html_content,
                        "attachments": [
                            att.url for att in msg.attachments
                            if att.content_type and att.content_type.startswith("image/")
                        ],
                        "embeds": embed_data
                    })

                render_messages.reverse()

                env = Environment(loader=FileSystemLoader('.'))
                try:
                    template = env.get_template('transcript_template.html')
                except FileNotFoundError:
                    await interaction.edit_original_response("Die Datei 'transcript_template.html' wurde nicht gefunden.")
                    return

                rendered_html = template.render(
                    channel_name=channel.name,
                    messages=render_messages
                )

                buffer = io.BytesIO(rendered_html.encode())
                print(f"DEBUG     Größe des Buffers (Follow-up): {buffer.getbuffer().nbytes} Bytes")

                trans_channel = bot.get_channel(int(TRANS_CHANNEL_ID))
                
                buffer_trans = io.BytesIO(rendered_html.encode())
                await interaction.edit_original_response(content=f"> {INFO_EMOJI} Transkript in {trans_channel.mention} erstellt!")

                print(f"DEBUG     Größe des Buffers (trans_channel): {buffer_trans.getbuffer().nbytes} Bytes")
                transcript_file_trans = discord.File(buffer_trans, filename=f"transcript von {channel.name}.html")
                
                message_count = 0
                async for _ in channel.history(limit=None):
                    message_count += 1

                member_count = 0
                
                members = channel.members
                for each in members:
                    member_count += 1
                    
                embed = discord.Embed(
                    title=f"{INFO_EMOJI} Transkript - {channel.name}",
                    description=f"**Stats**",
                    color=0x00ff00
                )
                global DELETE_USER
                
                embed.add_field(name="Nachrichten", value=message_count, inline=True)
                embed.add_field(name="Benutzer", value=member_count, inline=True)
                embed.add_field(name="Geschlossen von", value=DELETE_USER, inline=True)
                embed.set_footer(text="JabUB.css | by nino.css")
                embed.timestamp = discord.utils.utcnow()
                await trans_channel.send(embed=embed, file=transcript_file_trans)

            async def reopen_button_callback(interaction: discord.Interaction):
                if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
                    await interaction.response.send_message("Du hast keine Berechtigung, diese Aktion auszuführen.", ephemeral=True)
                    return

                async for message in interaction.channel.history(limit=10):
                    if message.author == bot.user:
                        await message.delete()
                        break

                await interaction.response.send_message(f"> {ticket_creator.mention} Das Ticket wurde neu eröffnet.")

            async def close_thread_confirmation(interaction: discord.Interaction):
                async def yes_callback(interaction: discord.Interaction):
                    await interaction.response.defer()
                    global DELETE_USER
                    DELETE_USER = interaction.user.name

                    archive_button = Button(emoji=ARCHIVE_EMOJI, style=secondary)
                    archive_button.callback = archive_thread_callback

                    delete_button = Button(emoji=TRASHCAN_EMOJI, style=danger)
                    delete_button.callback = delete_thread_confirmation

                    trans_button = Button(emoji=TRANSCRIPT_EMOJI, style=secondary)
                    trans_button.callback = trans_button_callback

                    reopen_button = Button(emoji=REOPEN_EMOJI, style=green)
                    reopen_button.callback = reopen_button_callback

                    view = View()
                    view.add_item(delete_button)
                    view.add_item(reopen_button)
                    view.add_item(archive_button)
                    view.add_item(trans_button)
                    
                    has_required_role = False

                    if TEAM_ROLE in interaction.user.roles or SUPPORT_ROLE_NAME in interaction.user.roles or SUPPORTHILFE_ROLE_NAME in interaction.user.roles:
                        has_required_role = True

                    if has_required_role:
                        await interaction.channel.send(view=view, content=f"> Ich habe **{ticket_creator}** nicht entfernt - Teammitglied. Man kann es nun {TRASHCAN_EMOJI} `Löschen`, {REOPEN_EMOJI} `Neu eröffnen`, {ARCHIVE_EMOJI} `Archivieren` oder {TRANSCRIPT_EMOJI} `Transkribieren`.")
                    else:
                        await thread.remove_user(ticket_creator)
                        await interaction.channel.send(view=view, content=f"> **{ticket_creator}** wurde vom Ticket entfernt. Man kann es nun {TRASHCAN_EMOJI} `Löschen`, {REOPEN_EMOJI} `Neu eröffnen`, {ARCHIVE_EMOJI} `Archivieren` oder {TRANSCRIPT_EMOJI} `Transkribieren`.")

                async def no_callback(interaction: discord.Interaction):
                    await interaction.response.defer()
                    await interaction.message.delete()

                yes_button = Button(label="Ja", style=danger)
                no_button = Button(label="Nein", style=secondary)

                yes_button.callback = yes_callback
                no_button.callback = no_callback

                view = View()
                view.add_item(yes_button)
                view.add_item(no_button)

                await interaction.response.send_message(view=view, content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket schließen möchtest?", ephemeral=False)

            close_button = Button(emoji=LOCK_EMOJI, label="Schließe das Ticket", style=danger)
            close_button.callback = close_thread_confirmation

            view = View()
            view.add_item(close_button)
            if reason:
                await thread.edit(name=reason_display + f" von {ticket_creator.name}")
            else:
                await thread.edit(name=f"Ticket von {ticket_creator.name}")
            await thread.send(
                view=view,
                embed=thread_embed,
                content=f"Bitte schildere dein Problem oder deine Frage ausführlich, {support_role.mention if support_role else '@Support (Rolle nicht gefunden)'} {supporthilfe_role.mention if supporthilfe_role else '@Supporthilfe (Rolle nicht gefunden)'} wird dir sobald wie möglich helfen!"
            )
            await interaction.response.send_message(f"> Ticket erstellt in {thread.mention}!", ephemeral=True)

        except discord.HTTPException as e:
            await interaction.response.send_message(f'> Fehler beim Erstellen des Tickets: {e}', ephemeral=False)
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Erstellen des Tickets: {e}")
            await interaction.response.send_message(f'> Ein unerwarteter Fehler ist aufgetreten.', ephemeral=False)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Fehler bei der Modal-Interaktion: {error}")
        await interaction.response.send_message(f'> Da ist ein Fehler aufgetreten: {error}', ephemeral=False)

async def create_thread_interaction(interaction: discord.Interaction):
    await interaction.response.send_modal(ThreadCreationModal())

class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji=TICKET_OPEN_EMOJI, label="Öffne ein Ticket", style=green, custom_id="open_ticket_button")
    async def open_ticket_button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ThreadCreationModal())

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="!", intents=intents, activity=discord.Activity(name="/help", type=discord.ActivityType.competing), *args, **kwargs)

    async def on_ready(self):
        logger.info(f'{self.user} is online! Syncing commands...')
        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            logger.info(f"Synced {len(synced)} commands to guild: {GUILD_ID.id}")
            logger.info("The Bot is ready!")

            persistent_view = TicketSetupView()
            self.add_view(persistent_view)

            channel_id, message_id = load_ticket_setup_message_id()
            if channel_id and message_id:
                try:
                    channel = self.get_channel(channel_id)
                    if channel:
                        message = await channel.fetch_message(message_id)
                        await message.edit(view=persistent_view)
                        logger.info(f"Re-attached TicketSetupView to message {message_id} in channel {channel_id}")
                    else:
                        logger.warning(f"Ticket setup channel {channel_id} not found.")
                except discord.NotFound:
                    logger.warning(f"Ticket setup message {message_id} in channel {channel_id} not found. It might have been deleted.")
                except Exception as e:
                    logger.error(f"Error re-attaching TicketSetupView: {e}")

        except Exception as e:
            logger.error(f"Error while syncing {GUILD_ID.id}: {e}")

bot = Bot()

@bot.tree.command(name="tickets", description="Setup Tickets in this channel!", guild=GUILD_ID)
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support",
        description="Hast du Fragen oder möchtest du etwas anmerken? Öffne jetzt ein Support-Ticket, um Kontakt mit unserem Team aufzunehmen. Es wird so schnell es geht jemand antworten. Du brauchst niemanden vom Team anzupingen.",
        color=0x00ff00
    )
    embed.add_field(name="Was als nächstes?", value='Als nächstes kriegst du ein paar Fragen, zum erstellen eines Tickets. **Zum überspringen, einfach auf "weiter" drücken.**')
    embed.set_footer(text="JabUB.css | by nino.css")

    view = TicketSetupView()

    message = await interaction.channel.send(embed=embed, view=view)

    save_ticket_setup_message_id(interaction.channel.id, message.id)

    await interaction.response.send_message(f"{interaction.user.mention} Ich habe das Support-Embed geschickt!", ephemeral=True)



# -----------------------------------------------#
# ------------------MUSIC BOT--------------------#
#------------------------------------------------#



yt_opts = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': False,
    'include_thumbnail': True,
    'source_address': '0.0.0.0'
}

def simple_embed(text: str, thumbnail: str | None = None, color: int = 0x00ff00):
    embed = discord.Embed(description=text, color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed

class Queue:
    def __init__(self):
        self.queue = deque()
        self.playing = False
    
    def add(self, source, title):
        self.queue.append((source, title))
    
    def get_next(self):
        return self.queue.popleft() if self.queue else None

    def is_empty(self):
        return len(self.queue) == 0

guild_queues = {}

@bot.tree.command(name="play", description="plays music", guild=GUILD_ID)
@app_commands.describe(url="URL or search term")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send(
            embed=simple_embed(f"{INFO_EMOJI} You have to be in a VC!"),
            ephemeral=True
        )
        return

    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        channel = interaction.user.voice.channel
        await channel.connect()
        voice_client = interaction.guild.voice_client

    loading_message = await interaction.followup.send(
        embed=simple_embed("Loading music <a:2923printsdark:1367119727763259533>")
    )

    search_query = url if url.startswith("http") else f"ytsearch:{url}"

    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
    except Exception as e:
        await interaction.followup.send(
            embed=simple_embed(f"{INFO_EMOJI} Failed to load video/playlist: {e}"),
            ephemeral=True
        )
        return

    if interaction.guild.id not in guild_queues:
        guild_queues[interaction.guild.id] = Queue()
    queue = guild_queues[interaction.guild.id]

    if "entries" in info:
        entries = info["entries"]

        if not url.startswith("http"):
            info = entries[0]
            audio_url = info.get("url")
            title = info.get("title", "Unknown title")
            thumbnail = info.get("thumbnail")
            await bot.change_presence(activity=discord.Activity(name=title, type=discord.ActivityType.listening))

            try:
                source = await discord.FFmpegOpusAudio.from_probe(audio_url, method='fallback')
                queue.add(source, (title, thumbnail))
                await interaction.channel.send(
                    embed=simple_embed(
                        f"{INFO_EMOJI}\n *Interaction User: {interaction.user.mention}*\n Added to queue: **{title}**",
                        thumbnail=thumbnail
                    )
                )
                await loading_message.delete()
            except Exception as e:
                await interaction.channel.send(
                    embed=simple_embed(f"{INFO_EMOJI}\n *Interaction User: {interaction.user.mention}*\n Failed to load audio: {e}"),
                    ephemeral=True
                )
                await loading_message.delete()
                return
        else:
            added_count = 0
            first_thumbnail = None
            for entry in entries:
                audio_url = entry.get("url")
                title = entry.get("title", "Unknown title")
                thumbnail = entry.get("thumbnail")
                await bot.change_presence(activity=discord.Activity(name=title, type=discord.ActivityType.listening))

                if not first_thumbnail:
                    first_thumbnail = thumbnail

                try:
                    source = await discord.FFmpegOpusAudio.from_probe(audio_url, method='fallback')
                    queue.add(source, (title, thumbnail))
                    added_count += 1
                except Exception:
                    continue
            await interaction.channel.send(
                embed=simple_embed(
                    f"{INFO_EMOJI}\n *Interaction User: {interaction.user.mention}*\n Added playlist to queue! ({added_count} tracks)",
                    thumbnail=first_thumbnail
                )
            )
            await loading_message.delete()
    else:
        audio_url = info.get("url")
        title = info.get("title", "Unknown title")
        thumbnail = info.get("thumbnail")
        await bot.change_presence(activity=discord.Activity(name=title, type=discord.ActivityType.listening))

        try:
            source = await discord.FFmpegOpusAudio.from_probe(audio_url, method='fallback')
            queue.add(source, (title, thumbnail))
            await interaction.channel.send(
                embed=simple_embed(
                    f"{INFO_EMOJI}\n *Interaction User: {interaction.user.mention}*\n Added to queue: **{title}**",
                    thumbnail=thumbnail
                )
            )
            await loading_message.delete()
        except Exception as e:
            await interaction.channel.send(
                embed=simple_embed(f"{INFO_EMOJI}\n *Interaction User: {interaction.user.mention}*\n Failed to load audio: {e}"),
                ephemeral=True
            )
            await loading_message.delete()
            return

    if not queue.playing:
        await play_next(interaction.guild, voice_client)

async def play_next(guild, voice_client):
    queue = guild_queues[guild.id]
    next_song = queue.get_next()

    if next_song:
        source, (title, thumbnail) = next_song
        queue.playing = True

        def after_song(e):
            if e:
                print(f"Error: {e}")
            pn = play_next(guild, voice_client)
            asyncio.run_coroutine_threadsafe(pn, bot.loop)

        voice_client.play(source, after=after_song)
        channel = bot.get_channel(i_channel)
        if channel:
            await channel.send(
                embed=simple_embed(f"{INFO_EMOJI} Now Playing: **{title}** {DANCE_EMOJI}", thumbnail=thumbnail)
            )
    else:
        queue.playing = False
        await bot.change_presence(activity=discord.Activity(name="/help", type=discord.ActivityType.competing))
        
@bot.tree.command(name="radio", description="Play a radio stream", guild=GUILD_ID)
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
async def radio_command(interaction: discord.Interaction, url: str | None = None, choice: app_commands.Choice[str] | None = None):
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

    await interaction.response.defer()

    if choice:
        stream_url = choice.value
    elif url:
        stream_url = url
    else:
        await interaction.followup.send(embed=simple_embed(f"{INFO_EMOJI} Please select a radio."), ephemeral=True)
    
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

    try:
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)

        voice_client = await voice_channel.connect() if voice_client is None or not voice_client.is_connected() else voice_client
        voice_client.play(source)

        await bot.change_presence(activity=discord.Activity(name="Live Radio", type=discord.ActivityType.listening))
        await interaction.followup.send(
            embed=simple_embed(f"Interaction User: {interaction.user.mention}\n{INFO_EMOJI} Now playing radio:\n`{stream_url}` {DANCE_EMOJI}"),
        )
        
    except discord.ClientException as e:
        await interaction.followup.send(
            embed=simple_embed(f"{INFO_EMOJI} Error playing the radio stream: {e}"),
            ephemeral=True
        )
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            
    except FileNotFoundError:
        await interaction.followup.send(
            embed=simple_embed("FFmpeg not found. Make sure it is installed and added to PATH."),
            ephemeral=True
        )
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            
    except Exception as e:
        await interaction.followup.send(
            embed=simple_embed(f"An unexpected error occurred: {e}"),
            ephemeral=True
        )
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
                
@bot.tree.command(name="fs", description="skips the current song!", guild=GUILD_ID)
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_playing():
        await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} Im not in a VC rn."), ephemeral=True)
        return

    queue = guild_queues.get(interaction.guild.id)
    if queue:
        queue.playing = False

    voice_client.stop()
    await interaction.response.send_message(embed=simple_embed(f"Skipped song! {TICKET_CREATED_EMOJI}"))

@bot.tree.command(name="ls", description="lists queued songs", guild=GUILD_ID)
async def list(interaction: discord.Interaction):
    queue = guild_queues.get(interaction.guild.id)

    if not queue or not queue.queue:
        await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} There is no queue"))
        return
    
    embed = discord.Embed(
        title=f"{INFO_EMOJI} Queue",
        description="Here are all queued songs: ",
        color=0x00ff00
    )
    
    for i, (_, title) in enumerate(queue.queue):
        if i >= 25:
            embed.add_field(name="", value="", inline=False)
            break
        embed.add_field(name=f"{i + 1}.", value=title, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="fl", description="Stops the Bot", guild=GUILD_ID)
async def leave(i: discord.Interaction):
    if i.guild.voice_client:
        await i.guild.voice_client.disconnect()
        await i.response.send_message(embed=simple_embed(f"Left {i.user.voice.channel}."))
        await bot.change_presence(activity=discord.Activity(name="/help", type=discord.ActivityType.competing))
    else:
        await i.response.send_message(embed=simple_embed(f"{INFO_EMOJI} You have to be in a VC"))

@bot.tree.command(name="fp", description="Pauses or unpauses the current song", guild=GUILD_ID)
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_playing():
        await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} No song is currently playing!"), ephemeral=True)
        return
    if voice_client.is_paused():
        voice_client.resume()  
        await interaction.response.send_message(embed=simple_embed(f"Resumed the song! {TICKET_CREATED_EMOJI}"))
    else:
        voice_client.pause()  
        await interaction.response.send_message(embed=simple_embed(f"Paused the song! {TICKET_CREATED_EMOJI}"))
        
@bot.tree.command(name="fsf", description="Shuffles the queue", guild=GUILD_ID)
async def shuffle(interaction: discord.Interaction):
    queue = guild_queues.get(interaction.guild.id)
    
    if not queue or not queue.queue:
        await interaction.response.send_message(embed=simple_embed(f"{INFO_EMOJI} The queue is empty!"), ephemeral=True)
        return
    
    random.shuffle(queue.queue)

    await interaction.response.send_message(embed=simple_embed(f"Queue shuffled! {TICKET_CREATED_EMOJI}"))

if __name__ == "__main__":
    bot.run(TOKEN)