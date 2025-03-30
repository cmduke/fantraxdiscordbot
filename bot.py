import os
import json
import requests
from fantraxapi import FantraxAPI
import discord
from discord.ext import tasks, commands

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

# Create the bot instance with the required intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variable for our authenticated FantraxAPI instance
api = None

def create_authenticated_session(username: str, password: str) -> requests.Session:
    """
    Create and return an authenticated session for Fantrax.
    This function sends a POST request to the Fantrax login endpoint
    using a payload extracted from your HAR file.
    """
    session = requests.Session()

    # Login endpoint from the HAR file
    login_url = "https://www.fantrax.com/fxpa/req"
    
    # Headers extracted from your HAR file
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "text/plain",  # The payload is sent as plain text
        "Referer": "https://www.fantrax.com/home",
        "Origin": "https://www.fantrax.com"
    }
    
    # Payload based on your HAR file.
    # Note: The "t" field (token) may be dynamic. Adjust if needed.
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
    
    # Convert payload to JSON string
    payload_text = json.dumps(payload)
    
    # Send login request
    response = session.post(login_url, headers=headers, data=payload_text)
    
    print("Login response status:", response.status_code)
    print("Response headers:", response.headers)
    print("Session cookies after login:", session.cookies.get_dict())
    
    # Check for authentication cookie.
    # The HAR file shows the "uig" cookie is set.
    auth_cookie = session.cookies.get("JSESSIONID")
    if not auth_cookie:
        auth_cookie = session.cookies.get("uig")
    if not auth_cookie:
        raise Exception("Login appears to have failed: No valid authentication cookie found.")
    
    print("Login successful. Auth cookie:", auth_cookie)
    return session

def get_recent_trade_blocks(api_instance):
    """
    Call the trade_block endpoint via the FantraxAPI.
    You can filter and format trade blocks as needed.
    """
    try:
        trade_blocks = api_instance.trade_block()
        return trade_blocks
    except Exception as e:
        print("Error fetching trade blocks:", e)
        return []

async def check_trade_block(channel, api_instance):
    """
    Check for recent trade blocks and send messages to the given Discord channel.
    """
    recent_trade_blocks = get_recent_trade_blocks(api_instance)
    if recent_trade_blocks:
        for trade_block in recent_trade_blocks:
            update_message = f"Trade Block update: {trade_block}"
            await channel.send(update_message)
    else:
        await channel.send("No recent updates to the trade block.")

# Bot event: on_ready
@bot.event
async def on_ready():
    global api
    print(f"Bot logged in as {bot.user}")
    # Retrieve credentials and league ID from environment variables
    username = os.getenv("FANTRAX_USERNAME")
    password = os.getenv("FANTRAX_PASSWORD")
    league_id = os.getenv("FANTRAX_LEAGUE_ID")
    # Create an authenticated session and initialize the FantraxAPI
    session = create_authenticated_session(username, password)
    api = FantraxAPI(league_id, session=session)
    periodic_check.start()

# Periodic task to check trade blocks every hour
@tasks.loop(hours=1)
async def periodic_check():
    channel = bot.get_channel(1355397798161416412)  # Replace with your channel ID
    if channel and api:
        await check_trade_block(channel, api)

# Command to manually check the trade block
@bot.command(name="checktradeblock")
async def checktradeblock_command(ctx):
    if api:
        await check_trade_block(ctx.channel, api)
    else:
        await ctx.send("API is not initialized yet.")

# Run the bot using the DISCORD_TOKEN environment variable
bot.run(os.getenv("DISCORD_TOKEN"))
