import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
GPT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # fallback to gpt-4o, else gpt-3.5-turbo

# Guardrail system prompt
GUARDRAIL_PROMPT = (
    "Aap sirf 'Al Arab Restaurant' se related sawalon ke jawab dein. "
    "Agar sawal kisi aur topic par ho, to politely mana kar dein ke main sirf Al Arab Restaurant se related sawalon ke jawab de sakta hoon. "
    "Kisi bhi irrelevant ya inappropriate sawal ka jawab na dein. "
    "Jab bhi roman urdu mein jawab dein, sirf wohi alfaaz use karein jo Pakistan mein aam hain. Indian ya kisi aur mulk ke khas lafz (jaise 'swagat', 'namaste', etc.) na use karein. Sirf simple Pakistani roman urdu mein jawab dein."
)

def get_ai_reply(message, system_prompt=None):
    prompt = GUARDRAIL_PROMPT + "\n"
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

def is_order_confirmation(message):
    """
    LLM se poochta hai: Kya yeh message order confirmation hai? Sirf 'yes' ya 'no' mein jawab do.
    """
    prompt = (
        "User ne yeh message bheja hai: '" + message + "'\n"
        "Kya yeh message order confirmation hai? Sirf 'yes' ya 'no' mein jawab dein. "
        "Agar user ne order confirm kiya hai (chahe kisi bhi style mein, jaise 'haan', 'theek hai', 'ok', 'confirm', 'yes', 'g han', etc.), to 'yes' likhein. Agar nahi, to 'no' likhein."
        "Sirf 'yes' ya 'no' return karein, koi aur text nahi."
    )
    try:
        import openai
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        reply = response.choices[0].message['content'].strip().lower()
        return reply == 'yes'
    except Exception as e:
        print('Order confirmation LLM error:', e)
        # Default: not confirmed if error
        return False 