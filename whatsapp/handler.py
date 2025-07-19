import os
import json
import re
from whatsapp.send_message import send_whatsapp_message, send_whatsapp_document
from sheets.google_sheets import append_order_to_sheet, update_order_status_in_sheet
from db.models import Order, SessionLocal, Conversation
from receipts.receipt_generator import generate_receipt
import openai
from openai_agent.ai_reply import get_ai_reply, is_order_confirmation
import time

user_histories = {}
user_languages = {}
user_sessions = {}  # NEW: per-user order state

openai.api_key = os.getenv('OPENAI_API_KEY')

GPT_MODEL = "gpt-4o-mini"

# Helper: Detect language preference or ask
LANG_OPTIONS = ['English', 'Urdu', 'Roman Urdu']
def detect_language(text):
    text_lower = text.lower()
    if 'english' in text_lower or any(word in text_lower for word in ['hello', 'order', 'menu', 'please', 'thanks']):
        return 'English'
    elif 'urdu' in text_lower or any(word in text_lower for word in ['آرڈر', 'کھانا', 'شکریہ', 'مہربانی']):
        return 'Urdu'
    elif 'roman' in text_lower or any(word in text_lower for word in ['kya', 'hai', 'ka', 'mein', 'order', 'biryani', 'shukriya']):
        return 'Roman Urdu'
    return 'Roman Urdu'

def get_user_language(from_number, text):
    # Lock language on first message
    if from_number not in user_languages:
        user_languages[from_number] = detect_language(text)
    return user_languages[from_number]

# Smart AI reply using GPT-4o-mini

def update_order_status(order_id, new_status, from_number=None):
    # Update in DB
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = new_status
            db.commit()
            # Notify user if number provided
            if from_number:
                status_msgs = {
                    'confirm': 'Aapka order confirm ho gaya hai! ✅',
                    'dispatched': 'Aapka order dispatch ho gaya hai! 🛵',
                    'delivered': 'Aapka order deliver ho gaya hai! 🎉',
                    'pending': 'Aapka order abhi pending hai. ⏳'
                }
                msg = status_msgs.get(new_status, f'Aapka order status: {new_status}')
                send_whatsapp_message(from_number, msg)
    except Exception as e:
        print('Order status update error:', e)
    finally:
        db.close()
    # Update in Google Sheet (optional, if you want to sync status)
    # TODO: Implement if needed

def get_ai_reply(message, from_number, system_prompt=None, state='greeting'):
    history = user_histories.get(from_number, [])
    history.append({"role": "user", "content": message})
    history = history[-10:]
    prompt = ""
    if system_prompt:
        prompt += system_prompt + "\n"
    for msg in history:
        prompt += f"{msg['role']}: {msg['content']}\n"
    language = user_languages.get(from_number, 'Roman Urdu')
    # Al Arab Restaurant full context prompt
    al_arab_context = (
        "You are the official WhatsApp assistant for Al Arab Restaurant, Karachi.\n"
        "Your job is to help customers in a friendly, festive, and professional way, using restaurant branding, emojis, and a warm tone.\n"
        "Always mention Al Arab Restaurant in your greetings and replies.\n"
        "Menu highlights: Chicken Shawarma (Rs. 490), Lebanese Shawarma (Rs. 500), Chicken Crispy Shawarma (Rs. 530), Chicken Cheese Shawarma (Rs. 530), Fish Shawarma (Rs. 590), Beef Shawarma (Rs. 460), Beef with Fries Shawarma (Rs. 500), Beef Cheese Shawarma (Rs. 540), Falafel Platter (Rs. 980/650), Falafel Roll (Rs. 250), Chicken Hummus Platter (Rs. 1,999), Beef Hummus Platter (Rs. 1,800), Zinger Burger (Rs. 500), Broast Chest (Rs. 550), Chicken Biryani (Rs. 250/450), Sweet Corn (Rs. 250), Cheezi Potatoes (Rs. 350), 6 Flavour Fries (Rs. 290), Chicken Fried Rice (Rs. 500), Chicken Manchurian with Rice (Rs. 800), Pasta/Lasagna specials.\n"
        "Deals: Pizza combos, Super Deal Rs. 500, Eid/Ramadan specials, daily combos.\n"
        "Timings: Rozana 12:00pm se 3:15am tak.\n"
        "Address: Gulistan-e-Johar, Block 15, Decent Towers, Continental Bakery ke qareeb. Dusra outlet: Alamgir Road, B.M. Society, Sharafabad.\n"
        "Delivery, takeaway, dine-in available.\n"
        "Contact numbers: 0300-2581719, 0345-3383881, 0333-7857596, 0314-9760610.\n"
        "Bread/pita, Arabic sauces, falafel, garlic sauce, etc. sab available hain.\n"
        "If user asks for menu, prices, deals, address, timings, delivery, ya feedback, always answer using above info.\n"
        "If user asks for menu, suggest popular items and prices.\n"
        "If user asks for deals, mention combos and specials.\n"
        "If user asks for address or timing, reply with details.\n"
        "If user asks for delivery, confirm it's available and share contact.\n"
        "If user asks about bread/pita, falafel, sauces, etc., answer from above info.\n"
        "Always use friendly, festive, and Arabic/restaurant-specific style with emojis.\n"
        "If user gives feedback, thank them warmly.\n"
        "If user wants to order, follow the step-by-step order collection as before.\n"
        "If user has already provided any order details (name, address, phone, items, payment), do NOT ask again, just politely confirm.\n"
        "If user gives all details in one message, confirm and save the order, don't ask again.\n"
        "IMPORTANT: Never say 'order confirm ho gaya', 'order placed', 'order confirm kar diya', or any similar phrase UNTIL the user has explicitly replied 'confirm' or given clear confirmation.\n"
        "If all details are present, ONLY send an order summary and ask the user to reply 'confirm' before proceeding.\n"
        "Do NOT say the order is confirmed or placed until the backend has saved it after user confirmation.\n"
    )
    # Conversational, human-like, restaurant-specific prompt
    if state == 'greeting':
        prompt = (
            al_arab_context +
            f"Greet the user warmly, ask about their mood or what they feel like eating today.\n"
            f"Don't ask for order details yet.\n"
            f"Reply in {language}.\n"
        ) + prompt
    elif state == 'order_interest':
        prompt = (
            al_arab_context +
            f"User is interested in ordering. Suggest popular dishes or ask if they'd like to place an order.\n"
            f"Don't ask for details yet, just encourage them.\n"
            f"Reply in {language}.\n"
        ) + prompt
    elif state == 'collecting_details':
        prompt = (
            al_arab_context +
            f"User wants to place an order. Now, politely and step-by-step, ask for order details (name, address, phone, items), one at a time.\n"
            f"If user has already provided any order details, do NOT ask again, just politely confirm.\n"
            f"If user gives all details in one message, confirm and save the order, don't ask again.\n"
            f"Reply in {language}.\n"
        ) + prompt
    else:
        prompt = (
            al_arab_context +
            f"Reply in {language}.\n"
        ) + prompt
    print("[DEBUG] Calling OpenAI API with prompt:", prompt)
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        print("[DEBUG] OpenAI API response:", response)
        reply = response.choices[0].message['content'].strip()
        print("[DEBUG] AI reply:", reply)
        history.append({"role": "assistant", "content": reply})
        user_histories[from_number] = history
        return reply
    except Exception as e:
        print('[DEBUG] OpenAI API error:', e)
        return "Sorry, I am unable to reply right now."

# Smart order extraction using GPT-4o-mini

def extract_field(message, field, language):
    # Use LLM to extract a single field from message
    prompt = f"""
Aap Al Arab Restaurant ke WhatsApp order assistant hain. User ka message {language} mein ho sakta hai. Sirf aur sirf {field} nikaal kar valid JSON mein do. Agar na ho to null return karo.
Example output: {{"{field}": "value"}}
Message: {message}
"""
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[{"role": "system", "content": prompt}]
    )
    raw = response.choices[0].message['content']
    try:
        clean = re.sub(r"^```json|^```|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        return json.loads(clean).get(field)
    except Exception as e:
        print(f'Field extraction error ({field}):', e)
        return None

def handle_incoming_message(data):
    print("[DEBUG] handle_incoming_message called with data:", data)
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages')
        if not messages:
            print("[DEBUG] No messages found in webhook payload")
            return
        msg = messages[0]
        from_number = msg['from']
        # Location message handle
        if msg.get('type') == 'location' and 'location' in msg:
            loc = msg['location']
            address = loc.get('address', '')
            name = loc.get('name', '')
            full_address = f"{address} {name}".strip()
            print(f"[DEBUG] Location received from {from_number}: {full_address}")
            # Save to session
            session = user_sessions.get(from_number, {'name': None, 'address': None, 'phone': None, 'items': None, 'payment_type': None, 'step': 'collecting_details'})
            session['address'] = full_address
            user_sessions[from_number] = session
            send_whatsapp_message(from_number, f"Location mil gayi! Address: {full_address}")
            # Continue normal flow (try to extract other fields, etc.)
            # You may want to trigger the next step here if needed
            # For now, just return to avoid double-processing
            return
        text = msg['text']['body'].strip() if msg.get('type') == 'text' else ''
        print(f"[DEBUG] Incoming message from {from_number}: {text}")

        # --- MENU PDF SEND LOGIC (moved to top, before state machine) ---
        menu_keywords = ['menu', 'menu bhejein', 'menu send', 'menu chahiye', 'menu chahta hoon', 'menu please', 'menu pdf']
        if any(word in text.lower() for word in menu_keywords):
            print(f"[DEBUG] Menu keyword detected in message: {text}")
            menu_pdf_path = 'menu.pdf' if os.path.exists('menu.pdf') else os.path.join('whatsapp', 'menu.pdf')
            pdf_sent = False
            if os.path.exists(menu_pdf_path):
                try:
                    send_whatsapp_message(from_number, 'Yeh raha hamara menu! (PDF attached)')
                    pdf_sent = send_whatsapp_document(from_number, menu_pdf_path, caption='Al Arab Restaurant Menu')
                    print(f"[DEBUG] PDF send attempted, success: {pdf_sent}")
                except Exception as e:
                    print('[DEBUG] Menu PDF send error:', e)
                    pdf_sent = False
            if not pdf_sent:
                send_whatsapp_message(from_number, 'Maaf kijiye, menu PDF abhi available nahi hai. Text menu bhej raha hoon.')
                # Only send text menu if PDF failed
                menu_highlights = (
                    "Menu highlights: Chicken Shawarma (Rs. 490), Lebanese Shawarma (Rs. 500), Chicken Crispy Shawarma (Rs. 530), Chicken Cheese Shawarma (Rs. 530), Fish Shawarma (Rs. 590), Beef Shawarma (Rs. 460), Beef Cheese Shawarma (Rs. 540), Falafel Platter (Rs. 980/650), Falafel Roll (Rs. 250), Chicken Hummus Platter (Rs. 1,999), Beef Hummus Platter (Rs. 1,800), Zinger Burger (Rs. 500), Broast Chest (Rs. 550), Chicken Biryani (Rs. 250/450), Sweet Corn (Rs. 250), Cheezi Potatoes (Rs. 350), 6 Flavour Fries (Rs. 290), Chicken Fried Rice (Rs. 500), Chicken Manchurian with Rice (Rs. 800), Pasta/Lasagna specials.\nDeals: Pizza combos, Super Deal Rs. 500, Eid/Ramadan specials, daily combos.\nTimings: Rozana 12:00pm se 3:15am tak.\nAddress: Gulistan-e-Johar, Block 15, Decent Towers, Continental Bakery ke qareeb. Dusra outlet: Alamgir Road, B.M. Society, Sharafabad.\nDelivery, takeaway, dine-in available.\nContact: 0300-2581719, 0345-3383881, 0333-7857596, 0314-9760610."
                )
                send_whatsapp_message(from_number, menu_highlights)
            return
        # Cancel/Prank detection
        if text.lower() in ['cancel', 'galat', 'غلط', 'کینسل']:
            db = SessionLocal()
            try:
                order = db.query(Order).filter(Order.whatsapp_number == from_number).order_by(Order.created_at.desc()).first()
                if order:
                    order.status = 'cancelled'
                    order.notes = (order.notes or '') + ' [User cancelled or reported prank]'
                    db.commit()
                    try:
                        update_order_status_in_sheet(from_number, order.created_at, 'cancelled')
                    except Exception as e:
                        print('Google Sheet cancel update error:', e)
                    send_whatsapp_message(from_number, 'Aapka order cancel kar diya gaya hai. Shukriya!')
                else:
                    send_whatsapp_message(from_number, 'Koi active order nahi mila. Shukriya!')
            except Exception as e:
                print('Order cancel error:', e)
            finally:
                db.close()
            return
        # --- NEW: Receipt/Status request if no active session ---
        session = user_sessions.get(from_number)
        if not session:
            receipt_keywords = ['receipt', 'raseed', 'total', 'bill', 'status', 'order status', 'order ka status', 'order ki raseed']
            if any(word in text.lower() for word in receipt_keywords):
                db = SessionLocal()
                try:
                    order = db.query(Order).filter(Order.whatsapp_number == from_number).order_by(Order.created_at.desc()).first()
                    if order:
                        # Only send receipt if order exists
                        receipt = generate_receipt({
                            'name': order.name,
                            'address': order.address,
                            'phone': order.phone,
                            'items': order.items,
                            'payment_type': order.payment_type,
                            'whatsapp_number': order.whatsapp_number,
                            'status': order.status
                        })
                        if receipt:
                            send_whatsapp_message(from_number, receipt)
                        else:
                            send_whatsapp_message(from_number, 'Aapki order ki raseed abhi available nahi hai.')
                    else:
                        send_whatsapp_message(from_number, 'Koi recent order nahi mila. Pehle order karein!')
                except Exception as e:
                    print('Receipt/status error:', e)
                    send_whatsapp_message(from_number, 'Kuch masla ho gaya, receipt nahi bhej sakte.')
                finally:
                    db.close()
                return
        # --- END NEW ---
        # Language preference (lock on first message)
        language = get_user_language(from_number, text)
        # User session state
        session = user_sessions.get(from_number, {'name': None, 'address': None, 'phone': None, 'items': None, 'payment_type': None, 'step': 'greeting'})
        print(f"[DEBUG] Session state for {from_number}: {session}")
        # State machine progression
        if session['step'] == 'greeting':
            if any(word in text.lower() for word in ['order', 'menu', 'biryani', 'burger', 'shawarma', 'khaana', 'khana', 'dish', 'item', 'pizza', 'rice', 'pulao']):
                session['step'] = 'order_interest'
            else:
                ai_response = get_ai_reply(text, from_number, state='greeting')
                print(f"[DEBUG] AI reply (greeting): {ai_response}")
                send_whatsapp_message(from_number, ai_response or 'Sorry, I am unable to reply right now.')
                user_sessions[from_number] = session
                return
        if session['step'] == 'order_interest':
            if any(word in text.lower() for word in ['haan', 'yes', 'ok', 'theek', 'chalo', 'kar do', 'place', 'confirm']):
                session['step'] = 'collecting_details'
            else:
                ai_response = get_ai_reply(text, from_number, state='order_interest')
                print(f"[DEBUG] AI reply (order_interest): {ai_response}")
                send_whatsapp_message(from_number, ai_response or 'Sorry, I am unable to reply right now.')
                user_sessions[from_number] = session
                return
        # Always try to extract missing fields from every message and AI reply
        if session['step'] == 'collecting_details':
            # Try to extract all fields from current message
            field_error = False
            if not session['name']:
                try:
                    name = extract_field(text, 'name', language)
                    print(f"[DEBUG] Extracted name from user: {name}")
                    if name:
                        session['name'] = name
                except Exception as e:
                    print(f"[DEBUG] Name extraction error: {e}")
                    field_error = True
            if not session['address']:
                try:
                    address = extract_field(text, 'address', language)
                    print(f"[DEBUG] Extracted address from user: {address}")
                    if address:
                        session['address'] = address
                except Exception as e:
                    print(f"[DEBUG] Address extraction error: {e}")
                    field_error = True
            if not session['phone']:
                try:
                    phone = extract_field(text, 'phone', language)
                    print(f"[DEBUG] Extracted phone from user: {phone}")
                    if phone:
                        session['phone'] = phone
                except Exception as e:
                    print(f"[DEBUG] Phone extraction error: {e}")
                    field_error = True
            if not session['items']:
                try:
                    items = extract_field(text, 'items', language)
                    print(f"[DEBUG] Extracted items from user: {items}")
                    if items:
                        session['items'] = items
                except Exception as e:
                    print(f"[DEBUG] Items extraction error: {e}")
                    field_error = True
            if not session['payment_type']:
                try:
                    payment_type = extract_field(text, 'payment_type', language)
                    print(f"[DEBUG] Extracted payment_type from user: {payment_type}")
                    if payment_type:
                        session['payment_type'] = payment_type
                except Exception as e:
                    print(f"[DEBUG] Payment type extraction error: {e}")
                    field_error = True
            # Also try to extract from last AI reply if available
            last_ai = user_histories.get(from_number, [])[-1]['content'] if user_histories.get(from_number, []) else ''
            if last_ai:
                try:
                    if not session['name']:
                        name = extract_field(last_ai, 'name', language)
                        print(f"[DEBUG] Extracted name from AI: {name}")
                        if name:
                            session['name'] = name
                except Exception as e:
                    print(f"[DEBUG] Name extraction error (AI): {e}")
                    field_error = True
                try:
                    if not session['address']:
                        address = extract_field(last_ai, 'address', language)
                        print(f"[DEBUG] Extracted address from AI: {address}")
                        if address:
                            session['address'] = address
                except Exception as e:
                    print(f"[DEBUG] Address extraction error (AI): {e}")
                    field_error = True
                try:
                    if not session['phone']:
                        phone = extract_field(last_ai, 'phone', language)
                        print(f"[DEBUG] Extracted phone from AI: {phone}")
                        if phone:
                            session['phone'] = phone
                except Exception as e:
                    print(f"[DEBUG] Phone extraction error (AI): {e}")
                    field_error = True
                try:
                    if not session['items']:
                        items = extract_field(last_ai, 'items', language)
                        print(f"[DEBUG] Extracted items from AI: {items}")
                        if items:
                            session['items'] = items
                except Exception as e:
                    print(f"[DEBUG] Items extraction error (AI): {e}")
                    field_error = True
                try:
                    if not session['payment_type']:
                        payment_type = extract_field(last_ai, 'payment_type', language)
                        print(f"[DEBUG] Extracted payment_type from AI: {payment_type}")
                        if payment_type:
                            session['payment_type'] = payment_type
                except Exception as e:
                    print(f"[DEBUG] Payment type extraction error (AI): {e}")
                    field_error = True
            if field_error:
                send_whatsapp_message(from_number, 'Maaf kijiye, mujhe aapka message sahi samajh nahi aaya. Thoda clearly likh dein, please.')
                user_sessions[from_number] = session
                return
            # Now check which required fields are still missing
            required_missing = []
            if not session['name']:
                required_missing.append('name')
            if not session['items']:
                required_missing.append('items')
            if not session['address']:
                required_missing.append('address')
            if not session['phone']:
                required_missing.append('phone')
            # If any required field missing, ask only that one (in loving style)
            prompts = {
                'name': 'Aapka naam share kar dein, taki order confirm ho sake! 😊',
                'address': 'Delivery address likh dein ya WhatsApp ka location button use kar ke apni location share kar dein! 🏠📍',
                'phone': 'Aapka contact number mil sakta hai, taki rider aap se raabta kar sake? 📞',
                'items': 'Aap kya order karna chahenge? (item aur quantity likhein) 🍽️',
            }
            if required_missing:
                ai_response = get_ai_reply(text, from_number, state='collecting_details')
                print(f"[DEBUG] AI reply (collecting_details): {ai_response}")
                send_whatsapp_message(from_number, prompts[required_missing[0]])
                user_sessions[from_number] = session
                return
            # All required fields present, send summary for confirmation
            summary = f"Aapka order summary:\n- Naam: {session['name'] if session['name'] else 'N/A'}\n- Item: {session['items']}\n- Address: {session['address']}\n- Phone: {session['phone']}\n- Payment: {session['payment_type'] if session['payment_type'] else 'N/A'}\nAgar sab theek hai to 'confirm' likhein, warna jo galat hai woh batayein."
            send_whatsapp_message(from_number, summary)
            session['step'] = 'confirming_order'
            user_sessions[from_number] = session
            return
        # Confirmation step: wait for user to reply 'confirm'
        if session.get('step') == 'confirming_order':
            try:
                confirmed = is_order_confirmation(text)
            except Exception as e:
                print('[DEBUG] LLM confirmation error:', e)
                confirmed = False
            if confirmed:
                print(f"[DEBUG] Attempting to save order: {session}")
                try:
                    row = [
                        session['name'] if session['name'] else 'N/A',
                        session['address'],
                        session['phone'],
                        json.dumps(session['items']),
                        session['payment_type'] if session['payment_type'] else 'N/A',
                        '',  # notes
                        from_number
                    ]
                    append_order_to_sheet(row, status='pending')
                    print('[DEBUG] Order saved to Google Sheet.')
                except Exception as e:
                    print('Google Sheet save error:', e)
                db = SessionLocal()
                try:
                    db_order = Order(
                        name=session['name'] if session['name'] else 'N/A',
                        address=session['address'],
                        phone=session['phone'],
                        payment_type=session['payment_type'] if session['payment_type'] else 'N/A',
                        whatsapp_number=from_number,
                        items=json.dumps(session['items']),
                        notes='',
                        status='pending'
                    )
                    db.add(db_order)
                    db.commit()
                    print('[DEBUG] Order saved to database.')
                except Exception as e:
                    print('Database save error:', e)
                    import traceback
                    traceback.print_exc()
                    print('Order data:', session)
                finally:
                    db.close()
                # Only now send the confirmation message
                confirm_msg = f"Shukriya! Aapka order confirm ho gaya hai. Al Arab Restaurant se kuch hi dair mein aapka order deliver ho jayega! \U0001F357\U0001F69A\u2728\nAapka order yeh address par deliver hoga: {session['address']} \U0001F3E0\nAgar yeh address galat hai ya aapne order nahi diya, to reply karein: 'Cancel' ya 'Galat'."
                send_whatsapp_message(from_number, confirm_msg)
                receipt = generate_receipt({**session, 'whatsapp_number': from_number})
                if receipt:
                    send_whatsapp_message(from_number, receipt)
                # Clear session after order
                user_sessions.pop(from_number, None)
            else:
                send_whatsapp_message(from_number, "Agar sab theek hai to 'confirm' ya koi bhi positive jawab dein (jaise 'haan', 'ok', 'theek hai', 'yes', etc.), warna jo galat hai woh batayein.")
            return
        else:
            user_sessions[from_number] = session
    except Exception as e:
        print('Error in handle_incoming_message:', e) 