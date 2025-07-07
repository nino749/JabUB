from constants import *

# Language Configuration
LANGUAGE = "en"

# English Translations
TEXTS_EN = {
    # First Ticket embed texts
    "SETUP_MESSAGE": "Which language should the bot use?",
    "GERMAN": "🇩🇪 German",
    "ENGLISH": "🇬🇧 English",
    "SUPPORT_HEADER_TEXT": "🎫 Support",
    "EMBED_CREATED": "Embed has been sent",
    "TICKET_CREATION_EMBED_TEXT": "Do you have questions or want to report something? Open a **Support Ticket** now to get in touch with our team. Someone will respond as soon as possible. You don't need to ping anyone from the team.",
    "WHAT_NEXT": "What's next?",
    "WHAT_NEXT_VALUE": 'Select a **category** from the **dropdown menu** to get more information and to **customize your ticket**.',
    
    # Error Messages
    "NO_PERMISSION": "You don't have permission for this command.",
    "CAN_ONLY_BE_USED_IN_THREAD": "This command can only be used in a ticket thread.",
    "NO_MEMBER": "Error: The member does not exist.",
    "MEMBER_NOT_FOUND": "Error: The member could not be found.",
    
    # Close Embed
    "CLOSE_EMBED_DESC": f'Close the ticket with {LOCK_EMOJI} and confirm with **"Yes"**, or cancel with **"No"**.\n To close the ticket with a **reason**, press {LOCK_W_REASON_EMOJI} and enter your reason.',
    "TICKET_OVERVIEW_TITLE": "🎫 Ticket Overview",
    
    # Embed Footer
    "EMBED_FOOTER": "Ticket System",
    
    # Ticket Messages
    "TICKET_CREATION_SUCCESS": "Ticket created in {thread}!",
    "TICKET_CREATION_ERROR": "Error creating ticket.",
    "TICKET_CLOSE_CONFIRMATION": "> {user} Are you sure you want to close the ticket?",
    "TICKET_CLOSE_WITH_REASON_CONFIRMATION": "> {user} Are you sure you want to close the ticket with the reason: ```{reason}```?",
    "DEFAULT_HELP_MESSAGE": "You will be helped as soon as possible!",
    "TICKET_CLOSED_TIMEOUT": "> Ticket closed for the following reason: ```Timeout after 30 days.```",
    "TICKET_CLOSED_BY": "> Ticket closed by **{user_display}** *({user_name})*",
    "TICKET_CLOSED_BY_REASON": "> Ticket closed by **{user_display}** *({user_name})* for the following reason: ```{reason}```",
    "TICKET_REOPENED": "> {user} The ticket has been reopened.",
    "SETUP_MESSAGES_DELETED": "> All setup messages in the ticket have been deleted.",
    
    # Button Labels
    "CANCEL_BUTTON_LABEL": "Cancel",
    "CLOSE_TICKET_BUTTON": "Close Ticket",
    "CLOSE_TICKET_REASON_BUTTON": "Close Ticket with Reason",
    "YES_CLOSE_BUTTON": "Yes, close",
    "NO_BUTTON": "No",
    "DELETE_BUTTON": "Delete",
    "REOPEN_BUTTON": "Reopen",
    "TRANSCRIPT_BUTTON": "Transcript",
    "ARCHIVE_BUTTON": "Archive",
    "YES_DELETE_BUTTON": "Yes, delete",
    
    # Confirmation Messages
    "CLOSE_CONFIRMATION": "> {user} Are you sure you want to close the ticket?",
    "DELETE_CONFIRMATION": "> {user} Do you really want to delete this ticket?",
    
    # Dropdown Options
    "DROPDOWN_PLACEHOLDER": "Select an option",
    "DISCORD_GENERAL": "General: Discord",
    "MINECRAFT_GENERAL": "General: Minecraft",
    "SURVIVAL_AREA": "Survival: Secure Area",
    "CREATIVE_PLOT": "Creative: Transfer Plot",
    "UNBAN_REQUEST": "Unban Request",
    "OTHER": "Other",
    
    # Ticket Category Messages
    "GENERAL_DISCORD_HELP": "How can we help you? What is your concern?",
    "GENERAL_MINECRAFT_HELP": "How can we help you? What is your concern?",
    "UNBAN_REQUEST_MESSAGE": "Now write your unban request. We will discuss it internally and get back to you here.",
    "OTHER_HELP": "How can we help you? What is your concern?",
    
    # Modal Titles and Labels
    "ARCHIVE_TICKET_MODAL_TITLE": "Archive the ticket",
    "RENAME_TICKET_LABEL": "Should the ticket have a different name?",
    "RENAME_TICKET_PLACEHOLDER": "The new name of the ticket",
    "ARCHIVE_ERROR": "Error archiving ticket: {error}",
    
    "TICKET_DESCRIPTION_MODAL_TITLE": "Ticket Description",
    "TICKET_DESCRIPTION_LABEL": "Ticket Description",
    "DESCRIPTION_ERROR": "Error changing description: {error}",
    
    "CLOSE_TICKET_MODAL_TITLE": "Close Ticket",
    "CLOSE_REASON_LABEL": "Reason",
    "CLOSE_REASON_PLACEHOLDER": "Enter the reason for closing the ticket.",
    
    "AREA_SAVING_MODAL_TITLE": "Secure Area",
    "AREA_SAVING_TITLE": "Secure Area",
    "WORLD_LABEL": "World",
    "WORLD_PLACEHOLDER": "The world, e.g. Overworld, Nether, End",
    "COORDINATES_LABEL": "Coordinates",
    "COORDINATES_PLACEHOLDER": "120 60 120 to 200 70 200",
    
    "PLOT_TRANSFER_MODAL_TITLE": "Transfer Plot",
    "PLOT_TRANSFER_TITLE": "Transfer Plot",
    "INGAME_NAME_LABEL": "In-game Name",
    "INGAME_NAME_PLACEHOLDER": "Your Minecraft account name",
    "CANSTEIN_NAME_LABEL": "Canstein Number",
    "CANSTEIN_NAME_PLACEHOLDER": "The number of the used Canstein account",
    
    # Embed Titles and Descriptions
    "TICKET_CLOSED_EMBED_TITLE": "Ticket Closed - {channel_name}",
    "TICKET_CLOSED_EMBED_DESC": "**Closed by:** {user}\n**Reason:** {reason}\n**Server:** {guild_name}",
    
    # Creation texts
    "LABEL_DISCORD": "General: Discord",
    "LABEL_MINECRAFT": "General: Minecraft",
    "LABEL_BEREICH": "Survival: Secure Area",
    "LABEL_PARZELLE": "Creative: Transfer Plot",
    "LABEL_ENTBANNUNG": "Unban Request",
    "LABEL_SONSTIGES": "Other",
    
    "PLACEHOLDER_TEXT": "Select an option",
    
    "TITLE_DISCORD": "General Discord",
    "TITLE_MINECRAFT": "General Minecraft",
    "TITLE_ENTBANNUNG": "Unban Request",
    "TITLE_BEREICH": "Survival: Secure Area",
    "TITLE_PARZELLE": "Creative: Transfer Plot",
    "TITLE_SONSTIGES": "Other",
    
    "MESSAGE_GENERAL": "How can we help you? What is your concern?",
    "MESSAGE_ENTBANNUNG": "Now write your unban request. We will discuss it internally and get back to you here."
}

# Function to get text based on current language
def get_text(key):
    """Get text in the current language"""
    return TEXTS_EN.get(key, key)

# Export all text constants
# Creation texts
LABEL_DISCORD = get_text("LABEL_DISCORD")
LABEL_MINECRAFT = get_text("LABEL_MINECRAFT")
LABEL_BEREICH = get_text("LABEL_BEREICH")
LABEL_PARZELLE = get_text("LABEL_PARZELLE")
LABEL_ENTBANNUNG = get_text("LABEL_ENTBANNUNG")
LABEL_SONSTIGES = get_text("LABEL_SONSTIGES")

PLACEHOLDER_TEXT = get_text("PLACEHOLDER_TEXT")

TITLE_DISCORD = get_text("TITLE_DISCORD")
TITLE_MINECRAFT = get_text("TITLE_MINECRAFT")
TITLE_ENTBANNUNG = get_text("TITLE_ENTBANNUNG")
TITLE_BEREICH = get_text("TITLE_BEREICH")
TITLE_PARZELLE = get_text("TITLE_PARZELLE")
TITLE_SONSTIGES = get_text("TITLE_SONSTIGES")

MESSAGE_GENERAL = get_text("MESSAGE_GENERAL")
MESSAGE_ENTBANNUNG = get_text("MESSAGE_ENTBANNUNG")

SETUP_MESSAGE = get_text("SETUP_MESSAGE")
ENGLISH_BTN = get_text("ENGLISH")
GERMAN_BTN = get_text("GERMAN")
SUPPORT_HEADER_TEXT = get_text("SUPPORT_HEADER_TEXT")
EMBED_CREATED = get_text("EMBED_CREATED")
TICKET_CREATION_EMBED_TEXT = get_text("TICKET_CREATION_EMBED_TEXT")
WHAT_NEXT = get_text("WHAT_NEXT")
WHAT_NEXT_VALUE = get_text("WHAT_NEXT_VALUE")

NO_PERMISSION = get_text("NO_PERMISSION")
CAN_ONLY_BE_USED_IN_THREAD = get_text("CAN_ONLY_BE_USED_IN_THREAD")
NO_MEMBER = get_text("NO_MEMBER")
MEMBER_NOT_FOUND = get_text("MEMBER_NOT_FOUND")

CLOSE_EMBED_DESC = get_text("CLOSE_EMBED_DESC")
TICKET_OVERVIEW_TITLE = get_text("TICKET_OVERVIEW_TITLE")

EMBED_FOOTER = get_text("EMBED_FOOTER")

TICKET_CREATION_SUCCESS = get_text("TICKET_CREATION_SUCCESS")
TICKET_CREATION_ERROR = get_text("TICKET_CREATION_ERROR")
TICKET_CLOSE_CONFIRMATION = get_text("TICKET_CLOSE_CONFIRMATION")
TICKET_CLOSE_WITH_REASON_CONFIRMATION = get_text("TICKET_CLOSE_WITH_REASON_CONFIRMATION")
DEFAULT_HELP_MESSAGE = get_text("DEFAULT_HELP_MESSAGE")
TICKET_CLOSED_TIMEOUT = get_text("TICKET_CLOSED_TIMEOUT")
TICKET_CLOSED_BY = get_text("TICKET_CLOSED_BY")
TICKET_CLOSED_BY_REASON = get_text("TICKET_CLOSED_BY_REASON")
TICKET_REOPENED = get_text("TICKET_REOPENED")
SETUP_MESSAGES_DELETED = get_text("SETUP_MESSAGES_DELETED")

CANCEL_BUTTON_LABEL = get_text("CANCEL_BUTTON_LABEL")
CLOSE_TICKET_BUTTON = get_text("CLOSE_TICKET_BUTTON")
CLOSE_TICKET_REASON_BUTTON = get_text("CLOSE_TICKET_REASON_BUTTON")
YES_CLOSE_BUTTON = get_text("YES_CLOSE_BUTTON")
NO_BUTTON = get_text("NO_BUTTON")
DELETE_BUTTON = get_text("DELETE_BUTTON")
REOPEN_BUTTON = get_text("REOPEN_BUTTON")
TRANSCRIPT_BUTTON = get_text("TRANSCRIPT_BUTTON")
ARCHIVE_BUTTON = get_text("ARCHIVE_BUTTON")
YES_DELETE_BUTTON = get_text("YES_DELETE_BUTTON")

CLOSE_CONFIRMATION = get_text("CLOSE_CONFIRMATION")
DELETE_CONFIRMATION = get_text("DELETE_CONFIRMATION")

DROPDOWN_PLACEHOLDER = get_text("DROPDOWN_PLACEHOLDER")
DISCORD_GENERAL = get_text("DISCORD_GENERAL")
MINECRAFT_GENERAL = get_text("MINECRAFT_GENERAL")
SURVIVAL_AREA = get_text("SURVIVAL_AREA")
CREATIVE_PLOT = get_text("CREATIVE_PLOT")
UNBAN_REQUEST = get_text("UNBAN_REQUEST")
OTHER = get_text("OTHER")

GENERAL_DISCORD_HELP = get_text("GENERAL_DISCORD_HELP")
GENERAL_MINECRAFT_HELP = get_text("GENERAL_MINECRAFT_HELP")
UNBAN_REQUEST_MESSAGE = get_text("UNBAN_REQUEST_MESSAGE")
OTHER_HELP = get_text("OTHER_HELP")

# Modal texts
ARCHIVE_TICKET_MODAL_TITLE = get_text("ARCHIVE_TICKET_MODAL_TITLE")
RENAME_TICKET_LABEL = get_text("RENAME_TICKET_LABEL")
RENAME_TICKET_PLACEHOLDER = get_text("RENAME_TICKET_PLACEHOLDER")
ARCHIVE_ERROR = get_text("ARCHIVE_ERROR")

TICKET_DESCRIPTION_MODAL_TITLE = get_text("TICKET_DESCRIPTION_MODAL_TITLE")
TICKET_DESCRIPTION_LABEL = get_text("TICKET_DESCRIPTION_LABEL")
DESCRIPTION_ERROR = get_text("DESCRIPTION_ERROR")

CLOSE_TICKET_MODAL_TITLE = get_text("CLOSE_TICKET_MODAL_TITLE")
CLOSE_REASON_LABEL = get_text("CLOSE_REASON_LABEL")
CLOSE_REASON_PLACEHOLDER = get_text("CLOSE_REASON_PLACEHOLDER")

AREA_SAVING_MODAL_TITLE = get_text("AREA_SAVING_MODAL_TITLE")
AREA_SAVING_TITLE = get_text("AREA_SAVING_TITLE")
WORLD_LABEL = get_text("WORLD_LABEL")
WORLD_PLACEHOLDER = get_text("WORLD_PLACEHOLDER")
COORDINATES_LABEL = get_text("COORDINATES_LABEL")
COORDINATES_PLACEHOLDER = get_text("COORDINATES_PLACEHOLDER")

PLOT_TRANSFER_MODAL_TITLE = get_text("PLOT_TRANSFER_MODAL_TITLE")
PLOT_TRANSFER_TITLE = get_text("PLOT_TRANSFER_TITLE")
INGAME_NAME_LABEL = get_text("INGAME_NAME_LABEL")
INGAME_NAME_PLACEHOLDER = get_text("INGAME_NAME_PLACEHOLDER")
CANSTEIN_NAME_LABEL = get_text("CANSTEIN_NAME_LABEL")
CANSTEIN_NAME_PLACEHOLDER = get_text("CANSTEIN_NAME_PLACEHOLDER")

TICKET_CLOSED_EMBED_TITLE = get_text("TICKET_CLOSED_EMBED_TITLE")
TICKET_CLOSED_EMBED_DESC = get_text("TICKET_CLOSED_EMBED_DESC")

NO_MEMBER = "> Error: Member was not found."
NO_PERMISSION = "> You don't have permission to perform this action."
SAME_VC = "> You must be in the same voice channel as the bot to use this command."