# ruff: noqa: F403 F405
import discord
from discord.ui import View, Button
from constants import *
from modals.ticketmodals import *
from typing import TYPE_CHECKING
from util.ticket_creator import get_ticket_creator, delete_ticket_creator
from texts import *
import asyncio
import logging
import colorlog

if TYPE_CHECKING:
    from cogs.tickets import TicketCog
    
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

# Define all persistent views
class PersistentCloseView(View):
    def __init__(self, bot, ticketcog: "TicketCog"):
        super().__init__(timeout=None)
        self.ticketcog = ticketcog
        self.bot = bot
        
        close_btn = Button(label="Ticket schließen", style=DANGER, emoji=LOCK_EMOJI, custom_id="close_ticket_button")
        close_btn.callback = self.close_button
        
        close_reason_btn = Button(label="Ticket mit Grund schließen", style=DANGER, emoji=LOCK_W_REASON_EMOJI, custom_id="close_ticket_button_reason")
        close_reason_btn.callback = self.close_button_with_reason
        
        self.add_item(close_btn)
        self.add_item(close_reason_btn)
    
    async def close_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked close_button in {interaction.channel}")
        await interaction.response.send_message(view=CloseConfirmView(ticketcog=self.ticketcog, bot=self.bot), content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket schließen möchtest?")
    
    async def close_button_with_reason(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked close_button_with_reason in {interaction.channel}")
        await interaction.response.send_modal(closeThreadReasonModal(ticketcog=self.ticketcog))

# The close view, with a reason
class CloseReasonConfirmView(View):
    def __init__(self, bot, ticketcog: "TicketCog", reason: str = ""):
        super().__init__(timeout=180)
        self.bot = bot
        self.reason = reason
        self.ticketcog = ticketcog
        
        yes_button = Button(emoji=CHECK, style=DANGER, label="Ja, schließen")
        yes_button.callback = self.yes_button
        
        no_button = Button(emoji=UNCHECK, style=SECONDARY, label="Nein")
        no_button.callback = self.no_button
        
        self.add_item(yes_button)
        self.add_item(no_button)
        
    async def yes_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} confirmed closing ticket with reason '{self.reason}' in {interaction.channel}")
        await interaction.message.delete()
        global DELETE_USER
        DELETE_USER = interaction.user
        reason = self.reason
        
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        
        if TICKET_CREATOR_ID is None:
            logger.warning(f"Ticket creator ID not found for channel {interaction.channel.id}")
            pass

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if TICKET_CREATOR is None:
            logger.warning(f"Ticket creator not found in guild for ID {TICKET_CREATOR_ID}")
            pass
        
        embed = discord.Embed(
            title=f"{LOCK_EMOJI} Ticket geschlossen - {interaction.channel.name}",
            description=f"**Geschlossen von:** {interaction.user.mention}\n**Grund:** {reason}\n**Server:** {interaction.guild.name}",
            color=0xff0000
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_footer(text=EMBED_FOOTER)
        embed.timestamp = discord.utils.utcnow()
        
        for member in interaction.channel.members:
            guild_member = guild.get_member(member.id)
            has_required_role = any(role.name in [TEAM_ROLE, SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in guild_member.roles)

            if not has_required_role:
                logger.info(f"Removing user {guild_member} from ticket channel {interaction.channel}")
                await interaction.channel.remove_user(guild_member)
                await asyncio.sleep(0.5)
                
                if SEND_TICKET_FEEDBACK is True:
                    logger.info(f"Sending closed ticket embed to {guild_member}")
                    await guild_member.send(embed=embed)
            else:
                logger.debug(f"User {guild_member} has required role, not removing from ticket channel")
            
        if not interaction.channel.name.startswith("[CLOSED] "):
            try:
                logger.info(f"Renaming channel {interaction.channel} to closed")
                await interaction.channel.edit(name=f"[CLOSED] {interaction.channel.name}")
                await asyncio.sleep(0.5)
                
                await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})* aus folgendem Grund: ```{reason}```")
            except discord.HTTPException as e:
                logger.error(f"HTTPException while closing ticket: {e}")
                if e.status == 429:
                    await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 1)
                    await interaction.channel.edit(name=f"[CLOSED] {interaction.channel.name}")
                    await asyncio.sleep(0.5)
                    await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})* aus folgendem Grund: ```{reason}```")
                else:
                    await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})* aus folgendem Grund: ```{reason}```")

    async def no_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} cancelled closing ticket with reason in {interaction.channel}")
        await interaction.message.delete()

# The close view, if you close a ticket
class CloseThreadView(View):
    def __init__(self, bot, ticketcog: "TicketCog"):
        super().__init__(timeout=None)
        self.ticketcog = ticketcog
        self.bot = bot
        
        archive_button = Button(emoji=ARCHIVE_EMOJI, style=SECONDARY, label="Archivieren", custom_id="archive_ticket_button")
        archive_button.callback = self.archive_button
        
        delete_button = Button(emoji=TRASHCAN_EMOJI, style=DANGER, label="Löschen", custom_id="delete_ticket_button")
        delete_button.callback = self.delete_button
        
        trans_button = Button(emoji=TRANSCRIPT_EMOJI, style=SECONDARY, label="Transkribieren", custom_id="transcript_ticket_button")
        trans_button.callback = self.trans_button
        
        reopen_button = Button(emoji=REOPEN_EMOJI, style=GREEN, label="Neu eröffnen", custom_id="reopen_ticket_button")
        reopen_button.callback = self.reopen_button
        
  
        self.add_item(delete_button)
        self.add_item(reopen_button)
        self.add_item(trans_button)
        self.add_item(archive_button)
        
    async def archive_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked archive_button in {interaction.channel}")
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            logger.warning(f"{interaction.user} tried to archive ticket without permission in {interaction.channel}")
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        
        await interaction.response.send_modal(ThreadModalRename())

    async def delete_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked delete_button in {interaction.channel}")
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            logger.warning(f"{interaction.user} tried to delete ticket without permission in {interaction.channel}")
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return

        await interaction.response.send_message(view=DeleteConfirmView(ticketcog=self.ticketcog), content=f"> {interaction.user.mention} Möchtest du dieses Ticket wirklich löschen?")
        
    async def trans_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked trans_button in {interaction.channel}")
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            logger.warning(f"{interaction.user} tried to transcribe ticket without permission in {interaction.channel}")
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        
        await interaction.response.send_modal(TransDesc(bot=self.bot))

    async def reopen_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} clicked reopen_button in {interaction.channel}")
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            logger.warning(f"{interaction.user} tried to reopen ticket without permission in {interaction.channel}")
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        if TICKET_CREATOR_ID is None:
            logger.warning(f"Ticket creator ID not found for channel {interaction.channel.id} on reopen")
            await interaction.response.send_message(NO_MEMBER, ephemeral=True)
            return

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
            logger.warning(f"{interaction.user} tried to reopen ticket without support role in {interaction.channel}")
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return

        if isinstance(interaction.channel, discord.Thread):
            async for message in interaction.channel.history(limit=None):
                if message.content.startswith("> ") and message.author == interaction.client.user:
                    try:
                        await message.delete()
                        logger.debug(f"Deleted setup message in {interaction.channel}")
                    except Exception as e:
                        logger.error(f"Error deleting setup message: {e}")
                    
            current_channel_name = interaction.channel.name
            if current_channel_name.startswith("[CLOSED] "):
                current_channel_name = current_channel_name[9:]
                
            await interaction.channel.edit(name=current_channel_name)
            await interaction.response.send_message("> Alle setup Nachrichten im Ticket wurden gelöscht.", ephemeral=True, delete_after=20)
            
            await asyncio.sleep(0.5)
            await interaction.channel.add_user(TICKET_CREATOR)
            await interaction.channel.send(f"> {TICKET_CREATOR.mention} Das Ticket wurde neu eröffnet.")
     
# The view, where you can deside between "yes" and "no"
class CloseConfirmView(View):
    def __init__(self, bot, ticketcog: "TicketCog", timeout = 180):
        super().__init__(timeout=timeout)
        self.ticketcog = ticketcog
        self.bot = bot
        
        yes_button = Button(emoji=CHECK, style=DANGER, label="Ja, schließen")
        yes_button.callback = self.yes_button
        
        no_button = Button(emoji=UNCHECK, style=SECONDARY, label="Nein")
        no_button.callback = self.no_button
        
        self.add_item(yes_button)
        self.add_item(no_button)
        
    async def yes_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} confirmed closing ticket without reason in {interaction.channel}")
        await interaction.message.delete()
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        if TICKET_CREATOR_ID is None:
            logger.warning(f"Ticket creator ID not found for channel {interaction.channel.id}")
            await interaction.response.send_message("Error, member wurde nicht gefunden.", ephemeral=True)
            return

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if TICKET_CREATOR is None:
            logger.warning(f"Ticket creator not found in guild for ID {TICKET_CREATOR_ID}")
            await interaction.response.send_message("Fehler: Der Member konnte nicht gefunden werden.", ephemeral=True)
            return
        
        for member in interaction.channel.members:
            guild_member = guild.get_member(member.id)
            has_required_role = any(role.name in [TEAM_ROLE, SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in guild_member.roles)

            if not has_required_role:
                logger.info(f"Removing user {guild_member} from ticket channel {interaction.channel}")
                await interaction.channel.remove_user(guild_member)
                await asyncio.sleep(0.5)
                
                embed = discord.Embed(
                    title=f"{LOCK_EMOJI} Ticket geschlossen - {interaction.channel.name}",
                    description=f"**Geschlossen von:** {interaction.user.mention}\n**Grund:** Keine Angabe\n**Server:** {interaction.guild.name}",
                    color=0xff0000
                )
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                embed.set_footer(text=EMBED_FOOTER)
                embed.timestamp = discord.utils.utcnow()
                
                if SEND_TICKET_FEEDBACK is True:
                    logger.info(f"Sending closed ticket embed to {guild_member}")
                    await guild_member.send(embed=embed)
            else:
                logger.debug(f"User {guild_member} has required role, not removing from ticket channel")
            
        if not interaction.channel.name.startswith("[CLOSED] "):
            try:
                logger.info(f"Renaming channel {interaction.channel} to closed")
                await interaction.channel.edit(name=f"[CLOSED] {interaction.channel.name}")
                await asyncio.sleep(0.5)
                
                await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})*.")
            except discord.HTTPException as e:
                logger.error(f"HTTPException while closing ticket: {e}")
                if e.status == 429:
                    await asyncio.sleep(e.retry_after if hasattr(e, 'retry_after') else 1)
                    await interaction.channel.edit(name=f"[CLOSED] {interaction.channel.name}")
                    await asyncio.sleep(0.5)
                    await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})*.")
                else:
                    await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})*.")
    
    async def no_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} cancelled closing ticket without reason in {interaction.channel}")
        await interaction.message.delete()

# The ticket-setup view
class TicketSetupView(View):
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown(ticketcog))

# The ticket-setup view dropdown
class TicketDropdown(discord.ui.Select):
    options = [
        discord.SelectOption(label=LABEL_DISCORD, emoji="💬", value="discord"),
        discord.SelectOption(label=LABEL_MINECRAFT, emoji="⛏️", value="minecraft"),
        discord.SelectOption(label=LABEL_BEREICH, emoji="🚧", value="bereich"),
        discord.SelectOption(label=LABEL_PARZELLE, emoji="🛠️", value="parzelle"),
        discord.SelectOption(label=LABEL_ENTBANNUNG, emoji="📝", value="entbannung"),
        discord.SelectOption(label=LABEL_SONSTIGES, emoji="❓", value="sonstiges")
    ]
    
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(placeholder=PLACEHOLDER_TEXT, options=self.options, custom_id="ticket_dropdown")
        self.ticketcog = ticketcog
        
    async def callback(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} selected '{self.values[0]}' in TicketDropdown in {interaction.channel}")
        if self.values[0] == "discord":
            fields = {
                "Title": TITLE_DISCORD,
                "message": MESSAGE_GENERAL
            }
            
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "minecraft":
            fields = {
                "Title": TITLE_MINECRAFT,
                "message": MESSAGE_GENERAL
            }
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "entbannung":       
            fields = {
                "Title": TITLE_ENTBANNUNG,
                "message": MESSAGE_ENTBANNUNG
            }
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "bereich":
            await interaction.response.send_modal(bereichModal(ticketcog=self.ticketcog))
            
        elif self.values[0] == "parzelle":
            await interaction.response.send_modal(parzelleModal(ticketcog=self.ticketcog))
            
        elif self.values[0] == "sonstiges":
            fields = {
                "Title": TITLE_SONSTIGES,
                "message": MESSAGE_GENERAL
            }
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)

# The delete confirmation view
class DeleteConfirmView(View):
    def __init__(self, *, timeout = 180, ticketcog: "TicketCog"):
        super().__init__(timeout=timeout)
        self.ticketcog = ticketcog
        
        yes_button = Button(emoji=CHECK, style=DANGER, label="Ja, löschen")
        yes_button.callback = self.yes_button
        
        no_button = Button(emoji=UNCHECK, style=SECONDARY, label="Nein")
        no_button.callback = self.no_button
        
        self.add_item(yes_button)
        self.add_item(no_button)
        
    async def yes_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} confirmed deleting ticket in {interaction.channel}")
        await interaction.channel.edit(name="[DELETING]")
        delete_ticket_creator(interaction.channel.id)
        await interaction.channel.delete()
        
    async def no_button(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user} cancelled deleting ticket in {interaction.channel}")
        await interaction.message.delete()
