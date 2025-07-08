import discord
from dotenv import dotenv_values

#
# Mods need the permisson to manage Threads.
#

#---------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------#

SEND_TICKET_FEEDBACK = True # Set to True to send feedback to users when their ticket is closed

SET_VC_STATUS_TO_MUSIC_PLAYING = False # Set to True, if the bot should change the VS status

#---------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------#

# Load config stuff
_config = dotenv_values(".env")
TICKET_CHANNEL_ID = _config.get("TICKET_CHANNEL_ID")
TOKEN = _config.get('DISCORD_TOKEN')
SYNC_SERVER = _config.get('SERVER')
I_CHANNEL = _config.get('I_CHANNEL')
TRANS_CHANNEL_ID = _config.get('TRANS_CHANNEL')
TEAM_ROLE = _config.get('TEAM_ROLE')
MOD = _config.get('MOD')
TRAIL_MOD = _config.get('TRAIL_MOD')
TICKET_CREATOR_FILE = "config/tickets.json"

# Emojis for the bot
CHECK = "<:check:1368203772123283506>"
UNCHECK = "<:X_:1373405777297014944>"
LOCK_EMOJI = "<:lock:1368203397467082823>"
TRASHCAN_EMOJI = "<:bin:1368203374092353627>"
ARCHIVE_EMOJI = "<:save:1368203337337540648>"
DELETE_EMOJI = "<:bin:1368203374092353627>"
TICKET_OPEN_EMOJI = "<:creation:1368203348066439190>"
TRANSCRIPT_EMOJI = "<:transcript:1368207338162491513>"
REOPEN_EMOJI = "<:unlock:1368203388231094373>"
INFO_EMOJI = "<:info:1370443515342884936>"
LOADING_EMOJI = "<a:2923printsdark:1367119727763259533>"
DANCE_EMOJI = "<a:dance:1369716119073587290>"
LOCK_W_REASON_EMOJI = "<:lock_with_reason:1371107805867671643>"

# Button Styles
DANGER = discord.ButtonStyle.danger
SECONDARY = discord.ButtonStyle.secondary
GREEN = discord.ButtonStyle.green
PURPLE = discord.ButtonStyle.blurple

# YT_OPTS
YT_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': False,
    'include_thumbnail': True,
    'source_address': '0.0.0.0',
    'outtmpl': '-',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '128',
    }]
}

# Embed
EMBED_FOOTER = "❤️ JabUB.css | by nino.css"