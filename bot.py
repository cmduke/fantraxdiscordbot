import discord
import os

# Create an instance of Intents and enable the specific ones you need
intents = discord.Intents.default()

# Enable the necessary intents
intents.message_content = True  # Allows your bot to read message content
intents.presences = True         # Allows your bot to track presence (online/offline) status
intents.members = True           # Allows your bot to track member updates (joining, leaving, etc.)


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
