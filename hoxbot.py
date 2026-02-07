import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')

message_logger = logging.getLogger('message_logger')
message_logger.setLevel(logging.INFO)
message_handler = logging.FileHandler("message.log", encoding="utf-8", mode='a')
message_logger.addHandler(message_handler)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True           # member join/leave, member info
intents.presences = True         # online/offline status (optional)
intents.reactions = True         # reaction add/remove
intents.guilds = True

bot = commands.Bot(command_prefix='hox', intents=intents)
bot_channel_id = 1466365993981972598
triggers = {
    "tits" : "this",
    "boobs" : "rude",
    "sex" : "stop!!",
    "spam" : "spam"
}

def get_response_for_text(text: str):
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=hox_db;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    cur = conn.cursor()

    cur.execute("""
        SELECT [trigger_word], [response]
        FROM dbo.response_table    
    """)

    text = text.lower()

    for trigger_word, response_word in cur.fetchall():
        if trigger_word.lower() in text:
            conn.close()
            return response_word

    conn.close()
    return None

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    try:
        reply_db = get_response_for_text(message.content)
    except Exception as e:
        print("Db error:", repr(e))
        reply_db = None

    if reply_db:
        await message.reply(reply_db)
        print(f"{reply_db} was found in the database")
        return

    message_logger.info(f"{message.author}: {message.content}")

    for word, reply in triggers.items():
        if word in message.content:
            await message.reply(reply)
            break

    await bot.process_commands(message)

@bot.event
async def on_ready():
    channel = bot.get_channel(bot_channel_id)
    print(f'Yokai! {bot.user.name} yoroshiku!')
    await channel.send("Yokai!")

@bot.command()
@commands.has_role('hox')
async def hox(ctx):
    await ctx.reply("Hox! Hox!")

@hox.error
async def secret_error(ctx, error):
    await ctx.send("whore you??")

@bot.command()
async def me(ctx):
    role = discord.utils.get(ctx.guild.roles, name='hox')
    await ctx.author.add_roles(role)
    await ctx.reply("Hox! ~⭐")

@bot.command()
async def nt(ctx):
    role = discord.utils.get(ctx.guild.roles, name='hox')
    await ctx.author.remove_roles(role)
    await ctx.reply("Hox! ~🌟")

@bot.event
async def on_message_delete(message):
    channel = bot.get_channel(bot_channel_id)
    await channel.send(f"{message.author.mention}I saw the cringe you posted")



bot.run(token, log_handler=handler, log_level=logging.DEBUG)
