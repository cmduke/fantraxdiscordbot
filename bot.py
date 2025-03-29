import discord
import os
import asyncio
import requests
from fantraxapi import FantraxAPI
from discord.ext import commands, tasks
from datetime import datetime, timedelta

# Initialize Fantrax API with the league ID
league_id = os.getenv("FANTRAX_LEAGUE_ID")  # Make sure your league ID is set in environment variables
api = FantraxAPI(league_id)

# Set the prefix that precedes all bot commands in Discord
bot_prefix = "!"  # Directly setting the command prefix

# Create an instance of Intents and enable the specific ones you need
intents = discord.Intents.default()

# Enable the necessary intents
intents.message_content = True  # Allows your bot to read message content
intents.presences = True         # Allows your bot to track presence (online/offline) status
intents.members = True           # Allows your bot to track member updates (joining, leaving, etc.)


# Initialize the bot with your token
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)


def get_recent_trade_blocks(api):
    # Fetch the trade block data
    trade_blocks = api.get_trade_block()
    
    # Get the current time and calculate the time one hour ago
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    # Filter trade blocks updated within the last hour
    recent_trade_blocks = []
    for trade_block in trade_blocks:
        update_date = trade_block['update_date']  # Ensure this is a datetime object
        if update_date >= one_hour_ago:
            recent_trade_blocks.append(trade_block)
    
    return recent_trade_blocks

async def check_trade_block(channel, api):
    # Get the recent trade blocks that were updated within the last hour
    recent_trade_blocks = get_recent_trade_blocks(api)

    if recent_trade_blocks:
        for trade_block in recent_trade_blocks:
            team_name = trade_block['team']['name']
            players_offered = trade_block['players_offered']
            positions_wanted = trade_block['positions_wanted']
            note = trade_block['note']
            update_message = f"**{team_name}** has updated their trade block:\n"
            update_message += f"Note: {note}\n"
            update_message += f"Players Offered: {', '.join(players_offered.keys())}\n"
            update_message += f"Positions Wanted: {', '.join(positions_wanted)}\n"
                
            await channel.send(update_message)
    else:
        await channel.send("No recent updates to the trade block.")


# Task to check the trade block every hour
@tasks.loop(hours=1)
async def periodic_check():
    # Change this to the channel you want the bot to post in
    channel = bot.get_channel(1355397798161416412)  # Replace YOUR_CHANNEL_ID with the actual channel ID
    if channel:
        await check_trade_block(channel, api)

# Command to trigger trade block check
@bot.command()
async def check_trade_block(channel, api):
    """Command to check the trade block for updates"""
    print("Checktradeblock command triggered")
    updated_blocks = check_trade_block()
    
    if updated_blocks:
        response = "Here are the teams with updated trade blocks in the past hour:\n"
        for block in updated_blocks:
            response += f"- {block.team.name}: {block.note}\n"
    else:
        response = "No trade block updates in the last hour."
    
    await ctx.send(response)

# Start the periodic task when the bot is ready
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    print(f"Command prefix: {config['bot_prefix']}")
    periodic_check.start()  # Start the hourly check when the bot is ready


async def scheduled_check():
    await bot.wait_until_ready()
    channel = bot.get_channel(1355397798161416412)  # Replace with your channel ID
    while not bot.is_closed():
        await check_trade_block(channel, api)  # Check for recent trade block updates
        await asyncio.sleep(3600)  # Wait for an hour before checking again


# def get_transactions():
#     league_id = os.getenv('FANTRAX_LEAGUE_ID')
#     api_key = os.getenv('FANTRAX_API_KEY')  # Make sure to set this environment variable in Railway

#     url = f'https://api.fantrax.com/league/{league_id}/transactions'
    
#     headers = {
#         'Authorization': f'Bearer {api_key}'
#     }

#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         transactions = response.json()
#         # For example, we can filter for new trade transactions
#         new_trades = [tx for tx in transactions if tx['type'] == 'trade']
#         return new_trades
#     else:
#         print(f"Error fetching transactions: {response.status_code}")
#         return []

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')



# Run the bot
client.run(os.getenv('DISCORD_TOKEN'))
