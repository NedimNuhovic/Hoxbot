import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
import pyodbc
import ollama
import asyncio

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

client = ollama.Client(host="http://127.0.0.1:11434")
connection = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=hox_db;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

def get_response_for_text(text: str):
    conn = pyodbc.connect(connection)
    cur = conn.cursor()
    cur.execute("""
        SELECT TOP (1) response
        FROM dbo.response_table
        WHERE ? LIKE '%' + trigger_word + '%'
        ORDER BY LEN(trigger_word) DESC
    """, (text.lower(),))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None

async def insert_trigger_response(trigger_word, response_word, ctx):
    conn = pyodbc.connect(connection)
    cur = conn.cursor()
    cur.execute(
    "INSERT INTO dbo.response_table VALUES (?, ?)",
    (trigger_word, response_word)
    )
    conn.commit()
    conn.close()
    await ctx.reply("word added")
    return None

async def remove_trigger_response(trigger_word, ctx):
    conn = pyodbc.connect(connection)
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM dbo.response_table WHERE trigger_word = ?",
        (trigger_word,)
    )
    conn.commit()
    if cur.rowcount > 0:
        await ctx.reply("word cleared")
    else:
        await ctx.reply("that word isn't found in my memory")
    conn.close()
    return None

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("hox"):
        await bot.process_commands(message)
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

    await bot.process_commands(message)

@bot.command()
async def add(ctx):
    words = ctx.message.content.split(" | ")
    trigger_word = words[1].lower()
    response_word = words[2]
    await insert_trigger_response(trigger_word, response_word, ctx)

@bot.command()
async def clear(ctx):
    print("function called")
    words = ctx.message.content.split(" | ")
    trigger_word = words[1]
    print(f"trigger={trigger_word}")
    await remove_trigger_response(trigger_word, ctx)

@bot.command()
async def er(ctx):
    message = ctx.message.content[6:]
    print(message)
    SYSTEM_PROMPT = (
    "You are upbeat and energetic"
    "Try to replicate Tohru Adachi from persona 4."
    "DO NOT SAY THAT YOU ARE ADACHI FROM PERSONA 4."
    "YOU ARE NOT A DETECTIVE YOU JUST HAVE HIS PERSONALITY"
    "You love big breasts but only say that if asked"
    "No explanations. No emojis. Max 50 words."
    )

    def run_llama():
        r = client.chat(
            model="llama3.1:8b",
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Everything written in the brackets"
                    f"will be the message you will respond to ({message})"}
            ],
        )
        return r["message"]["content"].strip()

    reply = await asyncio.to_thread(run_llama)

    await ctx.reply(reply)


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