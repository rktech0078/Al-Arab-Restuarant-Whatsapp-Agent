# 🕌 Al Arab Restaurant WhatsApp Agent 🍽️

Welcome to the official WhatsApp automation agent for **Al Arab Restaurant, Karachi**! This project enables seamless, AI-powered customer interaction, order management, and menu sharing directly via WhatsApp.

---

## 🚀 Features
- 🤖 **AI Chatbot**: Friendly, festive, and professional replies in Roman Urdu, Urdu, or English
- 📝 **Order Collection**: Step-by-step order taking, summary, and confirmation
- 📋 **Menu & Deals**: Instantly share menu highlights, prices, and special deals
- 🧾 **Receipt Generation**: Auto-generate and send digital receipts
- 📊 **Google Sheets Integration**: Orders are logged for easy management
- 🕒 **Business Info**: Share timings, address, and contact details on request
- 🔒 **Secure & Reliable**: Built with best practices for privacy and uptime

---

## 🛠️ Tech Stack
- **Python 3.8+**
- **Flask** (Webhook server)
- **OpenAI API** (AI replies)
- **WhatsApp Cloud API** (Messaging)
- **Google Sheets API** (Order logging)
- **SQLAlchemy** (Database)

---

## ⚡ Quick Start (Local)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/Al-Arab-Restuarant-Whatsapp-Agent.git
   cd Al-Arab-Restuarant-Whatsapp-Agent
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your `.env` file:**
   - Copy `.env.example` to `.env` (if available) or create `.env` with:
     ```env
     WHATSAPP_CLOUD_TOKEN=your_whatsapp_token
     WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
     OPENAI_API_KEY=your_openai_key
     GOOGLE_SHEETS_CREDENTIALS=your_gspread_json
     SHEET_ID=your_google_sheet_id
     ```
4. **Run the server:**
   ```bash
   python whatsapp/webhook.py
   ```
5. **Expose your local server** (for WhatsApp webhook):
   - Use [ngrok](https://ngrok.com/) or similar:
     ```bash
     ngrok http 5000
     ```
   - Set the webhook URL in WhatsApp Cloud API dashboard.

---

## 🌐 Deploy on Render
1. Push your code to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com/).
3. Set environment variables in the Render dashboard (same as `.env`).
4. Set build & start commands:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python whatsapp/webhook.py`
5. Add a health check endpoint if needed (`/ping`).
6. Set your Render public URL as the WhatsApp webhook.

---

## ⚙️ Environment Variables
| Variable                  | Description                        |
|---------------------------|------------------------------------|
| `WHATSAPP_CLOUD_TOKEN`    | WhatsApp Cloud API token           |
| `WHATSAPP_PHONE_NUMBER_ID`| WhatsApp phone number ID           |
| `OPENAI_API_KEY`          | OpenAI API key                     |
| `GOOGLE_SHEETS_CREDENTIALS` | Google service account JSON string |
| `SHEET_ID`                | Google Sheet ID for order logging  |

---

## 💬 Usage
- Customers message your WhatsApp number.
- The bot greets, shares menu, takes orders, and answers queries.
- Orders and receipts are managed automatically.

---

## 🧑‍💻 Contributing
Pull requests are welcome! For major changes, please open an issue first.

---

## 🙋‍♂️ Support & Contact
- For help, open an issue or contact the restaurant team.
- **Al Arab Restaurant, Karachi**
- 📞 0300-2581719, 0345-3383881, 0333-7857596, 0314-9760610

---

**Enjoy fast, friendly, and festive service with Al Arab Restaurant!** 🎉🍔🍕🥙 