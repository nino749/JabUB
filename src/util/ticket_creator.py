# ruff: noqa: F403 F405
import discord
from constants import *
from views.ticketviews import *
from modals.ticketmodals import *
import os
import json

def load_ticket_creator_data() -> dict:
    if not os.path.exists(TICKET_CREATOR_FILE):
        return {}
    try:
        with open(TICKET_CREATOR_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_ticket_creator_data(data: dict):
    with open(TICKET_CREATOR_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_ticket_creator(guild_id: int) -> int | None:
    data = load_ticket_creator_data()
    return data.get(str(guild_id))

def save_ticket_creator(thread_id: int, user_id: int):
    data = load_ticket_creator_data()
    data[str(thread_id)] = user_id
    save_ticket_creator_data(data)

def delete_ticket_creator(thread_id: int):
    data = load_ticket_creator_data()
    if str(thread_id) in data:
        del data[str(thread_id)]
        save_ticket_creator_data(data)

async def get_ticket_users(thread: discord.Thread):
    user_ids = set()
    users = []
    
    async for message in thread.history(limit=None):
        if message.author.id not in user_ids:
            user_ids.add(message.author.id)
            users.append(message.author)

    return users