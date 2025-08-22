2import telebot
import requests
import json
import time
from telebot.types import Message
import threading
from chk import check_card  # Import the check function from chk.py
from au import process_card_au
from at import process_card_at

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

<a href='https://t.me/stormxvup'>[⸙]</a> 𝗖𝗮𝗿𝗱 ⌁ <code>{cc}</code>
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
<a href='https://t.me/stormxvup'>┃ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌</a>
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
    checking_msg = checking_status_format(cc, "Stripe Auth 2th 2th", bin_info)
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
    checking_msg = checking_status_format(cc, "Stripe Auth 2", bin_info)
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

@bot.message_handler(commands=['at'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.at'))
def handle_at(message):
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
    checking_msg = checking_status_format(cc, "Authnet [5$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check CC using the AT function from at.py
    check_result = process_card_at(cc)
    
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

# Add these constants at the top with other configurations
# Update these constants at the top with other configurations
MAX_MASS_CHECK = 10
STATUS_EMOJIS = {
    'APPROVED': '✅',
    'Approved': '✅',
    'DECLINED': '❌',
    'Declined': '❌',
    'CCN': '🟡',
    'ERROR': '⚠️',
    'Error': '⚠️'
}

# Update this function for mass check formatting
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
        # Handle case where status might be in different formats
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

# Add these constants at the top with other configurations
MAX_MASS_CHECK = 10

# Add these handler functions
# Add this import at the top
import concurrent.futures

# Update the mass check handlers
@bot.message_handler(commands=['mchk'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mchk'))
def handle_mchk(message):
    # Save user
    save_user(message.from_user.id)
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
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
        
        # Limit to MAX_MASS_CHECK cards
        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")
        
        # Send immediate processing message
        initial_msg = f"```↯ Starting Mass Stripe Auth Check of {len(cards)} Cards...```"
        status_message = bot.reply_to(message, initial_msg)
        
        # Get gateway from first card quickly
        try:
            first_card_result = check_card(cards[0])
            gateway = first_card_result.get("gateway", "Stripe Auth 2th")
        except:
            gateway = "Stripe Auth 2th"
        
        # Update with proper format
        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                text=initial_processing_msg, parse_mode='HTML')
        except:
            pass
        
        # Start timer
        start_time = time.time()
        
        # Process cards in background thread
        def process_cards():
            try:
                results = []
                
                # Process cards with thread pool for better performance
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    # Submit all card checking tasks
                    future_to_card = {executor.submit(check_card, card): card for card in cards}
                    
                    # Process results as they complete
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
                        
                        # Update progress after each card
                        current_time = time.time() - start_time
                        progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                        try:
                            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                                text=progress_msg, parse_mode='HTML')
                        except:
                            pass
                
                # Final update
                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                        text=final_msg, parse_mode='HTML')
                except Exception as e:
                    bot.send_message(message.chat.id, f"Error updating final message: {str(e)}")
                    
            except Exception as e:
                error_msg = f"Mass check failed: {str(e)}"
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                        text=error_msg, parse_mode='HTML')
                except:
                    bot.send_message(message.chat.id, error_msg)
        
        # Run in background thread
        thread = threading.Thread(target=process_cards)
        thread.start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

@bot.message_handler(commands=['mass'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mass'))
def handle_mass(message):
    # Save user
    save_user(message.from_user.id)
    
    try:
        cards_text = None
        command_parts = message.text.split()
        
        # Check if cards are provided after command
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
        
        # Limit to MAX_MASS_CHECK cards
        if len(cards) > MAX_MASS_CHECK:
            cards = cards[:MAX_MASS_CHECK]
            bot.reply_to(message, f"⚠️ Maximum {MAX_MASS_CHECK} cards allowed. Checking first {MAX_MASS_CHECK} cards only.")
        
        # Send immediate processing message
        initial_msg = f"```↯ Starting Mass Stripe 2 Check of {len(cards)} cards...```"
        status_message = bot.reply_to(message, initial_msg)
        
        # Get gateway from first card quickly
        try:
            first_card_result = process_card_au(cards[0])
            gateway = first_card_result.get("gateway", "Stripe Auth 2")
        except:
            gateway = "Stripe Auth 2"
        
        # Update with proper format
        initial_processing_msg = format_mass_check_processing(len(cards), 0, gateway)
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                text=initial_processing_msg, parse_mode='HTML')
        except:
            pass
        
        # Start timer
        start_time = time.time()
        
        # Process cards in background thread
        def process_cards():
            try:
                results = []
                
                # Process cards with thread pool for better performance
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    # Submit all card checking tasks
                    future_to_card = {executor.submit(process_card_au, card): card for card in cards}
                    
                    # Process results as they complete
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
                        
                        # Update progress after each card
                        current_time = time.time() - start_time
                        progress_msg = format_mass_check(results, len(cards), current_time, gateway, i)
                        try:
                            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                                text=progress_msg, parse_mode='HTML')
                        except:
                            pass
                
                # Final update
                final_time = time.time() - start_time
                final_msg = format_mass_check(results, len(cards), final_time, gateway, len(cards))
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                        text=final_msg, parse_mode='HTML')
                except Exception as e:
                    bot.send_message(message.chat.id, f"Error updating final message: {str(e)}")
                    
            except Exception as e:
                error_msg = f"Mass AU check failed: {str(e)}"
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                                        text=error_msg, parse_mode='HTML')
                except:
                    bot.send_message(message.chat.id, error_msg)
        
        # Run in background thread
        thread = threading.Thread(target=process_cards)
        thread.start()
    
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

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
