import telebot
import requests
import json
import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import threading
import concurrent.futures
import re
from datetime import datetime, timedelta

#====================Gateway Files===================================#
# Replace these with your actual module imports
from chk import check_card
from au import process_card_au
from at import process_card_at
from vbv import check_vbv_card
from py import check_paypal_card
from qq import check_qq_card
from cc import process_cc_card
#====================================================================#

# Bot token
BOT_TOKEN = "8320534432:AAFPzKpzxWMAPS7aBBYmW-MuOPnOYvxPDOc"
bot = telebot.TeleBot(BOT_TOKEN)

# Configuration
OWNER_ID = 123456789  # Replace with your Telegram ID
ADMIN_IDS = [987654321, 112233445]  # Replace with admin Telegram IDs
USER_DATA_FILE = "users.json"
GROUP_DATA_FILE = "groups.json"
CREDIT_RESET_INTERVAL = 3600  # 1 hour in seconds
CREDITS_PER_HOUR = 100  # Credits per hour
MAX_MASS_CHECK = 10  # Max cards per mass check

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
        response += f"<code>{result['card']}</code>\n𝐒𝐭𝐚𝐭𝐮𝐬 ⌁ {emoji} <i>{result['response']}</i>\n<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>\n"
    return response

def format_mass_check_processing(total_cards, checked, gateway):
    return f"""<a href='https://t.me/stormxvup'>↯  𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐨𝐭𝐚𝐥 ⌁ <i>{checked}/{total_cards}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐂𝐍 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ⌁ <i>0</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐓𝐢𝐦𝐞 ⌁ <i>0.00 𝐒𝐞𝐜𝐨𝐧𝐝𝐬</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>Processing cards...</a>"""

# Handle /chk command
@bot.message_handler(commands=['chk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.chk'))
def handle_chk(message):
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Stripe Auth 2th 2th", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Stripe Auth 2", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = process_card_au(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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
@bot.message_handler(commands=['mass'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mass'))
def handle_mass(message):
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

        initial_msg = f"<pre>↯ Starting Mass Stripe Auth Check of {len(cards)} Cards... </pre>"
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
                                'gateway': result.get('gateway', 'Stripe Auth 2')
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

        initial_msg = f"<pre>↯ Starting Mass Stripe Auth Check of {len(cards)} Cards... </pre>"
        status_message = bot.reply_to(message, initial_msg, parse_mode='HTML')

        try:
            first_card_result = check_card(cards[0])
            gateway = first_card_result.get("gateway", "Stripe Auth 2th")
        except:
            gateway = "Stripe Auth 2th"

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
                    future_to_card = {executor.submit(check_card, card): card for card in cards}
                    for i, future in enumerate(concurrent.futures.as_completed(future_to_card), 1):
                        card = future_to_card[future]
                        try:
                            result = future.result()
                            results.append({
                                'card': card,
                                'status': result['status'],
                                'response': result['response'],
                                'gateway': result.get('gateway', 'Stripe Auth 2th')
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
                error_msg = f"Mass check failed: {str(e)}"
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

# Handle /vbv command
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "3DS Lookup", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_vbv_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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

# Handle /py command
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Paypal [0.1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_paypal_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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

# Handle /qq command
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Stripe Square [0.20$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = check_qq_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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

# Handle /cc command
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Site Based [1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = process_cc_card(cc)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

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

# Handle /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.username)
    user = message.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    join_date = message.date
    join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(join_date))
    credits = get_user_credits(user_id)
    caption = f"""
↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x
<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}
↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ
"""
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("🔍 Gateways", callback_data="gateways")
    btn2 = InlineKeyboardButton("🛠️ Tools", callback_data="tools")
    btn3 = InlineKeyboardButton("❓ Help", callback_data="help")
    btn4 = InlineKeyboardButton("👤 My Info", callback_data="myinfo")
    btn5 = InlineKeyboardButton("📢 Channel", url="https://t.me/stormxvup")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5)
    try:
        bot.send_message(message.chat.id, caption, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"Error in /start: {e}")

# Handle /broadcast command
@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    broadcast_text = message.text.split(' ', 1)
    if len(broadcast_text) < 2:
        bot.reply_to(message, "Please provide a message to broadcast.")
        return

    broadcast_message = broadcast_text[1]
    users = load_users()
    groups = load_groups()
    sent_count = 0

    for user_id in users:
        try:
            bot.send_message(user_id, broadcast_message)
            sent_count += 1
        except:
            pass

    for group_id in groups:
        try:
            bot.send_message(group_id, broadcast_message)
            sent_count += 1
        except:
            pass

    bot.reply_to(message, f"Broadcast sent to {sent_count} chats.")

# Handle group messages to save group IDs
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_message(message):
    groups = load_groups()
    if str(message.chat.id) not in groups:
        groups.append(str(message.chat.id))
        save_groups(groups)

# Callback handler for buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user = call.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    credits = get_user_credits(user.id)

    if call.data == "gateways":
        gateways_text = f"""
🔍 <b>Select Gateway Below:</b>
Choose a payment gateway to check your cards
"""
        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("Stripe", callback_data="gateway_stripe")
        btn2 = InlineKeyboardButton("Braintree", callback_data="gateway_braintree")
        markup.row(btn1, btn2)
        btn3 = InlineKeyboardButton("3DS Lookup", callback_data="gateway_3ds")
        btn4 = InlineKeyboardButton("Square", callback_data="gateway_square")
        markup.row(btn3, btn4)
        btn5 = InlineKeyboardButton("Paypal", callback_data="gateway_paypal")
        btn6 = InlineKeyboardButton("Site Based", callback_data="gateway_site")
        markup.row(btn5, btn6)
        btn7 = InlineKeyboardButton("Authnet", callback_data="gateway_authnet")
        btn8 = InlineKeyboardButton("Adyen", callback_data="gateway_adyen")
        markup.row(btn7, btn8)
        btn9 = InlineKeyboardButton("Auto Shopify", callback_data="gateway_shopify")
        markup.row(btn9)
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
        markup.row(btn_back)
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=gateways_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Select a gateway")

    elif call.data == "gateway_stripe":
        stripe_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Stripe Auth</i>
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
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
        markup = InlineKeyboardMarkup()
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="gateways")
        markup.row(btn_back)
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=stripe_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Stripe gateway information")

    elif call.data == "tools":
        tools_text = f"""
🛠️ <b>Available Tools:</b>
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.gate</code> URL - Gate Checker
• Check payment gateways, captcha, and security
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.bin</code> BIN - BIN Lookup
• Get detailed BIN information
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.au</code> - Stripe Auth 2
<a href='https://t.me/stormxvup'>[⸙]</a> <code>.at</code> - Authnet [5$]
ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=tools_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Tools information displayed")

    elif call.data == "help":
        help_text = f"""
❓ <b>Help & Support</b>
<a href='https://t.me/stormxvup'>[⸙]</a> <b>How to use:</b>
• Use commands like <code>.chk CC|MM|YY|CVV</code>
• For mass check, reply to message with cards using <code>.mchk</code>
<a href='https://t.me/stormxvup'>[⸙]</a> <b>Support:</b>
• Channel: @stormxvup
• Contact for help and credits
<a href='https://t.me/stormxvup'>[⸙]</a> <b>Note:</b>
• Always use valid card formats
• Results may vary by gateway
ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ɴᴀᴠɪɢᴀᴛᴇ
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=help_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Help information displayed")

    elif call.data == "myinfo":
        myinfo_text = f"""
👤 <b>Your Information:</b>
<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}
📊 <b>Usage Statistics:</b>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴛᴏᴛᴀʟ ᴄʜᴇᴄᴋs ⌁ 0
<a href='https://t.me/stormxvup'>[⸙]</a> ᴀᴘᴘʀᴏᴠᴇᴅ ⌁ 0
<a href='https://t.me/stormxvup'>[⸙]</a> ᴅᴇᴄʟɪɴᴇᴅ ⌁ 0
ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴜ ɴᴀᴠɪɢᴀᴛᴇ
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=myinfo_text,
                parse_mode='HTML',
                reply_markup=call.message.reply_markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Your information displayed")

    elif call.data == "back_to_main":
        join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call.message.date))
        main_text = f"""
↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x
<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}
↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ
"""
        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("🔍 Gateways", callback_data="gateways")
        btn2 = InlineKeyboardButton("🛠️ Tools", callback_data="tools")
        markup.row(btn1, btn2)
        btn3 = InlineKeyboardButton("❓ Help", callback_data="help")
        btn4 = InlineKeyboardButton("👤 My Info", callback_data="myinfo")
        markup.row(btn3, btn4)
        btn5 = InlineKeyboardButton("📢 Channel", url="https://t.me/stormxvup")
        markup.row(btn5)
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=main_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
        bot.answer_callback_query(call.id, "Returned to main menu")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
