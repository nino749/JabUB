from constants import *

# Language Configuration
LANGUAGE = "de"

# German Translations
TEXTS_DE = {
    # First Ticket embed texts
    "SETUP_MESSAGE": "Welche Sprache soll der Bot benutzen?",
    "GERMAN": "🇩🇪 Deutsch",
    "ENGLISH": "🇬🇧 Englisch",
    "SUPPORT_HEADER_TEXT": "🎫 Support",
    "EMBED_CREATED": "Embed wurde gesendet",
    "TICKET_CREATION_EMBED_TEXT": "Hast du Fragen oder möchtest etwas anmerken? Öffne jetzt ein **Support-Ticket**, um Kontakt mit unserem Team aufzunehmen. Es wird so schnell es geht jemand antworten. Du brauchst niemanden vom Team anzupingen.",
    "WHAT_NEXT": "Was als nächstes?",
    "WHAT_NEXT_VALUE": 'Wähle eine **Kategorie** aus dem **Drop-Down Menü** aus, um weitere Informationen zu erhalten und um dein **Ticket anzupassen**.',
    
    # Error Messages
    "NO_PERMISSION": "Du hast keine Berechtigung für diesen Befehl.",
    "CAN_ONLY_BE_USED_IN_THREAD": "Dieser Befehl kann nur in einem Ticket-Thread verwendet werden.",
    "NO_MEMBER": "Fehler: Der Member existiert nicht.",
    "MEMBER_NOT_FOUND": "Fehler: Der Member konnte nicht gefunden werden.",
    
    # Close Embed
    "CLOSE_EMBED_DESC": f'Schließe das Ticket mit {LOCK_EMOJI} und bestätige mit **"Ja"**, oder brich mit **"Nein"** ab.\n Um das Ticket mit einem **Grund** zuschließen, drücke auf {LOCK_W_REASON_EMOJI} und gib deinen Grund an.',
    "TICKET_OVERVIEW_TITLE": "🎫 Ticket Übersicht",
    
    # Embed Footer
    "EMBED_FOOTER": "Ticket System",
    
    # Ticket Messages
    "TICKET_CREATION_SUCCESS": "Ticket erstellt in {thread}!",
    "TICKET_CREATION_ERROR": "Fehler beim Erstellen des Tickets.",
    "TICKET_CLOSE_CONFIRMATION": "> {user} Bist du dir sicher, dass du das Ticket schließen möchtest?",
    "TICKET_CLOSE_WITH_REASON_CONFIRMATION": "> {user} Bist du dir sicher, dass du das Ticket mit dem Grund: ```{reason}``` schließen möchtest?",
    "DEFAULT_HELP_MESSAGE": "Es wird dir so schnell wie möglich geholfen!",
    "TICKET_CLOSED_TIMEOUT": "> Ticket geschlossen aus folgendem Grund: ```Time-Out nach 30 Tagen.```",
    "TICKET_CLOSED_BY": "> Ticket geschlossen von **{user_display}** *({user_name})*",
    "TICKET_CLOSED_BY_REASON": "> Ticket geschlossen von **{user_display}** *({user_name})* aus folgendem Grund: ```{reason}```",
    "TICKET_REOPENED": "> {user} Das Ticket wurde neu eröffnet.",
    "SETUP_MESSAGES_DELETED": "> Alle setup Nachrichten im Ticket wurden gelöscht.",
    
    # Button Labels
    "CANCEL_BUTTON_LABEL": "Abbrechen",
    "CLOSE_TICKET_BUTTON": "Ticket schließen",
    "CLOSE_TICKET_REASON_BUTTON": "Ticket mit Grund schließen",
    "YES_CLOSE_BUTTON": "Ja, schließen",
    "NO_BUTTON": "Nein",
    "DELETE_BUTTON": "Löschen",
    "REOPEN_BUTTON": "Neu eröffnen",
    "TRANSCRIPT_BUTTON": "Transkribieren",
    "ARCHIVE_BUTTON": "Archivieren",
    "YES_DELETE_BUTTON": "Ja, löschen",
    
    # Confirmation Messages
    "CLOSE_CONFIRMATION": "> {user} Bist du dir sicher, dass du das Ticket schließen möchtest?",
    "DELETE_CONFIRMATION": "> {user} Möchtest du dieses Ticket wirklich löschen?",
    
    # Dropdown Options
    "DROPDOWN_PLACEHOLDER": "Wähle eine Option",
    "DISCORD_GENERAL": "Allgemein: Discord",
    "MINECRAFT_GENERAL": "Allgemein: Minecraft",
    "SURVIVAL_AREA": "Survival: Bereich sichern",
    "CREATIVE_PLOT": "Kreativ: Parzelle übertragen",
    "UNBAN_REQUEST": "Entbannungsantrag",
    "OTHER": "Sonstiges",
    
    # Ticket Category Messages
    "GENERAL_DISCORD_HELP": "Wie können wir dir helfen? Was ist dein Anliegen?",
    "GENERAL_MINECRAFT_HELP": "Wie können wir dir helfen? Was ist dein Anliegen?",
    "UNBAN_REQUEST_MESSAGE": "Schreibe nun dein Entbannungs-Antrag. Wir werden ihn intern besprechen und uns bei dir hier melden.",
    "OTHER_HELP": "Wie können wir dir helfen? Was ist dein Anliegen?",
    
    # Modal Titles and Labels
    "ARCHIVE_TICKET_MODAL_TITLE": "Archiviere das Ticket",
    "RENAME_TICKET_LABEL": "Soll das Ticket einen anderen Namen haben?",
    "RENAME_TICKET_PLACEHOLDER": "Der neue Name des Tickets",
    "ARCHIVE_ERROR": "Fehler beim Archivieren des Tickets: {error}",
    
    "TICKET_DESCRIPTION_MODAL_TITLE": "Beschreibung des Tickets",
    "TICKET_DESCRIPTION_LABEL": "Beschreibung des Tickets",
    "DESCRIPTION_ERROR": "Fehler beim ändern der Beschreibung: {error}",
    
    "CLOSE_TICKET_MODAL_TITLE": "Ticket schließen",
    "CLOSE_REASON_LABEL": "Grund",
    "CLOSE_REASON_PLACEHOLDER": "Gib den Grund für das Schließen des Tickets an.",
    
    "AREA_SAVING_MODAL_TITLE": "Bereich Sichern",
    "AREA_SAVING_TITLE": "Bereich Sichern",
    "WORLD_LABEL": "Welt",
    "WORLD_PLACEHOLDER": "Die Welt, e.g. Overworld, Nether, End",
    "COORDINATES_LABEL": "Koordinaten",
    "COORDINATES_PLACEHOLDER": "120 60 120 bis 200 70 200",
    
    "PLOT_TRANSFER_MODAL_TITLE": "Parzelle übertragen",
    "PLOT_TRANSFER_TITLE": "Parzelle übertragen",
    "INGAME_NAME_LABEL": "Ingame Name",
    "INGAME_NAME_PLACEHOLDER": "Der Name deines Minecraft Accounts",
    "CANSTEIN_NAME_LABEL": "Canstein Nummer",
    "CANSTEIN_NAME_PLACEHOLDER": "Die Nummer des benutzten Canstein Accounts",
    
    # Embed Titles and Descriptions
    "TICKET_CLOSED_EMBED_TITLE": "Ticket geschlossen - {channel_name}",
    "TICKET_CLOSED_EMBED_DESC": "**Geschlossen von:** {user}\n**Grund:** {reason}\n**Server:** {guild_name}",
    
    # Creation texts
    "LABEL_DISCORD": "Allgemein: Discord",
    "LABEL_MINECRAFT": "Allgemein: Minecraft",
    "LABEL_BEREICH": "Survival: Bereich sichern",
    "LABEL_PARZELLE": "Kreativ: Parzelle übertragen",
    "LABEL_ENTBANNUNG": "Entbannungsantrag",
    "LABEL_SONSTIGES": "Sonstiges",
    
    "PLACEHOLDER_TEXT": "Wähle eine Option",
    
    "TITLE_DISCORD": "Allgemeines Discord",
    "TITLE_MINECRAFT": "Allgemeines Minecraft",
    "TITLE_ENTBANNUNG": "Entbannungsantrag",
    "TITLE_BEREICH": "Survival: Bereich sichern",
    "TITLE_PARZELLE": "Kreativ: Parzelle übertragen",
    "TITLE_SONSTIGES": "Sonstiges",
    
    "MESSAGE_GENERAL": "Wie können wir dir helfen? Was ist dein Anliegen?",
    "MESSAGE_ENTBANNUNG": "Schreibe nun dein Entbannungs-Antrag. Wir werden ihn intern besprechen und uns bei dir hier melden."
}

# Function to get text based on current language
def get_text(key):
    """Get text in the current language"""
    return TEXTS_DE.get(key, key)

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

NO_MEMBER = "> Fehler: Member wurde nicht gefunden."
NO_PERMISSION = "> Du hast keine Berechtigung, diese Aktion auszuführen."
SAME_VC = "> Du musst dich im selben Sprachkanal wie der Bot befinden, um diesen Befehl zu nutzen."