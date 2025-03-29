import discord
import os

intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot with your token
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

# Run the bot
client.run(os.getenv('DISCORD_TOKEN'))
