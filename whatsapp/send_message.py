import os
from dotenv import load_dotenv
import pathlib
import time
import requests

# Force load .env from project root
env_path = pathlib.Path(__file__).parent.parent.resolve() / ".env"
load_dotenv(dotenv_path=env_path)

WHATSAPP_CLOUD_TOKEN = os.getenv('WHATSAPP_CLOUD_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

print("[DEBUG] (send_message.py) WHATSAPP_CLOUD_TOKEN:", WHATSAPP_CLOUD_TOKEN)
print("[DEBUG] (send_message.py) WHATSAPP_PHONE_NUMBER_ID:", WHATSAPP_PHONE_NUMBER_ID)

if not WHATSAPP_CLOUD_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
    raise RuntimeError("[ERROR] WhatsApp Cloud API token or phone number ID is missing! Please check your .env file and environment setup.")


def send_whatsapp_message(to, message):
    print(f"[DEBUG] (send_whatsapp_message) Using Token: {WHATSAPP_CLOUD_TOKEN}")
    print(f"[DEBUG] (send_whatsapp_message) Using Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    # Step 1: Send Actual Message (typing indicator removed)
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_CLOUD_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    print(f"[DEBUG] Sending WhatsApp message to: {to} | Message: {message}")
    print(f"[DEBUG] (send_whatsapp_message) URL: {url}")
    print(f"[DEBUG] (send_whatsapp_message) Headers: {headers}")
    print(f"[DEBUG] (send_whatsapp_message) Data: {data}")
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"[DEBUG] WhatsApp API response: {response.status_code} | {response.text}")
        if response.status_code == 200:
            print(f"[CLOUD SEND] To: {to} | Message: {message}")
        else:
            print(f"WhatsApp Cloud API error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"WhatsApp Cloud API exception: {e}")
