import datetime

def generate_receipt(order):
    now = datetime.datetime.now().strftime('%d-%b-%Y %I:%M %p')
    items_list = order.get('items', [])
    if isinstance(items_list, str):
        import json
        try:
            items_list = json.loads(items_list)
        except:
            items_list = []
    items_str = ''
    if items_list:
        for item in items_list:
            name = item.get('name', 'Item')
            qty = item.get('quantity', 1)
            items_str += f"- {qty} x {name}\n"
    else:
        return None  # No items, don't send receipt
    payment_type = order.get('payment_type', '').strip()
    if not payment_type:
        return None  # No payment type, don't send receipt
    receipt = f"""
Al-ARAB Restaurant 🕌

Name: {order.get('name', '')} 🧑
Address: {order.get('address', '')} 🏠
Phone: {order.get('phone', '')} 📞
WhatsApp: {order.get('whatsapp_number', '')} 💬

Date/Time: {now} ⏰

--- Order Summary ---
{items_str}

Payment Type: {payment_type} 💰

---

Shukriya! 💖 Umeed hai aapko hamari service pasand aayi! 🙌 Please visit again. 😊👍
"""
    return receipt