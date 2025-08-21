import telebot
import requests
import json
import time
from telebot.types import Message
from chk import check_card  # Import the check function from chk.py
from au import process_card_au

# Bot token (replace with your actual token)
BOT_TOKEN = "8320534432:AAFPzKpzxWMAPS7aBBYmW-MuOPnOYvxPDOc"
bot = telebot.TeleBot(BOT_TOKEN)

# Configuration
OWNER_ID = 123456789  # Replace with your Telegram ID
ADMIN_IDS = [987654321, 112233445]  # Replace with admin Telegram IDs
USER_DATA_FILE = "users.json"

# Load user data from file
def load_users():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save user data to file
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users, f)

# Get user status
def get_user_status(user_id):
    if user_id == OWNER_ID:
        return "Owner"
    elif user_id in ADMIN_IDS:
        return "Admin"
    else:
        return "User"

# Get bin information
def get_bin_info(bin_number):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_number}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Format for checking status
def checking_status_format(cc, gateway, bin_info):
    # Extract card details
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    
    # Format the response
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ ↯ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱 ⌁ {cc}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>Processing</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a>𝐁𝐫𝐚𝐧𝐝 ➳ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a>𝐁𝐚𝐧𝐤 ➳ {bin_info.get('type', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {bin_info.get('country_name', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>"""
    
    return result

# Format the check result for approved status
def approved_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken):
    # Extract card details
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    
    # Format the response
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('type', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country_name', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {Userstatus} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    
    return result

# Format the check result for declined status
def declined_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken):
    # Extract card details
    parts = cc.split('|')
    if len(parts) < 4:
        return "Invalid card format. Use: CC|MM|YY|CVV"
    
    # Format the response
    result = f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ Declined ❌</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱
   ↳ <code>{cc}</code>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⌁ <i>{gateway}</i> 
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⌁ <i>{response}</i>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ⌁ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('type', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country_name', 'UNKNOWN')} {bin_info.get('country_flag', '')}
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {Userstatus} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    
    return result

# Single check format function that chooses the right format
def single_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken, status):
    if status.upper() == "APPROVED":
        return approved_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken)
    else:
        return declined_check_format(cc, gateway, response, mention, Userstatus, bin_info, time_taken)

# Handle chk command
@bot.message_handler(commands=['chk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.chk'))
def handle_chk(message):
    # Save user
    save_user(message.from_user.id)
    
    # Extract CC details from message
    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return
    
    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return
    
    # Get user info
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    
    # Get bin info
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}
    
    # Send checking status message
    checking_msg = checking_status_format(cc, "Stripe Auth", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check CC using the external function from chk.py
    check_result = check_card(cc)
    
    # Calculate time taken
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    
    # Format and send final response
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
    
    # Edit the original message with the final result
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                         text=response_text, parse_mode='HTML')

@bot.message_handler(commands=['au'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.au'))
def handle_au(message):
    # Save user
    save_user(message.from_user.id)
    
    # Extract CC details from message
    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide CC details in format: CC|MM|YY|CVV")
        return
    
    cc = command_parts[1]
    if '|' not in cc:
        bot.reply_to(message, "Invalid format. Use: CC|MM|YY|CVV")
        return
    
    # Get user info
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    
    # Get bin info
    bin_number = cc.split('|')[0][:6]
    bin_info = get_bin_info(bin_number) or {}
    
    # Send checking status message
    checking_msg = checking_status_format(cc, "Stripe AU", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check CC using the AU function from au.py
    check_result = process_card_au(cc)
    
    # Calculate time taken
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    
    # Format and send final response
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
    
    # Edit the original message with the final result
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                         text=response_text, parse_mode='HTML')

# Broadcast function for owner/admin
@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    
    # Extract broadcast message
    broadcast_text = message.text.split(' ', 1)
    if len(broadcast_text) < 2:
        bot.reply_to(message, "Please provide a message to broadcast.")
        return
    
    broadcast_message = broadcast_text[1]
    users = load_users()
    
    # Send to all users
    sent_count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, broadcast_message)
            sent_count += 1
        except:
            # User might have blocked the bot
            pass
    
    bot.reply_to(message, f"Broadcast sent to {sent_count} users.")

# Start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    save_user(message.from_user.id)
    bot.reply_to(message, "Welcome to the CC Checker Bot! Use /chk or .chk followed by CC details.")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
