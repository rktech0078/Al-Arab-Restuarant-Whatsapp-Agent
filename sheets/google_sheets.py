import gspread
from google.oauth2.service_account import Credentials
from config import Config
import datetime

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_INFO = Config.get_google_service_account()

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_ID = Config.GOOGLE_SHEET_ID


def append_order_to_sheet(row, status='pending'):
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.sheet1  # Default: first sheet
    # Check if sheet is empty, if yes, add headings
    if worksheet.row_count == 0 or not worksheet.get_all_values():
        worksheet.append_row(['Name', 'Address', 'Phone', 'Items', 'Payment Type', 'Notes', 'WhatsApp Number', 'Date/Time', 'Status'])
    # Add current date/time and status to row
    now = datetime.datetime.now().strftime('%d-%b-%Y %I:%M %p')
    row = row + [now, status]
    worksheet.append_row(row)


def update_order_status_in_sheet(whatsapp_number, created_at, new_status):
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.sheet1
    all_rows = worksheet.get_all_values()
    # Find the row with matching WhatsApp number and date/time (last match)
    target_row = None
    for idx, row in enumerate(all_rows):
        if len(row) >= 7 and row[6] == whatsapp_number:
            # Compare date/time (created_at) with row[7] (Date/Time)
            if len(row) >= 8 and created_at.strftime('%d-%b-%Y %I:%M %p') == row[7]:
                target_row = idx + 1  # 1-based index for gspread
    if target_row:
        worksheet.update_cell(target_row, 9, new_status)  # 9th column is Status 