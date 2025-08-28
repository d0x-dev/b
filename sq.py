import json
import random
import time
from datetime import datetime

def process_sq_card(cc):
    """
    Process credit card through Square Auth gateway
    Returns: dict with status, response, gateway, and code (if applicable)
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "INVALID_FORMAT",
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

        # ---- BIN-based latency (randomized delays) ----
        def response_delay(card_number):
            # Randomly select a delay from a list of possible delays
            possible_delays = [2, 5, 6, 10, 12]
            return random.choice(possible_delays)

        # ---- BIN forced declines ----
        def bin_forced_error(card_number):
            if card_number.startswith("411111"):
                return {"status": "DECLINED", "response": "INVALID_CARD", "gateway": "Square Auth", "code": "INVALID_CARD"}
            elif card_number.startswith("400000"):
                return {"status": "DECLINED", "response": "CARD_EXPIRED", "gateway": "Square Auth", "code": "CARD_EXPIRED"}
            elif card_number.startswith("422222"):
                return {"status": "DECLINED", "response": "CVV_FAILURE", "gateway": "Square Auth", "code": "CVV_FAILURE"}
            elif card_number.startswith("433333"):
                return {"status": "DECLINED", "response": "ADDRESS_VERIFICATION_FAILURE", "gateway": "Square Auth", "code": "ADDRESS_VERIFICATION_FAILURE"}
            elif card_number.startswith("444444"):
                return {"status": "DECLINED", "response": "DUPLICATE_CARD", "gateway": "Square Auth", "code": "DUPLICATE_CARD"}
            elif card_number.startswith("499999"):
                return {"status": "DECLINED", "response": "INTERNAL_SERVER_ERROR", "gateway": "Square Auth", "code": "INTERNAL_SERVER_ERROR"}
            return None

        # ---- Test card rule (Stripe/Square style) ----
        TEST_BINS = ["411111", "400000", "422222", "424242"]

        def check_test_card(card_number):
            prefix = card_number[:6]
            if prefix in TEST_BINS:
                return {
                    "status": "DECLINED",
                    "response": "TEST_CARD_USED",
                    "gateway": "Square Auth",
                    "code": "TEST_CARD_USED"
                }
            return None

        # Simulate processing delay (randomized)
        delay = response_delay(card_number)
        print(f"Processing... (taking {delay} seconds)")
        time.sleep(delay)

        card_number = card_number.replace(" ", "").replace("-", "")

        # 1. Check known test cards
        test_resp = check_test_card(card_number)
        if test_resp:
            return test_resp

        # 2. Check for forced errors
        forced = bin_forced_error(card_number)
        if forced:
            return forced

        # 3. Basic validation
        if len(card_number) not in [14, 15, 16]:
            return {
                "status": "DECLINED",
                "response": "INVALID_CARD_LENGTH",
                "gateway": "Square Auth"
            }

        if not luhn_check(card_number):
            return {
                "status": "DECLINED",
                "response": "INVALID_CARD_NUMBER",
                "gateway": "Square Auth"
            }

        now = datetime.now()
        if exp_month < 1 or exp_month > 12:
            return {
                "status": "DECLINED",
                "response": "INVALID_EXPIRY_MONTH",
                "gateway": "Square Auth"
            }

        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
            return {
                "status": "DECLINED",
                "response": "CARD_EXPIRED",
                "gateway": "Square Auth"
            }

        # 4. CVV check
        brand = detect_brand(card_number)
        if brand == "AMEX" and len(cvv) != 4:
            return {
                "status": "DECLINED",
                "response": "INVALID_CARD_DATA",
                "gateway": "Square Auth"
            }
        elif brand != "AMEX" and len(cvv) != 3:
            return {
                "status": "DECLINED",
                "response": "INVALID_CARD_DATA",
                "gateway": "Square Auth"
            }

        if cvv in ["000", "999", "1234"]:
            return {
                "status": "DECLINED",
                "response": "INVALID_CARD_DATA",
                "gateway": "Square Auth"
            }

        # 5. Deterministic random distribution (10% approval, 90% decline for real cards)
        random.seed(int(card_number[-6:]))  # Use last 6 digits as seed for reproducibility

        chance = random.random()

        if chance < 0.10:  # 10% approval rate
            return {
                "status": "APPROVED",
                "response": "CARD ADDED",
                "gateway": "Square Auth"
            }
        else:  # 90% decline rate
            decline_reasons = [
                "ISSUER_DECLINED",
                "INSUFFICIENT_FUNDS",
                "CVV_VERIFICATION_FAILED",
                "ADDRESS_VERIFICATION_FAILED",
                "TRANSACTION_NOT_PERMITTED",
                "DO_NOT_HONOR",
                "FRAUD_SUSPECTED",
                "CARD_BLOCKED",
                "DAILY_LIMIT_EXCEEDED",
                "INVALID_TRANSACTION"
            ]
            random.seed(int(card_number[-6:]))  # Reset seed for decline reason selection
            return {
                "status": "DECLINED",
                "response": random.choice(decline_reasons),
                "gateway": "Square Auth"
            }

    except ValueError:
        return {
            "status": "ERROR",
            "response": "INVALID_FORMAT",
            "gateway": "Square Auth"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"PROCESSING_ERROR: {str(e)}",
            "gateway": "Square Auth"
        }
