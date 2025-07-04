# ruff: noqa: F403 F405
from discord.ext import commands
from constants import *
from discord import *
from discord.ui import View, Button
import random

class GuessNumberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counting_channels = {}
        self.last_user = {}
        self.bot_number = None
        self.difficulty = None
        self.numb_of_guesses = 0
        self.awaiting_custom_input = False
        
    async def game_start(self, difficulty, custom_value):
        if difficulty == "easy":
            self.bot_number = random.randint(1, 100)
            self.difficulty = "Easy"
        elif difficulty == "normal":
            self.bot_number = random.randint(1, 1000)
            self.difficulty = "Normal"
        elif difficulty == "hard":
            self.bot_number = random.randint(1, 10000)
            self.difficulty = "Hard"
        elif difficulty == "custom":
            self.bot_number = random.randint(1, custom_value)
            self.difficulty = f"Custom range of 1 - {custom_value}"
        
        print(self.bot_number)

    async def check_number(self, number, channel, message: discord.Message):
        bot_number = self.bot_number
        if bot_number is None:
            if self.awaiting_custom_input:
                await message.delete(delay=2)
                return
            await message.delete(delay=2)
            await channel.send("Game not started yet. Type 'start' to begin.", delete_after=4)
            return
        if number == bot_number:
            await channel.send(f"{message.author.mention} Congratulations! You guessed the number! 🎉")
            self.bot_number = None
            
        else:
            self.numb_of_guesses += 1
            diff = abs(number - bot_number)
            if number < bot_number:
                await message.add_reaction("⬆️")
            else:
                await message.add_reaction("⬇️")
                if diff == 0:
                    await message.add_reaction("🎉")
                elif diff == 1:
                    await message.add_reaction("🔥")
                elif diff <= 3:
                    await message.add_reaction("🌋")
                elif diff <= 10:
                    await message.add_reaction("🌡️")
                elif diff <= 30:
                    await message.add_reaction("❄️")
                elif diff <= 100:
                    await message.add_reaction("🧊")
                elif diff <= 500:
                    await message.add_reaction("🥶")
                else:
                    await message.add_reaction("💀")
                
    async def clear_game(self):
        self.bot_number = None
        self.difficulty = None
        self.numb_of_guesses = 0

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.name != "guess-number":
            return

        channel = message.channel

        async def easy_callback(interaction):
            await interaction.response.send_message(f"Started on `Easy` difficulty! Good Luck! {CHECK}")
            await self.game_start(difficulty="easy", custom_value=None)

        async def normal_callback(interaction):
            await interaction.response.send_message(f"Started on `Normal` difficulty! Good Luck! {CHECK}")
            await self.game_start(difficulty="normal", custom_value=None)

        async def hard_callback(interaction):
            await interaction.response.send_message(f"Started on `Hard` difficulty! Good Lachs, you will need it! {CHECK}")
            await self.game_start(difficulty="hard", custom_value=None)

        async def custom_callback(interaction: discord.Interaction):
            self.awaiting_custom_input = True
            await interaction.response.send_message(f"Please enter your custom max. number", ephemeral=True, delete_after=15)
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            try:
                custom_msg = await self.bot.wait_for('message', check=check, timeout=30)
                if custom_msg.content.strip() in [":q", "quit"]:
                    await custom_msg.delete(delay=2)
                    await interaction.followup.send("Custom difficulty cancelled.", ephemeral=True, delete_after=5)
                    self.awaiting_custom_input = False
                    return
                custom_input = int(custom_msg.content.strip())
                await custom_msg.delete(delay=2)
                await custom_callback_end(interaction=interaction, custom_input=custom_input)
            except ValueError:
                await interaction.followup.send(f'Please enter a valid number. Or quit with "quit" / ":q".', ephemeral=True, delete_after=10)
            except Exception as e:
                await interaction.followup.send("Timed out or error occurred. Please try again.", ephemeral=True, delete_after=10)
            finally:
                self.awaiting_custom_input = False

        async def custom_callback_end(interaction, custom_input):
            await interaction.followup.send(f"Started on `custom` difficulty! With a range of 1 - {custom_input}! {CHECK}")
            await self.game_start(difficulty="custom", custom_value=custom_input)

        try:
            number = int(message.content.strip())
            await self.check_number(number, channel, message=message)
        except ValueError:
            if message.content.strip() == "start" or message.content.strip() == ":s":
                await self.clear_game()
                message_author = message.author
                await message.delete()
                await channel.send(f"Starting {LOADING_EMOJI}")

                view = View()

                easy_btn = Button(label="Easy", style=GREEN, emoji="👽")
                easy_btn.callback = easy_callback

                normal_btn = Button(label="Normal", style=SECONDARY, emoji="😀")
                normal_btn.callback = normal_callback

                hard_btn = Button(label="Hard", style=DANGER, emoji="💀")
                hard_btn.callback = hard_callback
                
                custom_btn = Button(label="Custom", style=discord.ButtonStyle.blurple, emoji="❓")
                custom_btn.callback = custom_callback

                view.add_item(easy_btn)
                view.add_item(normal_btn)
                view.add_item(hard_btn)
                view.add_item(custom_btn)
                
                await channel.last_message.delete()
                await channel.send(f"{message_author.mention} Please select a difficulty out of those.", view=view)
            elif message.content.strip() == "difficulty":
                await channel.send(f"{message.author.mention} Current difficulty: `{self.difficulty}`", delete_after=3)
            elif message.content.strip() == "surrender":
                if self.difficulty:
                    await channel.send(f"{message.author.mention} You surrendered! With `{self.numb_of_guesses}` guesses in `{self.difficulty}` difficulty. The number was: `{self.bot_number}`!")
                    await self.clear_game()
                else:
                    await message.delete(delay=3)
                    await channel.send("Game not started yet. Type 'start' to begin.", delete_after=4)
            else:
                await message.delete(delay=2)
                await channel.send(f"{message.author.mention} Please only use numbers to guess.", delete_after=3)
                return