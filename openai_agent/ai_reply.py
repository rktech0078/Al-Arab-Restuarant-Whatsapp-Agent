import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
GPT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # fallback to gpt-4o, else gpt-3.5-turbo

def get_ai_reply(message, system_prompt=None):
    prompt = ""
    if system_prompt:
        prompt += system_prompt + "\n"
    prompt += message
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print('OpenAI API error:', e)
        return "Sorry, I am unable to reply right now." 