import discord
import requests
import os
import asyncio
import json
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from fantraxapi import FantraxAPI

def create_authenticated_session(username: str, password: str) -> requests.Session:
    session = requests.Session()
    
    # The login endpoint from the HAR file:
    login_url = "https://www.fantrax.com/fxpa/req"
    
    # Set headers as shown in the HAR file. Adjust if necessary.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "text/plain",  # Note: The request sends the payload as plain text
        "Referer": "https://www.fantrax.com/home",
        # You can add other headers if needed.
    }
    
    # Build the JSON payload.
    # The HAR file shows a structure like this:
    # {
    #   "msgs": [
    #       {
    #         "method": "login",
    #         "data": {
    #             "u": "cmduke",
    #             "p": "XfQJqUV6K5k6",
    #             "t": "03AFcWeA6BmZYCrP7Fxh-EDIryVa6schFWOAmaWUyvMZIbPLmEfXJEU6Ir7D2HW8_jB0286rIRekvUjwobnrNoYbkDQ_RqwlHZFHLTtKlgf1giAOcTAYhPwvvTZ7vThN_RPYOH51YjSOj43gTB6kG5ue4JXGNpScOpdPAdZw_z7B0zjbQOAI9aP9zooOWdJ2_jgPebif5eiJbe9fm6WIQgAh8HscZHSMneTXCi0GOekAr76JR_7t67BgA3B2rAR7dAqPQ_WA4Yoy3JwboGJczjC_uU7esJbNLDpuVsOSxmpgX6weP-hoU-uaEvCd3VDl-SlHpuSSScaLG7GV36JqBXXH7_qPYlzUrzjgLDzRciDzUO1QPZnT1SkjD0WCoqpdELfyudyrhl1s0-RROiZeGCbmDG1vP7mmzWX8lXXcfrlU-0r8lmEMYMhgVOyCzcTSXq_SU_nxtZ_AYtsp-dKBlp8Z4NDp5LL6tMheU3-jjqWs5qszfC92Pu-Ewn4LxMu7DHj9tTXXIGhAsE42OtUU6zzmoHyEVPHN8DyYLkvTNHEaTQ5GD1ymjkEytLVFxr-E4SMf1dzaGm7Nlo4RmgoTZBt756bPmRmOZGfMrg-aLAnvz7mh1xyvChF4eVaeq7UGdQUk_ofFJj8mqtGKGiypmMgocL7mGerFlFjB_fY-6Uc7AHdGKelUkovcgxN8q42Acmkf_IApU3DVfiplErk3aejBab7n7ICfBVUqCCvo6bVWZ3nPmEmCxdxdxufcpr0enl_SOHVGioYuxDsFIdor148gMxCrzuNR-U7lGIjtNtQi0PRiLLN1uTPK8j-2Nr8ymCjACNC17-rdQJn995BwMdiaSxaWdv48foZNle8HYvNJE5sF4ugui0to56TJYeftQWeNV4l390NL9n4Rw9bid5fnL86mPbn4uzC2SQZOq0GTEGYtgxmvcV50Q",
    #             "v": 3
    #         }
    #       }
    #   ],
    #   "uiv": 3,
    #   "refUrl": "https://www.fantrax.com/home",
    #   "dt": 2,
    #   "at": 0,
    #   "av": "0.0",
    #   "tz": "America/Chicago",
    #   "v": "167.0.0"
    # }
    #
    # Replace the login credentials below with your own.
    payload = {
        "msgs": [
            {
                "method": "login",
                "data": {
                    "u": username,
                    "p": password,
                    # The token "t" in the HAR file might be a constant or might change over time.
                    # You might need to update this value based on how Fantrax handles login.
                    "t": "03AFcWeA6BmZYCrP7Fxh-EDIryVa6schFWOAmaWUyvMZIbPLmEfXJEU6Ir7D2HW8_jB0286rIRekvUjwobnrNoYbkDQ_RqwlHZFHLTtKlgf1giAOcTAYhPwvvTZ7vThN_RPYOH51YjSOj43gTB6kG5ue4JXGNpScOpdPAdZw_z7B0zjbQOAI9aP9zooOWdJ2_jgPebif5eiJbe9fm6WIQgAh8HscZHSMneTXCi0GOekAr76JR_7t67BgA3B2rAR7dAqPQ_WA4Yoy3JwboGJczjC_uU7esJbNLDpuVsOSxmpgX6weP-hoU-uaEvCd3VDl-SlHpuSSScaLG7GV36JqBXXH7_qPYlzUrzjgLDzRciDzUO1QPZnT1SkjD0WCoqpdELfyudyrhl1s0-RROiZeGCbmDG1vP7mmzWX8lXXcfrlU-0r8lmEMYMhgVOyCzcTSXq_SU_nxtZ_AYtsp-dKBlp8Z4NDp5LL6tMheU3-jjqWs5qszfC92Pu-Ewn4LxMu7DHj9tTXXIGhAsE42OtUU6zzmoHyEVPHN8DyYLkvTNHEaTQ5GD1ymjkEytLVFxr-E4SMf1dzaGm7Nlo4RmgoTZBt756bPmRmOZGfMrg-aLAnvz7mh1xyvChF4eVaeq7UGdQUk_ofFJj8mqtGKGiypmMgocL7mGerFlFjB_fY-6Uc7AHdGKelUkovcgxN8q42Acmkf_IApU3DVfiplErk3aejBab7n7ICfBVUqCCvo6bVWZ3nPmEmCxdxdxufcpr0enl_SOHVGioYuxDsFIdor148gMxCrzuNR-U7lGIjtNtQi0PRiLLN1uTPK8j-2Nr8ymCjACNC17-rdQJn995BwMdiaSxaWdv48foZNle8HYvNJE5sF4ugui0to56TJYeftQWeNV4l390NL9n4Rw9bid5fnL86mPbn4uzC2SQZOq0GTEGYtgxmvcV50Q",
                    "v": 3
                }
            }
        ],
        "uiv": 3,
        "refUrl": "https://www.fantrax.com/home",
        "dt": 2,
        "at": 0,
        "av": "0.0",
        "tz": "America/Chicago",
        "v": "167.0.0"
    }
    
    # Convert payload to JSON string (as the request expects text/plain)
    payload_text = json.dumps(payload)
    
    # Send the login POST request
    response = session.post(login_url, headers=headers, data=payload_text)
    
    if response.status_code != 200:
        raise Exception(f"Login failed with status code: {response.status_code}")
    
    # Check if login was successful by looking for the JSESSIONID cookie.
    jsessionid = session.cookies.get("JSESSIONID", domain="www.fantrax.com")
    if not jsessionid:
        raise Exception("Login appears to have failed: JSESSIONID not found in cookies.")
    
    print("Login successful. JSESSIONID:", jsessionid)
    return session

if __name__ == "__main__":
    # Retrieve credentials from environment variables or replace with your values.
    username = os.getenv("FANTRAX_USERNAME")
    password = os.getenv("FANTRAX_PASSWORD")
    league_id = os.getenv("FANTRAX_LEAGUE_ID")
    
    # Create an authenticated session.
    session = create_authenticated_session(username, password)
    
    # Initialize the FantraxAPI with the authenticated session.
    api = FantraxAPI(league_id, session=session)

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
