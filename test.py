# -*- coding: utf-8 -*-

from discord.ext import commands
from config import get_token

TOKEN = get_token()

bot = commands.Bot(
    command_prefix="!",
    case_insensitive=True,
    strip_after_prefix=True,
)


@bot.event
async def on_ready():
    print("Tester is ready!")

bot.load_extension("hangman")

try:
    bot.run(TOKEN)
except Exception as e:
    print(f"LOGGING ERROR: {e}")
