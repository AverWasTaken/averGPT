import os
import re
import discord
import openai
import json
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv # pip install python-dotenv, for some reason the package isnt "dotenv"

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APIKEY = os.getenv("OPENAI_API_KEY")

engine = "gpt-3.5-turbo"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="fin", intents=intents, heartbeat_timeout=120)

def trim_conversation_history(history, max_tokens=3000):
    trimmed_history = []
    total_tokens = 0

    for message in reversed(history):
        message_tokens = count_tokens(message["content"])
        if total_tokens + message_tokens > max_tokens:
            break

        trimmed_history.insert(0, message)
        total_tokens += message_tokens

    return trimmed_history

def save_conversation_history(user_id, history):
    file_name = f"conversation_history_{user_id}.json"
    with open(file_name, "w") as f:
        json.dump(history, f)

def load_conversation_history(user_id):
    file_name = f"conversation_history_{user_id}.json"
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            history = json.load(f)
    else:
        history = [{"role": "system", "content": "You are a AI powered discord bot named Fin that is designed to answer any question asked or communicate with users. You are to act very intelligent and also friendly. You are developed by a person named Aver and also OpenAI. If asked for, always provide those names."}]
        save_conversation_history(user_id, history)
    return history

def delete_old_history_files(max_age_hours=1):
    current_time = datetime.now()
    for file in os.listdir():
        if file.startswith("conversation_history_") and file.endswith(".json"):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file))
            age_hours = (current_time - file_creation_time).total_seconds() / 3600
            if age_hours > max_age_hours:
                os.remove(file)
                print(f"{file} History Deleted after one hour")

def count_tokens(text):
    return len(text.split())

def remove_mentions(text):
    mention_pattern = r"(@everyone|@here|<@!?\d+>|<@&\d+>)"
    return re.sub(mention_pattern, "", text)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="with the GPT-3.5 API"))
    await bot.tree.sync()

@bot.tree.command(name="fin", description="Interact with Fin, the AI assistant")
async def fin(Interaction: discord.Interaction, prompt: str):
    user_id = Interaction.user.id

    conversation_history = load_conversation_history(user_id)
    conversation_history.append({"role": "user", "content": prompt})

    # Trim the conversation history
    conversation_history = trim_conversation_history(conversation_history)

    async with Interaction.channel.typing():
        openai.api_key = APIKEY
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=500,
            n=1,
            temperature=0.7,
        )
    reply = response.choices[0].message['content'].strip()
    conversation_history.append({"role": "assistant", "content": reply})
    save_conversation_history(user_id, conversation_history)

    reply = remove_mentions(reply)
    color = discord.Color.from_rgb(255, 255, 255)
    embed = discord.Embed(title="Fin's Response:", description=f"**{reply}**", color=color)
    embed.set_footer(text="developed with ❤️ | by aver")

    await Interaction.response.send_message(embed=embed)

    delete_old_history_files()

bot.run(TOKEN)
