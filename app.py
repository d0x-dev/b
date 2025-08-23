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

# Handle /mvbv command
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
                        result = check_vbv_card(card)
                        results.append({
                            'card': card,
                            'status': result['status'],
                            'response': result['response'],
                            'gateway': result.get('gateway', '3DS Lookup')
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
                error_msg = f"Mass VBV check failed: {str(e)}"
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

# Handle /mpy command
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
                        result = check_paypal_card(card)
                        results.append({
                            'card': card,
                            'status': result['status'],
                            'response': result['response'],
                            'gateway': result.get('gateway', 'Paypal [0.1$]')
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
                error_msg = f"Mass PayPal check failed: {str(e)}"
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

# Handle /at command
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

    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}

    checking_msg = checking_status_format(cc, "Authnet [5$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')

    start_time = time.time()
    check_result = process_card_at(cc)
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
            bot.reply_to(message, "❌ You don't have enough credits. Wait for your credits to reset.")
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐕𝐕/𝐂𝐕𝐂 ➳ <i>{result.get('cvv_cvc_status', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐈𝐧𝐛𝐮𝐢𝐥𝐭 𝐒𝐲𝐬𝐭𝐞𝐦 ➳ <i>{result.get('inbuilt_system', 'Unknown')}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐒𝐭𝐚𝐭𝐮𝐬 ➳ <i>{result.get('status_code', 'N/A')}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗢𝗧𝗔𝗟 𝗧𝗜𝗠𝗘 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

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
    save_users(message.from_user.id)
    
    # Get user information
    user = message.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    join_date = message.date  # This is a timestamp, convert to readable format
    join_date_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(join_date))
    
    
    # Create the caption with formatting
    caption = f"""
↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x

<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}

↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ
"""
    
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

# Add callback handler for the buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user = call.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    username = f"@{user.username}" if user.username else "None"
    credits = "0"  # Default credits
    
    if call.data == "gateways":
        # Show gateway selection menu
        gateways_text = f"""
🔍 <b>Select Gateway Below:</b>

Choose a payment gateway to check your cards
"""
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
        braintree_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Braintree Auth</i>
[⸙] 𝐂𝐌𝐃: /b3 [Single]
[⸙] 𝐂𝐌𝐃: /mb3 [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
──────── ⸙ ─────────
[⸙] 𝐍𝐀𝐌𝐄: <i>Braintree Charge</i>
[⸙] 𝐂𝐌𝐃: /br [Single]
[⸙] 𝐂𝐌𝐃: /mbr [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        three_ds_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>3DS Lookup</i>
[⸙] 𝐂𝐌𝐃: /vbv [Single]
[⸙] 𝐂𝐌𝐃: /mvbv [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        square_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Square Charge</i>
[⸙] 𝐂𝐌𝐃: /qq [Single]
[⸙] 𝐂𝐌𝐃: /mqq [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        paypal_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Paypal Charge</i>
[⸙] 𝐂𝐌𝐃: /py [Single]
[⸙] 𝐂𝐌𝐃: /mpy [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        site_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Site Based Charge</i>
[⸙] 𝐂𝐌𝐃: /cc [Single]
[⸙] 𝐂𝐌𝐃: /mcc [Mass]
[⸙] 𝐒𝐭𝐎𝐭𝐮𝐬: Active ✅
"""
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
        authnet_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Authnet Charge</i>
[⸙] 𝐂𝐌𝐃: /at [Single]
[⸙] 𝐂𝐌𝐃: /mat [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        adyen_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Adyen Charge</i>
[⸙] 𝐂𝐌𝐃: /ad [Single]
[⸙] 𝐂𝐌𝐃: /mad [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        shopify_text = f"""
[⸙] 𝐍𝐀𝐌𝐄: <i>Auto Shopify Charge</i>
[⸙] 𝐂𝐌𝐃: /sh [Single]
[⸙] 𝐂𝐌𝐃: /msh [Mass]
[⸙] 𝐒𝐭𝐚𝐭𝐮𝐬: Active ✅
"""
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
        main_text = f"""
↯ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ sᴛᴏʀᴍ x

<a href='https://t.me/stormxvup'>[⸙]</a> ғᴜʟʟ ɴᴀᴍᴇ ⌁ {mention}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴊᴏɪɴ ᴅᴀᴛᴇ ⌁ {join_date_formatted}
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʜᴀᴛ ɪᴅ ⌁ <code>{user.id}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴜsᴇʀɴᴀᴍᴇ ⌁ <i>{username}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> ᴄʀᴇᴅɪᴛs ⌁ {credits}

↯ ᴜsᴇ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ
"""
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

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
