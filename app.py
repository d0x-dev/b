import telebot
import requests
import json
import time
from telebot.types import Message
import threading

#====================Gateway Files===================================#
from chk import check_card 
from au import process_card_au
from at import process_card_at
from vbv import check_vbv_card 
from py import check_paypal_card
from qq import check_qq_card
#====================================================================#

# Bot token 
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

def get_bin_info(bin_number):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_number}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Convert the API response to a consistent format
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐫𝐚𝐧𝐝 ➳ {bin_info.get('brand', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ➳ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐁𝐚𝐧𝐤 ⌁ {bin_info.get('bank', 'UNKNOWN')}
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⌁ {bin_info.get('country', 'UNKNOWN')} {bin_info.get('country_flag', '')}
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

# Add this function for mass check while checking format
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
        initial_msg = f"<pre>↯ Starting Mass Stripe Auth Check of {len(cards)} Cards... </pre>"
        status_message = bot.reply_to(message, initial_msg, parse_mode='HTML')

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
        initial_msg = f"<pre>↯ Starting Mass Stripe Auth Check of {len(cards)} Cards... </pre>"
        status_message = bot.reply_to(message, initial_msg, parse_mode='HTML')

        
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

# Add this function for mass AT check
def process_mass_at_check(cards):
    results = []
    for card in cards:
        try:
            result = process_card_at(card)
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
                'gateway': 'Authnet [5$]'
            })
    return results

# Add this handler for mass AT check command
@bot.message_handler(commands=['mat'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mat'))
def handle_mat(message):
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
        initial_msg = f"🚀 Starting mass AT check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)
        
        # Get gateway from first card quickly
        try:
            first_card_result = process_card_at(cards[0])
            gateway = first_card_result.get("gateway", "Authnet [5$]")
        except:
            gateway = "Authnet [5$]"
        
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
                    future_to_card = {executor.submit(process_card_at, card): card for card in cards}
                    
                    # Process results as they complete
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
                error_msg = f"Mass AT check failed: {str(e)}"
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


# Add these handler functions
@bot.message_handler(commands=['vbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.vbv'))
def handle_vbv(message):
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
    checking_msg = checking_status_format(cc, "3DS Lookup", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check VBV status
    check_result = check_vbv_card(cc)
    
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
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                             text=response_text, parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

@bot.message_handler(commands=['mvbv'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mvbv'))
def handle_mvbv(message):
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
        initial_msg = f"🚀 Starting mass VBV check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)
        
        # Gateway for VBV is always "3DS Lookup"
        gateway = "3DS Lookup"
        
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
                
                # Process cards sequentially (VBV check is fast and doesn't need threading)
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
                error_msg = f"Mass VBV check failed: {str(e)}"
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

# Add PayPal command handler
@bot.message_handler(commands=['py'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.py'))
def handle_py(message):
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
    checking_msg = checking_status_format(cc, "Paypal [0.1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check PayPal status
    check_result = check_paypal_card(cc)
    
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
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                             text=response_text, parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

# Add mass PayPal command handler
@bot.message_handler(commands=['mpy'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mpy'))
def handle_mpy(message):
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
        initial_msg = f"🚀 Starting mass PayPal check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)
        
        # Gateway for PayPal
        gateway = "Paypal [0.1$]"
        
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
                
                # Process cards sequentially
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
                error_msg = f"Mass PayPal check failed: {str(e)}"
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
        
# Add QQ command handler
@bot.message_handler(commands=['qq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.qq'))
def handle_qq(message):
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
    checking_msg = checking_status_format(cc, "Stripe Square [0.20$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check Stripe Square status
    check_result = check_qq_card(cc)
    
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
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                             text=response_text, parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

# Add mass QQ command handler
@bot.message_handler(commands=['mqq'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mqq'))
def handle_mqq(message):
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
        initial_msg = f"🚀 Starting mass Stripe Square check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)
        
        # Gateway for Stripe Square
        gateway = "Stripe Square [0.20$]"
        
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
                
                # Process cards sequentially
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
                error_msg = f"Mass Stripe Square check failed: {str(e)}"
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

# Add this import at the top
from cc import check_cc_card

# Add CC command handler
@bot.message_handler(commands=['cc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.cc'))
def handle_cc(message):
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
    checking_msg = checking_status_format(cc, "Site Based [1$]", bin_info)
    status_message = bot.reply_to(message, checking_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check Site Based status
    check_result = check_cc_card(cc)
    
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
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                             text=response_text, parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')

# Add mass CC command handler
@bot.message_handler(commands=['mcc'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.mcc'))
def handle_mcc(message):
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
        initial_msg = f"🚀 Starting mass Site Based check of {len(cards)} cards..."
        status_message = bot.reply_to(message, initial_msg)
        
        # Gateway for Site Based
        gateway = "Site Based [1$]"
        
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
                
                # Process cards sequentially
                for i, card in enumerate(cards, 1):
                    try:
                        result = check_cc_card(card)
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
                error_msg = f"Mass Site Based check failed: {str(e)}"
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

# Add this import at the top with other imports
import re

# Add this function to handle the gate command
def check_gate_url(url):
    """
    Check a URL for payment gateways, captcha, and other security features
    """
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

        # Main checking logic
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

# Add this function to format the gate check result
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    
    # Format payment gateways as string
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗢𝗧𝗔𝗟 𝗧𝗜𝗠𝗘 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

# Add this handler for the gate command
@bot.message_handler(commands=['gate'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.gate'))
def handle_gate(message):
    # Save user
    save_user(message.from_user.id)
    
    # Extract URL from message
    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide a URL to check. Example: /gate https://example.com")
        return
    
    url = command_parts[1]
    
    # Get user info
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    
    # Send processing message
    processing_msg = f"<a href='https://t.me/stormxvup'>🔍 Checking URL: {url}</a>"
    status_message = bot.reply_to(message, processing_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Check URL
    result = check_gate_url(url)
    
    # Calculate time taken
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    
    # Format and send final response
    response_text = format_gate_result(result, mention, user_status, time_taken)
    
    # Edit the original message with the final result
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                         text=response_text, parse_mode='HTML')

def format_bin_result(bin_info, bin_number, mention, user_status, time_taken):
    if not bin_info:
        return f"""
<a href='https://t.me/stormxvup'>┏━━━━━━━⍟</a>
<a href='https://t.me/stormxvup'>┃ 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨 ❌</a>
<a href='https://t.me/stormxvup'>┗━━━━━━━━━━━⊛</a>

<a href='https://t.me/stormxvup'>[⸙]</a> 𝐄𝐫𝐫𝐨𝐫 ➳ <code>No information found for BIN: {bin_number}</code>
<a href='https://t.me/stormxvup'>──────── ⸙ ─────────</a>
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐑𝐞𝐪 𝐁𝐲 ⌁ {mention} [ {user_status} ]
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""
    
    # Extract bin information with fallbacks
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
<a href='https://t.me/stormxvup'>[⸙]</a> 𝐃𝐞𝐯 ⌁ ⏤‌‌𝐃𝐚𝐫𝐤𝐛𝐨𝐲
<a href='https://t.me/stormxvup'>[⸙]</a> 𝗧𝗶𝗺𝗲 ⌁ {time_taken} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"""

# Add this handler for the bin command
@bot.message_handler(commands=['bin'])
@bot.message_handler(func=lambda m: m.text and m.text.startswith('.bin'))
def handle_bin(message):
    # Save user
    save_user(message.from_user.id)
    
    # Extract BIN from message
    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Please provide a BIN number. Example: /bin 524534 or .bin 52453444|02|2026")
        return
    
    # Extract BIN from various formats
    input_text = command_parts[1]
    
    # Handle different formats: .bin 52453444|02|2026, .bin 52453444|02|2026|144, .bin 52453444xxx|02|2026|746
    # Extract first 6-8 digits from the input
    bin_number = ""
    for char in input_text:
        if char.isdigit():
            bin_number += char
            if len(bin_number) >= 8:  # Get up to 8 digits
                break
        elif char == '|':  # Stop at pipe character
            break
    
    # Ensure we have at least 6 digits
    if len(bin_number) < 6:
        bot.reply_to(message, "Please provide a valid BIN with at least 6 digits. Example: /bin 524534 or .bin 52453444|02|2026")
        return
    
    # Take first 6-8 digits (most BIN APIs work with 6-8 digits)
    bin_number = bin_number[:8]  # Use first 8 digits max
    
    # Get user info
    user_status = get_user_status(message.from_user.id)
    mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    
    # Send processing message
    processing_msg = f"<a href='https://t.me/stormxvup'>🔍 Checking BIN: {bin_number}</a>"
    status_message = bot.reply_to(message, processing_msg, parse_mode='HTML')
    
    # Start timer
    start_time = time.time()
    
    # Get BIN info using your existing function
    bin_info = get_bin_info(bin_number) or {}
    
    # Calculate time taken
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    
    # Format and send final response
    response_text = format_bin_result(bin_info, bin_number, mention, user_status, time_taken)
    
    # Edit the original message with the final result
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, 
                         text=response_text, parse_mode='HTML')

# Also update your existing get_bin_info function to handle more cases if needed
# Your existing get_bin_info function should work fine

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
