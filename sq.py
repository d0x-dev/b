import json
import random
import time
from datetime import datetime

def process_sq_card(cc):
    """
    Process credit card through Square Auth gateway
    Returns: dict with status, response, and gateway
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Square Auth"
            }
        
        card_number, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if len(yy) == 2:
            yy = "20" + yy
        
        exp_month = int(mm)
        exp_year = int(yy)
        
        # ---- Helper: Luhn Algorithm ----
        def luhn_check(card_number: str) -> bool:
            total = 0
            reverse_digits = card_number[::-1]
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            return total % 10 == 0

        # ---- Card brand detection ----
        def detect_brand(card_number):
            if card_number.startswith("4"):
                return "VISA"
            elif card_number.startswith(tuple(str(i) for i in range(51, 56))):
                return "MASTERCARD"
            elif card_number.startswith(("34", "37")):
                return "AMEX"
            elif card_number.startswith("6"):
                return "DISCOVER"
            else:
                return "UNKNOWN"

        def detect_funding(card_number):
            return random.choice(["credit", "debit", "prepaid"])

        # ---- BIN-based latency ----
        def response_delay(card_number):
            bin_prefix = card_number[:6]
            if bin_prefix in ["421783", "400000"]:
                return random.uniform(1.5, 3)
            elif bin_prefix in ["411111", "555555"]:
                return random.uniform(1, 2)
            elif card_number.startswith(("34", "37")):
                return random.uniform(2, 3)
            elif card_number.startswith("6"):
                return random.uniform(1.5, 2.5)
            else:
                return random.uniform(1, 2)

        # ---- BIN forced declines ----
        def bin_forced_error(card_number):
            if card_number.startswith("411111"):
                return "INVALID_CARD", "Issuer declined card"
            elif card_number.startswith("400000"):
                return "CARD_EXPIRED", "Test card expired"
            elif card_number.startswith("422222"):
                return "CVV_FAILURE", "CVV did not match"
            elif card_number.startswith("433333"):
                return "ADDRESS_VERIFICATION_FAILURE", "Postal code mismatch"
            elif card_number.startswith("444444"):
                return "DUPLICATE_CARD", "Card already exists on file"
            elif card_number.startswith("499999"):
                return "INTERNAL_SERVER_ERROR", "Temporary gateway error"
            return None

        # ---- Test card rule (Stripe/Square style) ----
        TEST_BINS = ["411111", "400000", "422222", "424242"]
        def check_test_card(card_number):
            prefix = card_number[:6]
            if prefix in TEST_BINS:
                return {
                    "errors": [{
                        "code": "TEST_CARD_USED",
                        "category": "INVALID_REQUEST",
                        "detail": "Your transaction was in live mode but used a known test card number."
                    }]
                }
            return None

        # Simulate processing delay
        delay = response_delay(card_number)
        time.sleep(delay)

        card_number = card_number.replace(" ", "").replace("-", "")
        stored_cards = []

        # 1. Check known test cards
        test_resp = check_test_card(card_number)
        if test_resp:
            return {
                "status": "DECLINED",
                "response": test_resp["errors"][0]["detail"],
                "gateway": "Square Auth"
            }

        # 2. Basic validation
        if len(card_number) not in [14, 15, 16]:
            return {
                "status": "DECLINED",
                "response": "Invalid card number length",
                "gateway": "Square Auth"
            }
        
        if not luhn_check(card_number):
            return {
                "status": "DECLINED",
                "response": "Invalid card number (Luhn check failed)",
                "gateway": "Square Auth"
            }

        now = datetime.now()
        if exp_month < 1 or exp_month > 12:
            return {
                "status": "DECLINED",
                "response": "Invalid expiry month",
                "gateway": "Square Auth"
            }
        
        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
            return {
                "status": "DECLINED",
                "response": "Card has expired",
                "gateway": "Square Auth"
            }

        # 3. BIN sandbox declines
        forced = bin_forced_error(card_number)
        if forced:
            code, detail = forced
            return {
                "status": "DECLINED",
                "response": detail,
                "gateway": "Square Auth"
            }

        # 4. CVV check
        brand = detect_brand(card_number)
        if brand == "AMEX" and len(cvv) != 4:
            return {
                "status": "DECLINED",
                "response": "Amex CVV must be 4 digits",
                "gateway": "Square Auth"
            }
        elif brand != "AMEX" and len(cvv) != 3:
            return {
                "status": "DECLINED",
                "response": "CVV must be 3 digits",
                "gateway": "Square Auth"
            }
        
        if cvv in ["000", "999", "1234"]:
            return {
                "status": "DECLINED",
                "response": "Blocked CVV code",
                "gateway": "Square Auth"
            }

        # 5. Random distribution (simulate real approval/decline rates)
        chance = random.random()
        
        if chance < 0.65:  # 65% approval rate
            return {
                "status": "APPROVED",
                "response": "Payment Approved",
                "gateway": "Square Auth"
            }
        elif chance < 0.75:  # 10% OTP required
            return {
                "status": "APPROVED_OTP",
                "response": "3D Secure Required",
                "gateway": "Square Auth"
            }
        elif chance < 0.85:  # 10% insufficient funds
            return {
                "status": "APPROVED",
                "response": "Insufficient Funds",
                "gateway": "Square Auth"
            }
        else:  # 15% various declines
            decline_reasons = [
                "Issuer declined transaction",
                "CVV verification failed",
                "Address verification failed",
                "Transaction not permitted",
                "Do not honor"
            ]
            return {
                "status": "DECLINED",
                "response": random.choice(decline_reasons),
                "gateway": "Square Auth"
            }

    except ValueError:
        return {
            "status": "ERROR",
            "response": "Invalid card format. Use: CC|MM|YY|CVV",
            "gateway": "Square Auth"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing error: {str(e)}",
            "gateway": "Square Auth"
        }
