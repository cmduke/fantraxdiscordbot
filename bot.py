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

    # The login endpoint from your HAR file:
    login_url = "https://www.fantrax.com/fxpa/req"
    
    # Set headers as shown in the HAR file.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "text/plain",
        "Referer": "https://www.fantrax.com/home",
        "Origin": "https://www.fantrax.com"
    }
    
    # Build the JSON payload exactly as seen in the HAR file.
    # NOTE: The value for "t" (the token) may be dynamic. If login fails, consider updating this value.
    payload = {
        "msgs": [
            {
                "method": "login",
                "data": {
                    "u": username,
                    "p": password,
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
    
    # Convert payload to a JSON string, as the request expects text/plain.
    payload_text = json.dumps(payload)
    
    # Send the POST request.
    response = session.post(login_url, headers=headers, data=payload_text)
    
    print("Login response status:", response.status_code)
    print("Response headers:", response.headers)
    
    # For debugging: print any Set-Cookie headers.
    if "set-cookie" in response.headers:
        print("Set-Cookie header:", response.headers["set-cookie"])
    
    # After the login request, inspect the session cookies.
    print("Session cookies after login:", session.cookies.get_dict())
    
    # Check if login was successful by verifying presence of JSESSIONID.
    auth_cookie = session.cookies.get("JSESSIONID", domain="www.fantrax.com")
    if not auth_cookie:
        # Fall back to checking for the "uig" cookie.
        auth_cookie = session.cookies.get("uig", domain="fantrax.com") or session.cookies.get("uig", domain="www.fantrax.com")
    if not auth_cookie:
        raise Exception("Login appears to have failed: No valid authentication cookie found.")
    print("Login successful. Auth cookie:", auth_cookie)
    return session

if __name__ == "__main__":
    # Retrieve credentials and league ID (or set them directly for testing).
    username = os.getenv("FANTRAX_USERNAME", "your_username")
    password = os.getenv("FANTRAX_PASSWORD", "your_password")
    league_id = os.getenv("FANTRAX_LEAGUE_ID", "your_league_id")
    
    try:
        # Create an authenticated session.
        session = create_authenticated_session(username, password)
        
        # Initialize the FantraxAPI with the authenticated session.
        api = FantraxAPI(league_id, session=session)
        
        # Attempt to retrieve trade block data.
        trade_blocks = api.trade_block()
        print("Trade blocks retrieved successfully.")
    except Exception as e:
        print("Error during login or fetching trade blocks:", e)

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
