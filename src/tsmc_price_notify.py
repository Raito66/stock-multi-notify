import os
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Setting up the Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = service_account.Credentials.from_service_account_info(
    json.loads(os.environ['GOOGLE_SHEETS_CREDENTIALS']), scopes=SCOPES)

# Accessing Google Sheets
SPREADSHEET_ID = os.environ['GOOGLE_SHEET_ID']

def get_sheets_service():
    return build('sheets', 'v4', credentials=CREDS)

# Load history from Google Sheets
def load_history_from_sheets():
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1').execute()
    return result.get('values', [])

# Save data to Google Sheets
def save_to_sheets(data):
    service = get_sheets_service()
    sheet = service.spreadsheets()
    values = [data]
    body = {'values': values}
    sheet.values().append(spreadsheetId=SPREADSHEET_ID, range='Sheet1', body=body, valueInputOption='RAW').execute()

# Auto cleanup old data beyond 60 days
def cleanup_old_data(history):
    threshold_date = datetime.utcnow() - timedelta(days=60)
    return [entry for entry in history if datetime.strptime(entry[0], '%Y-%m-%d') > threshold_date]

# Calculate moving averages
def calculate_ma(data, days):
    return sum(data[-days:]) / days if len(data) >= days else None

# Analyze trend and get smart suggestions
def analyze_trend(history):
    prices = [float(entry[1]) for entry in history]
    ma5 = calculate_ma(prices, 5)
    ma20 = calculate_ma(prices, 20)
    ma60 = calculate_ma(prices, 60)
    suggestion = "Hold"  # Placeholder for actual suggestion logic
    return ma5, ma20, ma60, suggestion

# Smart buy/sell suggestions
def get_smart_suggestion(history):
    ma5, ma20, ma60, suggestion = analyze_trend(history)
    return {'ma5': ma5, 'ma20': ma20, 'ma60': ma60, 'suggestion': suggestion}

# Main function
def main():
    history = load_history_from_sheets()
    cleaned_history = cleanup_old_data(history)
    price_data = [datetime.utcnow().strftime('%Y-%m-%d'), 100.0, 0, 0, 0, datetime.utcnow().isoformat()]  # Example data
    save_to_sheets(price_data)
    suggestions = get_smart_suggestion(cleaned_history)
    print(suggestions)
