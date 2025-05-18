# ruff: noqa: F403 F405
import discord
from discord.ui import Modal, TextInput
from constants import *
from util.transcript import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.tickets import TicketCog

# Rename the ticket, before it gets archived
class ThreadModalRename(Modal, title='Archiviere das Ticket'):
    name_TextInput = TextInput(label="Soll das Ticket einen anderen Namen haben?", placeholder="Der neue Name des Tickets", max_length=30, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name_TextInput.value
        try:
            await interaction.response.defer()
            await interaction.channel.edit(name=new_name, archived=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Fehler beim Archivieren des Tickets: {e}", ephemeral=True)

# Get a summary of the ticket after transcripting it
class TransDesc(Modal):
    name_TextInput = TextInput(label="Beschreibung des Tickets", placeholder="", required=False)
    
    def __init__(self, bot):
        super().__init__(title="Beschreibung des Tickets")
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        summary = self.name_TextInput.value
        
        try:
            await trans_ticket(interaction=interaction, summary=summary, bot=self.bot)
            
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Fehler beim ändern der Beschreibung: {e}", ephemeral=True)
            pass

# Get a reason to close the ticket
class closeThreadReasonModal(Modal):
    reason_TextInput = TextInput(label="Grund", placeholder="Gib den Grund für das Schließen des Tickets an.", style=discord.TextStyle.short, max_length=200)
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(title='Ticket schließen')
        self.ticketcog = ticketcog
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        reason = self.reason_TextInput.value
        await self.ticketcog.close_thread_with_reason(interaction=interaction, reason=reason)

# Area saving modal, to get the world and coordinates
class bereichModal(Modal):
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(title='Bereich Sichern')
        self.ticketcog = ticketcog
        self.welt = discord.ui.TextInput(label="Welt", placeholder="Die Welt, e.g. Overworld, Nether, End", style=discord.TextStyle.short, max_length=60)
        self.koordinaten = discord.ui.TextInput(label="Koordinaten", placeholder="120 60 120 bis 200 70 200")

        self.add_item(self.welt)
        self.add_item(self.koordinaten)
        
    async def on_submit(self, interaction: discord.Interaction):
        fields = {
            "Title": "Bereich Sichern",
            "Koordinaten": self.koordinaten.value,
            "Welt": self.welt.value,
            "message": "Es wird dir so schnell wie möglich geholfen!"
        }
        await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)

# get the coordinates of the plot
class parzelleModal(Modal):
    def __init__(self, ticketcog: "TicketCog"):
        super().__init__(title='Parzelle übertragen')
        self.ticketcog = ticketcog
        
        self.ingame_name = discord.ui.TextInput(label="Ingame Name", placeholder="Der Name deines Minecraft Accounts", style=discord.TextStyle.short, max_length=60)
        self.canstein_name = discord.ui.TextInput(label="Canstein Name", placeholder="Der Name des benutzten Canstein Accounts", style=discord.TextStyle.short, max_length=60, required=False)
        self.add_item(self.ingame_name)
        self.add_item(self.canstein_name)

    async def on_submit(self, interaction: discord.Interaction):
        fields = {
            "Title": "Parzelle übertragen",
            "Ingame Name": self.ingame_name.value,
            "Canstein Name": self.canstein_name.value,
            "message": "Es wird dir so schnell wie möglich geholfen!"
        }
        await self.ticketcog.create_ticket_thread(interaction=interaction, fields=fields)


