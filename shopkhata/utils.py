"""
shopkhata/utils.py — Helper utilities for ShopKhata.
"""
import re
import uuid
from datetime import datetime
from urllib.parse import quote


def generate_txn_id(prefix='TXN'):
    """Generate a unique transaction ID with prefix."""
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"


def format_currency(amount):
    """Format numeric amount into Indian Rupee string."""
    try:
        val = float(amount)
        return f"₹{val:,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def today_str():
    """Return today's date formatted as YYYY-MM-DD."""
    return datetime.today().strftime('%Y-%m-%d')


def validate_phone(phone):
    """Validate 10-digit Indian phone number (starts with 6-9)."""
    if not phone:
        return True
    return bool(re.match(r'^[6-9]\d{9}$', str(phone).strip()))


def format_date(date_str):
    """Format YYYY-MM-DD or ISO timestamp into readable string."""
    if not date_str:
        return '—'
    try:
        clean = date_str.split('T')[0].split(' ')[0]
        dt = datetime.strptime(clean, '%Y-%m-%d')
        return dt.strftime('%d %b %Y')
    except Exception:
        return date_str


def get_whatsapp_link(phone, customer_name, balance, shop_name='Our Shop'):
    """Generate a WhatsApp click-to-chat URL with polite Hindi/English reminder."""
    if not phone:
        return None
    clean_phone = re.sub(r'\D', '', str(phone))
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    message = (
        f"Namaste {customer_name} ji 🙏,\n\n"
        f"This is a gentle reminder from *{shop_name}* regarding your pending shop credit (Khata) "
        f"amount of *₹{balance:,.2f}*.\n\n"
        f"Kindly clear the dues at your earliest convenience.\n"
        f"Thank you for your continued support! 🏪"
    )
    return f"https://wa.me/{clean_phone}?text={quote(message)}"
