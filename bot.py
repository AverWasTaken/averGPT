#apikey = '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'
#token = 'MTA4Nzk2NTQ1OTk0MjQ3Nzg2Ng.G8h8J-._7FIN6qiSB181xE0kiTFM4WBom6g26a1OXehlw'

import os
import random
import re
import discord
import aiohttp
import openai
import httpx
from discord.ext import commands

engine = "pt-3.5-turbo"

apikey = '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'
token = 'MTA4Nzk2NTQ1OTk0MjQ3Nzg2Ng.G8h8J-._7FIN6qiSB181xE0kiTFM4WBom6g26a1OXehlw'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents, heartbeat_timeout=120)

conversation_history = {}
response_probability = 0

def count_tokens(text):
    return len(text.split())

def remove_mentions(text):
    mention_pattern = r"(@everyone|@here|<@!?\d+>|<@&\d+>)"
    return re.sub(mention_pattern, "", text)

async def download_file(url, file_name):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with open(file_name, 'wb') as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)



async def process_txt_file(file_name, user_id, prompt):
    ...
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.openai.com/v1/engines/{engine}/completions",
            json={
                "messages": [{"role": "system", "content": "You are a helpful assistant."},
                             {"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.5,
                "stop": ["\n"],
                "n": 1,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai.api_key}"
            }
        )
    response = response.json()
    ...


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="With The GPT-3 API."))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    prompt = message.content
    user_id = message.author.id
    if prompt.startswith("gpt "):
        prompt = prompt[4:]
    elif random.random() >= response_probability:
        await bot.process_commands(message)
        return

    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    conversation_history[user_id].append({"role": "user", "content": prompt})

    async with message.channel.typing():
        openai.api_key = apikey
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history[user_id],
            max_tokens=500,
            n=1,
            temperature=0.7,
        )
    reply = response.choices[0].message['content'].strip()
    conversation_history[user_id].append({"role": "assistant", "content": reply})

    reply = remove_mentions(reply)
    await message.reply(reply, mention_author=False)
    await bot.process
    commands(message)

@bot.command(name="gpttxt")
async def gpttxt_command(ctx, *, prompt: str):
    if not ctx.message.attachments:
        await ctx.send("Please attach a .txt file to your message.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(".txt"):
        await ctx.send("Please make sure the attached file is a .txt file.")
        return

    file_name = f"{ctx.message.id}_{attachment.filename}"
    await download_file(attachment.url, file_name)

    user_id = ctx.author.id
    async with ctx.channel.typing():
        reply = await process_txt_file(file_name, user_id, prompt)

    os.remove(file_name)
    if reply.strip():  # Check if reply is not empty or contains only whitespace
        await ctx.send(reply)
else:
    await ctx.send("No response generated. Please try again with a different prompt.")

bot.run(token)



