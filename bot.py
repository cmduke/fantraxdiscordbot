import discord
import os
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from fantraxapi import FantraxAPI

# Initialize Fantrax API with the league ID
league_id = os.getenv("FANTRAX_LEAGUE_ID")  # Make sure your league ID is set in environment variables
api = FantraxAPI(league_id)


# Set the prefix that precedes all bot commands in Discord
bot_prefix = "!"  # Directly setting the command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

def get_recent_trade_blocks(api):
    # Use the correct method from FantraxAPI
    trade_blocks = api.trade_block()  # Updated method call
    
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_trade_blocks = []
    for trade_block in trade_blocks:
        update_date = trade_block['update_date']  # Ensure this is a datetime object
        if update_date >= one_hour_ago:
            recent_trade_blocks.append(trade_block)
    
    return recent_trade_blocks

async def check_trade_block(channel, api):
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
    channel = bot.get_channel(1355397798161416412)  # Replace with your channel ID
    if channel:
        await check_trade_block(channel, api)

@bot.command(name="checktradeblock")
async def checktradeblock_command(ctx):
    """Manually check the trade block for updates"""
    await check_trade_block(ctx.channel, api)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    print(f"Command prefix: {bot_prefix}")
    periodic_check.start()  # Start the hourly check when the bot is ready

@bot.event
async def on_message(message):
    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')
    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
