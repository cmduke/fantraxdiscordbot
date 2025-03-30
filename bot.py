import os
import json
import requests
from fantraxapi import FantraxAPI
from discord.ext import tasks, commands

# Global variable for the FantraxAPI instance.
api = None

def create_authenticated_session(username: str, password: str) -> requests.Session:
    session = requests.Session()

    # Login endpoint from your HAR file.
    login_url = "https://www.fantrax.com/fxpa/req"
    
    # Headers extracted from HAR file.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "text/plain",
        "Referer": "https://www.fantrax.com/home",
        "Origin": "https://www.fantrax.com"
    }
    
    # Payload based on HAR file.
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
    
    # Convert payload to a JSON string.
    payload_text = json.dumps(payload)
    
    # Send the login POST request.
    response = session.post(login_url, headers=headers, data=payload_text)
    
    print("Login response status:", response.status_code)
    print("Response headers:", response.headers)
    print("Session cookies after login:", session.cookies.get_dict())
    
    # Check for an authentication cookie.
    auth_cookie = session.cookies.get("JSESSIONID")
    if not auth_cookie:
        auth_cookie = session.cookies.get("uig")
    if not auth_cookie:
        raise Exception("Login appears to have failed: No valid authentication cookie found.")
    
    print("Login successful. Auth cookie:", auth_cookie)
    return session

# Bot setup
bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    global api
    print(f"Bot logged in as {bot.user}")
    # Create an authenticated session and initialize the FantraxAPI.
    username = os.getenv("FANTRAX_USERNAME")
    password = os.getenv("FANTRAX_PASSWORD")
    league_id = os.getenv("FANTRAX_LEAGUE_ID")
    session = create_authenticated_session(username, password)
    api = FantraxAPI(league_id, session=session)
    periodic_check.start()

@tasks.loop(hours=1)
async def periodic_check():
    channel = bot.get_channel(1355397798161416412)
    if channel and api:
        await check_trade_block(channel, api)

# Example command function
@bot.command(name="checktradeblock")
async def check_tradeblock_command(ctx):
    await check_trade_block(ctx.channel, api)

# Placeholder for check_trade_block and get_recent_trade_blocks functions.
async def check_trade_block(channel, api):
    recent_trade_blocks = get_recent_trade_blocks(api)
    if recent_trade_blocks:
        for trade_block in recent_trade_blocks:
            update_message = f"Trade Block updated: {trade_block}"
            await channel.send(update_message)
    else:
        await channel.send("No recent updates to the trade block.")

def get_recent_trade_blocks(api):
    # This function assumes the API call returns a list of trade blocks.
    trade_blocks = api.trade_block()
    # Filter trade blocks as needed.
    return trade_blocks

bot.run(os.getenv("DISCORD_TOKEN"))
