# ruff: noqa: F403 F405
import discord
from jinja2 import Environment, FileSystemLoader
import io
import markdown
from constants import *
from modals.ticketmodals import *
from util.ticket_creator import get_ticket_creator, get_ticket_users

async def trans_ticket(interaction: discord.Interaction, summary: str, bot):
    guild = interaction.guild
    TICKET_CREATOR_ID = get_ticket_creator(interaction.channel.id) 
    if TICKET_CREATOR_ID is None:
        await interaction.response.send_message("Error, member wurde nicht gefunden.", ephemeral=True)
        return

    TICKET_CREATOR = guild.get_member(TICKET_CREATOR_ID)
    if not any(role.name in [SUPPORT_ROLE_NAME, SUPPORTHILFE_ROLE_NAME] for role in interaction.user.roles):
        await interaction.response.send_message("Du hast keine Berechtigung, um diese Aktion auszuführen.", ephemeral=True, delete_after=10)
        return

    await interaction.response.send_message(f"> {TRANSCRIPT_EMOJI} Erstelle das Transkript {LOADING_EMOJI}")

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
        template = env.get_template('src/transcript_template.html')
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
    await interaction.edit_original_response(content=f"> {TRANSCRIPT_EMOJI} Transkript in {trans_channel.mention} erstellt!")

    print(f"DEBUG     Größe des Buffers (trans_channel): {buffer_trans.getbuffer().nbytes} Bytes")
    transcript_file_trans = discord.File(buffer_trans, filename=f"transcript von {channel.name}.html")
    
    message_count = 0
    async for _ in channel.history(limit=None):
        if not _.author.bot:
            message_count += 1

    member_count = 0
    
    members = channel.members
    for member in members:
        member_count += 1
        
    embed = discord.Embed(
        title=f"{TRANSCRIPT_EMOJI} Transkript - {channel.name}",
        description="**Stats**",
        color=0x00ff00
    )

    users = await get_ticket_users(interaction.channel)
    user_list_str = "\n".join([f"* {user.name}" for user in users])
    embed.set_author(name=TICKET_CREATOR if TICKET_CREATOR else None, icon_url=TICKET_CREATOR.avatar.url if TICKET_CREATOR else None)
    embed.add_field(name="Beschreibung", value=summary, inline=False)
    embed.add_field(name="Nachrichten", value=message_count, inline=True)
    embed.add_field(name="Erstellt von", value=TICKET_CREATOR if TICKET_CREATOR else None, inline=True)
    embed.add_field(name=f"Benutzer (Insgesamt: {member_count})", value=user_list_str, inline=False)
    embed.set_thumbnail(url=interaction.user.avatar.url)
    embed.set_footer(text="JabUB.css | by www.ninoio.gay")
    embed.timestamp = discord.utils.utcnow()
    
    await trans_channel.send(embed=embed, file=transcript_file_trans)