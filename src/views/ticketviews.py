# ruff: noqa: F403 F405
import discord
from discord.ui import View, Button
from constants import *
from modals.ticketmodals import *
from typing import TYPE_CHECKING
from util.ticket_creator import get_ticket_creator, delete_ticket_creator

if TYPE_CHECKING:
    from cogs.tickets import TicketCog
    
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
        await interaction.response.send_message(view=CloseConfirmView(ticketcog=self.ticketcog, bot=self.bot), content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket schließen möchtest?")
    
    async def close_button_with_reason(self, interaction: discord.Interaction):
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
        await interaction.message.delete()
        global DELETE_USER
        DELETE_USER = interaction.user
        reason = self.reason
        
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        
        if TICKET_CREATOR_ID is None:
            pass

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if TICKET_CREATOR is None:
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
                await interaction.channel.remove_user(guild_member)
                
                if SEND_TICKET_FEEDBACK is True:
                    await guild_member.send(embed=embed)
            else:
                pass
            
        await interaction.channel.send(view=CloseThreadView(ticketcog=self.ticketcog, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})* aus folgendem Grund: ```{reason}```")

    async def no_button(self, interaction: discord.Interaction):
        await interaction.message.delete()

# The close view, if you close a ticket
class CloseThreadView(View):
    def __init__(self, *, timeout = None, ticketcog: "TicketCog", bot):
        super().__init__(timeout=timeout)
        self.ticketcog = ticketcog
        self.bot = bot
        
        archive_button = Button(emoji=ARCHIVE_EMOJI, style=SECONDARY, label="Archivieren")
        archive_button.callback = self.archive_button
        
        delete_button = Button(emoji=TRASHCAN_EMOJI, style=DANGER, label="Löschen")
        delete_button.callback = self.delete_button
        
        trans_button = Button(emoji=TRANSCRIPT_EMOJI, style=SECONDARY, label="Transkribieren")
        trans_button.callback = self.trans_button
        
        reopen_button = Button(emoji=REOPEN_EMOJI, style=GREEN, label="Neu eröffnen")
        reopen_button.callback = self.reopen_button
        
  
        self.add_item(delete_button)
        self.add_item(reopen_button)
        self.add_item(trans_button)
        self.add_item(archive_button)
        
    async def archive_button(self, interaction: discord.Interaction):
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        
        await interaction.response.send_modal(ThreadModalRename())

    async def delete_button(self, interaction: discord.Interaction):
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return

        await interaction.response.send_message(view=DeleteConfirmView(ticketcog=self.ticketcog), content=f"> {interaction.user.mention} Möchtest du dieses Ticket wirklich löschen?")
        
    async def trans_button(self, interaction: discord.Interaction):
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        
        await interaction.response.send_modal(TransDesc(bot=self.bot))

    async def reopen_button(self, interaction: discord.Interaction):
        if not (
            interaction.user.guild_permissions.administrator or
            any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles)
        ):
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        if TICKET_CREATOR_ID is None:
            await interaction.response.send_message(NO_MEMBER, ephemeral=True)
            return

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True, delete_after=20)
            return

        if isinstance(interaction.channel, discord.Thread):
            async for message in interaction.channel.history(limit=None):
                if message.content.startswith("> ") and message.author == interaction.client.user:
                    try:
                        await message.delete()
                    except Exception:
                        pass
            await interaction.response.send_message("> Alle setup Nachrichten im Ticket wurden gelöscht.", ephemeral=True, delete_after=20)
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
        await interaction.message.delete()
        guild = interaction.guild
        TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
        if TICKET_CREATOR_ID is None:
            await interaction.response.send_message("Error, member wurde nicht gefunden.", ephemeral=True)
            return

        TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)

        if TICKET_CREATOR is None:
            await interaction.response.send_message("Fehler: Der Member konnte nicht gefunden werden.", ephemeral=True)
            return
        
        for member in interaction.channel.members:
            guild_member = guild.get_member(member.id)
            has_required_role = any(role.name in [TEAM_ROLE, SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in guild_member.roles)

            if not has_required_role:
                await interaction.channel.remove_user(guild_member)
                
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
                    await guild_member.send(embed=embed)
            else:
                pass

        await interaction.channel.send(view=CloseThreadView(ticketcog=self, bot=self.bot), content=f"> Ticket geschlossen von **{interaction.user.display_name}** *({interaction.user.name})*")

    async def no_button(self, interaction: discord.Interaction):
        await interaction.message.delete()

# The ticket-setup view
class TicketSetupView(View):
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown(ticketcog))

# The ticket-setup view dropdown
class TicketDropdown(discord.ui.Select):
    options = [
        discord.SelectOption(label="Allgemein: Discord", emoji="💬", value="discord"),
        discord.SelectOption(label="Allgemein: Minecraft", emoji="⛏️", value="minecraft"),
        discord.SelectOption(label="Survival: Bereich sichern", emoji="🚧", value="bereich"),
        discord.SelectOption(label="Kreativ: Parzelle übertragen", emoji="🛠️", value="parzelle"),
        discord.SelectOption(label="Entbannungsantrag", emoji="📝", value="entbannung"),
        discord.SelectOption(label="Sonstiges", emoji="❓", value="sonstiges")
    ]
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(placeholder="Wähle eine Option", options=self.options, custom_id="ticket_dropdown")
        self.ticketcog = ticketcog
        
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "discord":
            fields = {
                "Title": "Allgemeines Discord",
                "message": "Wie können wir dir helfen? Was ist dein Anliegen?"
            }
            
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "minecraft":
            fields = {
                "Title": "Allgemeines Minecraft",
                "message": "Wie können wir dir helfen? Was ist dein Anliegen?"
            }
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "entbannung":       
            fields = {
                "Title": "Entbannungsantrag",
                "message": "Schreibe nun dein Entbannungs-Antrag. Wir werden intern darüber abstimmen und uns bei dir hier melden."
            }
            await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)
            
        elif self.values[0] == "bereich":
            await interaction.response.send_modal(bereichModal(ticketcog=self.ticketcog))
            
        elif self.values[0] == "parzelle":
            await interaction.response.send_modal(parzelleModal(ticketcog=self.ticketcog))
            
        elif self.values[0] == "sonstiges":
            fields = {
                "Title": "Sonstiges",
                "message": "Wie können wir dir helfen? Was ist dein Anliegen?"
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
        delete_ticket_creator(interaction.channel.id)
        await interaction.channel.delete()
        
    async def no_button(self, interaction: discord.Interaction):
        await interaction.message.delete()