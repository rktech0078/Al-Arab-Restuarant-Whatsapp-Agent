from flask import Flask, request, jsonify
from whatsapp.handler import handle_incoming_message
from config import Config
import threading
import time
import requests
from dotenv import load_dotenv
import pathlib

# Force load .env from project root
env_path = pathlib.Path(__file__).parent.parent.resolve() / ".env"
print("DEBUG: Loading .env from:", env_path)
load_dotenv(dotenv_path=env_path)
import os
print("DEBUG: (webhook.py) WHATSAPP_CLOUD_TOKEN =", os.getenv("WHATSAPP_CLOUD_TOKEN"))
print("DEBUG: (webhook.py) WHATSAPP_PHONE_NUMBER_ID =", os.getenv("WHATSAPP_PHONE_NUMBER_ID"))

app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == Config.VERIFICATION_TOKEN:
            return challenge, 200
        else:
            return 'Verification token mismatch', 403
    try:
        data = request.get_json(force=True)
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages')
        if not messages:
            print('No messages found in webhook payload')
            return jsonify({'status': 'no messages'}), 200
        handle_incoming_message(data)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print('Webhook error:', e)
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

def keep_alive():
    while True:
        try:
            print("Pinging self to stay awake...")
            requests.get("https://whatsapp-cloud-api-success.onrender.com/ping")
        except Exception as e:
            print("Keep-alive ping failed:", e)
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
