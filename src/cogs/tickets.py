# ruff: noqa: F403 F405
import discord
from discord.ext import commands
from discord import app_commands
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
from util.ticket_creator import *
import traceback

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="tickets", description="Setup tickets in this channel!")
    async def setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
            return

        await interaction.response.send_message("Embed wurde gesendet", ephemeral=True)
        embed = discord.Embed(
            title="🎫 Support",
            description="Hast du Fragen oder möchtest du etwas anmerken? Öffne jetzt ein **Support-Ticket**, um Kontakt mit unserem Team aufzunehmen. Es wird so schnell es geht jemand antworten. Du brauchst niemanden vom Team anzupingen.",
            color=0x00ff00
        )
        embed.set_author(name="Tickets", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
        
        embed.add_field(name="Was als nächstes?", value='Wähle eine **Kategorie** aus dem **Drop-Down Menü** aus, um weitere Informationen zu erhalten und um dein **Ticket anzupassen**.')
        embed.set_footer(text=EMBED_FOOTER)

        await interaction.channel.send(embed=embed, view=TicketSetupView(interaction))
        
    @app_commands.command(name="close", description="Lets you close the ticket")
    async def close(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Dieser Befehl kann nur in einem Ticket-Thread verwendet werden.", ephemeral=True)
            return

        if interaction.channel.parent_id != int(TICKET_CHANNEL_ID):
            await interaction.response.send_message("Dieser Befehl kann nur in einem Ticket-Thread verwendet werden.", ephemeral=True)
            return
        
        cancel_btn = Button(emoji=UNCHECK, label="Abbrechen", style=SECONDARY)
        cancel_btn.callback = self.cancel_btn_callback
            
        view = PersistentCloseView(ticketcog=self, bot=self.bot)
        view.add_item(cancel_btn)
        
        await interaction.response.send_message(view=view, content="") 
        
    async def cancel_btn_callback(self, interaction):
        await interaction.message.delete()
    
    async def close_thread_confirmation(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=CloseConfirmView(ticketcog=self), content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket schließen möchtest?", ephemeral=False)

    async def close_thread_with_reason(self, interaction: discord.Interaction, reason: str):
        await interaction.followup.send(view=CloseReasonConfirmView(ticketcog=self, bot=self.bot, reason=reason), content=f"> {interaction.user.mention} Bist du dir sicher, dass du das Ticket mit dem Grund: ```{reason}``` schließen möchtest?", ephemeral=False)

    async def create_ticket_thread(self, interaction: discord.Interaction, fields: dict):
        global TICKET_CREATOR
        guild = interaction.guild
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        supporthilfe_role = discord.utils.get(guild.roles, name=SUPPORTHILFE_ROLE_NAME)

        try:
            title = fields.get("Title")
            thread = await interaction.channel.create_thread(name=title + f" von {interaction.user.display_name}", type=discord.ChannelType.private_thread)
            
            save_ticket_creator(thread.id, interaction.user.id)
            TICKET_CREATOR = interaction.user

            await thread.add_user(interaction.user)
            await thread.edit(invitable=False)

            embed = discord.Embed(
                title="🎫 Ticket Übersicht",
                description=f'Schließe das Ticket mit {LOCK_EMOJI} und bestätige mit **"Ja"**, oder brich mit **"Nein"** ab.\n Um das Ticket mit einem **Grund** zuschließen, drücke auf {LOCK_W_REASON_EMOJI} und gib deinen Grund an.',
                color=0x00ff00
            )
            embed.set_footer(text=EMBED_FOOTER)
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

            for name, value in fields.items():
                if name not in ["Title", "Rolle", "message"] and value.strip():
                    embed.add_field(name=name, value=value, inline=False)
            
            message = fields.get("message", "Es wird dir so schnell wie möglich geholfen!")

            await thread.send(
                embed=embed,
                view=PersistentCloseView(bot=self.bot, ticketcog=self),
                content=f"{support_role.mention if support_role else ''} {supporthilfe_role.mention if supporthilfe_role else ''} {message}"
            )
            await interaction.response.send_message(f"Ticket erstellt in {thread.mention}!", ephemeral=True, delete_after=20)

        except Exception as e:
            await interaction.response.send_message("Fehler beim Erstellen des Tickets.", ephemeral=True, delete_after=10)
            print(f"Fehler beim Erstellen des Tickets: {e}")
            print(traceback.format_exc())

    # Update a ticket after a timeout (30 days by default)
    @commands.Cog.listener(name="THREAD_UPDATE")
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        guild = after.guild
        if not before.archived and after.archived:
            for member in after.members:
                guild_member = guild.get_member(member.id)
                has_required_role = any(role.name in [TEAM_ROLE, SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in guild_member.roles)

                if not has_required_role:
                    await after.send(view=None, content="> Ticket geschlossen aus folgendem Grund: ```Time-Out nach 30 Tagen.```")
                    await after.remove_user(guild_member)
                else:
                    pass

    async def cog_load(self):
        self.bot.tree.add_command(self.setup, guild=discord.Object(id=SYNC_SERVER))
        self.bot.tree.add_command(self.close, guild=discord.Object(id=SYNC_SERVER))
