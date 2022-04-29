# -*- coding: utf-8 -*-

# Discord - HangMan
# A "cog" to play HangMan for Discord bots which is written in discord.py

# Author: Cagatay URESIN
# Mail: cagatayuresin@gmail.com
# GitHub: https://github.com/cagatayuresin/discord-hangman
# https://cagatayuresin.com/discord-hangman

from asyncio import futures, sleep
from discord.ext import commands
import json

# ---------- Command configuration ----------
command_name = "hangman"
command_aliases = [
    "hang"
]
command_usage = """
Hangman! Just type any letter and send, 'hint' to take a hint, 'cancel' to finish it.
"""
command_brief = """
A little Hangman Game.
"""
command_help = """
After the command is given, the game starts. In the channel where you open the game, 
the bot expects you to guess. To guess, you must send a letter to the same channel. Until the game is over, 
the bot takes everything you type as a guess and deletes it. The game is over when all your lives are gone. When you 
win the game it's over. When you guess 'cancel' it is game over. Guess 'hint' when a clue is needed for the question. 

For more help: 
cagatayuresin@gmail.com
https://github.com/cagatayuresin
"""
# -------------------------------------------

# The word list
# You can pull a word from a database or an API
# TODO: I'll make a little dataset of random question examples to test
# Test question
the_question = {
    'name': 'The Godfather',
    'category': 'Movie',
    'hints': [
        'This movie has a very good IMDb point.',
        'Al Pacino plays.',
        'A 1972 movie.'
    ]
}

# ---------- Game Configuration ----------
with open("hangman_conf.json", mode="r", encoding="utf-8") as f:
    cfg = json.loads(f.read())

censor_char = cfg['censor_char']
guess_time_out = cfg['guess_time_out']
point_config = cfg['point_config']

# The man
#  ______
#  |    |
#  |    O
#  |   /|\
#  |   / \
# _|
the_man = [
        " ______\n |    |\n |    O     ♥ {}\n |   /|\\    # {}\n |   / \\    p {}\n_|",
        " ______\n |    |\n |    O     ♥ {}\n |   /|\\    # {}\n |   /      p {}\n_|",
        " ______\n |    |\n |    O     ♥ {}\n |   /|\\    # {}\n |          p {}\n_|",
        " ______\n |    |\n |    O     ♥ {}\n |   /|     # {}\n |          p {}\n_|",
        " ______\n |    |\n |    O     ♥ {}\n |    |     # {}\n |          p {}\n_|",
        " ______\n |    |\n |    O     ♥ {}\n |          # {}\n |          p {}\n_|",
        " ______\n |    |\n |          ♥ {}\n |          # {}\n |          p {}\n_|",
]

# The question format to keep update the game
game_panel = "```" \
             "{}\n" \
             "{}\n" \
             "{}\n" \
             "{} # {}\n" \
             "{}\n" \
             "{}\n" \
             "```"
# ----------------------------------------


class Question:
    name: str
    answer: str
    question: str
    length: int
    category: str
    hints: list
    hint_count: int
    appears: list
    unknown_letters: list
    point_cfg: dict
    point: int
    hp: int

    def __init__(self, question: dict):
        self.name = question['name']
        self.answer = self.name.lower()
        self.question = self.censor(self.name)
        self.length = self.name.count(censor_char)
        self.category = question['category'].lower()
        self.hints = list(question['hints'])
        self.hint_count = len(self.hints)
        self.appears = []
        self.unknown_letters = list(set(self.answer))
        self.point_cfg = point_config
        self.point = 0
        self.hp = self.point_cfg['HP']

    @staticmethod
    def censor(uncensored_words: str, the_censor_char=censor_char) -> str:
        """
        Censors the question with the censor character

        censor("For Exam-ple 4", "#") -> "### ####-### 4"
        """
        censored_words = uncensored_words.lower()
        censored_words = [char for char in censored_words]

        for i in range(len(censored_words)):
            if censored_words[i] in cfg['charset']:
                censored_words[i] = the_censor_char

        return ''.join(censored_words)

    def give_hint(self) -> str:
        if len(self.hints) == 0:
            return "there is no hint to give!"
        else:
            self.point += self.point_cfg['hint_penalty']
            return self.hints.pop(0)

    def ask_letter(self, letter: str) -> str:
        letter = letter.lower()

        if len(letter) > 1 and letter != self.answer:
            self.hp -= 1
            self.point += self.point_cfg['one_shot_penalty']
            return "one shot penalty!"
        elif len(letter) > 1 and letter == self.answer:
            self.point += self.point_cfg['one_shot_multiplier'] * len(self.unknown_letters)
            self.question = letter
            self.unknown_letters = []
            return "one shot success! - game over!"
        elif letter not in cfg['charset']:
            self.hp -= 1
            self.point += self.point_cfg['out_of_charset_guess']
            return "out of charset!"
        elif letter in self.appears:
            self.hp -= 1
            self.point += self.point_cfg['known_letter_penalty']
            return "known letter penalty!"
        elif letter in self.answer:
            self.point += self.point_cfg['letter_point']
            self.appears.append(letter)
            question_list = [char for char in self.question]
            answer_list = [char for char in self.answer]
            for i in range(len(question_list)):
                if answer_list[i] == letter:
                    question_list[i] = letter
            self.question = ''.join(question_list)
            self.unknown_letters.pop(self.unknown_letters.index(letter))
            return "letter success!"
        else:  # It means the answer doesn't include the letter
            self.hp -= 1
            self.point += self.point_cfg['not_exist_letter']
            self.appears.append(letter)
            return "letter doesn't exist!"


class HangMan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def wrapper(context):
        def check_out(message) -> bool:
            return context.author == message.author and context.channel == message.channel

        return check_out

    @commands.command(name=command_name,
                      aliases=command_aliases,
                      brief=command_brief,
                      usage=command_usage,
                      help=command_help)
    async def hangman(self, ctx):
        the_player = {
            'id': ctx.message.author.id,
            'mention': ctx.message.author.mention,
            'name': ctx.message.author.display_name,
            'guild_id': ctx.guild.id,
            'guild_name': ctx.guild.name
        }
        game_info = "good luck!"

        question = Question(the_question)

        def bot_game_panel():
            panel = game_panel.format(
                the_man[question.hp].format(question.hp,
                                            len(question.unknown_letters),
                                            question.point),
                question.question,
                question.category,
                ''.join(question.appears),
                len(question.appears),
                the_player['name'],
                game_info
            )
            return ctx.send(panel)

        await ctx.send(
            "`'hint' to take hint\n"
            "'cancel' to finish`")

        while True:
            the_panel = await bot_game_panel()
            if question.hp == 0:
                game_info = "game over"
                await the_panel.delete()
                await bot_game_panel()
                break
            try:
                guess = await self.bot.wait_for(
                    "message",
                    timeout=guess_time_out,
                    check=self.wrapper(ctx)
                )
            except futures.TimeoutError:
                await the_panel.delete()
                game_info = f"timeout! {guess_time_out} seconds."
                await bot_game_panel()
                break

            if guess.author.id == the_player['id']:
                await sleep(1)
                await guess.delete()
                if guess.content.lower() == 'cancel':
                    game_info = f"the game canceled by {the_player['name']}!"
                    await the_panel.delete()
                    await bot_game_panel()
                    break
                elif guess.content.lower() == 'hint':
                    game_info = question.give_hint()
                    await the_panel.delete()
                else:
                    game_info = question.ask_letter(guess.content.lower())
                    if game_info == "one shot success! - game over!":
                        await the_panel.delete()
                        await bot_game_panel()
                        break
                    await the_panel.delete()


def setup(bot_):
    bot_.add_cog(HangMan(bot_))
