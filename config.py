import os
from dotenv import load_dotenv
import json

load_dotenv()
print("DEBUG: WHATSAPP_CLOUD_TOKEN (config.py) =", os.getenv("WHATSAPP_CLOUD_TOKEN"))

class Config:
    # WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    WHATSAPP_CLOUD_TOKEN = os.getenv('WHATSAPP_CLOUD_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
    
    @staticmethod
    def get_google_service_account():
        # Securely load service account JSON from environment variable
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError('GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set!')
        return json.loads(service_account_json) 