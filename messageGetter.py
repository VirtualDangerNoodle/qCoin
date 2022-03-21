from __future__ import print_function

import base64
import os.path
from bs4 import BeautifulSoup
import warnings
import requests
import xlsxwriter

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

warnings.filterwarnings('ignore', category=UserWarning, module='bs4')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.labels']


"Auth flow + Saves credentials in json"
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())


def get_msgList():
    # Retrieves msg ID list from 'orders' inbox
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds='Label_7937775743692656712').execute()
        message_list = results.get('messages', [])
        id_list = [message['id'] for message in message_list]
        return id_list
    except HttpError as error:
        print(f'An error occurred: {error}')



def get_msgContent(message_id):
    # Retrieves message body + header
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().get(userId='me', id=message_id, format='full').execute()   # JSON dict

        payload = results['payload']
        headers = payload['headers']
        # Get the body and decode it with base 64decoder
        parts = payload.get('parts')[0]
        data = parts['body']['data']
        data = data.replace('-', '+').replace('_', '/')
        decoded_msg = base64.b64decode(data)
        # Parse resulting lxml with Bs4
        soup = BeautifulSoup(decoded_msg, 'lxml')
        body = soup.get_text().split()
        for h in headers:
            if h['name'] == 'From':
                sender = h['value']
                #body.append(sender)
        return body, sender
    except HttpError as error:
        print(f'An error occurred: {error}')


def priceInspector(item_url):
    # Take items from URL and scrape price
    try:
        page = requests.get(item_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        if 'meshok.net' in item_url:
            results = soup.find(id='gInfo')
            item_price = float(results.find('b', itemprop='price').contents[-1])
            return item_price
        elif 'auction.ru' in item_url:
            results = soup.find('span', class_='price')
            item_price = float(results.text.strip())
            return item_price
        else:
            pass

    except HttpError as error:
        print(f'An error occurred: {error}')

# ..MAIN..

workbook = xlsxwriter.Workbook('/home/snek/Desktop/Test619.xlsx')

for msg_id in get_msgList():

    total = 0
    row = 5
    col = 1
    msg_body, msg_header = get_msgContent(msg_id)
    c_name = ' '.join(msg_header.split()[:-1])
    worksheet = workbook.add_worksheet('%s - Nº %s' % (c_name, msg_id[-4:]))

    worksheet.write('B2', 'Client Name')
    worksheet.write('B3', 'Order ID')
    worksheet.write('B4', 'Total')
    worksheet.write('B5', 'Item')
    worksheet.write('C5', 'Price')

    for msg_url in msg_body:
        if 'https:' not in msg_url:
            del msg_url
        else:
            price = priceInspector(msg_url)
            total = total + price

            worksheet.write('C2', c_name)
            worksheet.write('C3', msg_id)

            worksheet.write_string(row, col, msg_url)
            worksheet.write_number(row, col + 1, price)
            row += 1
    worksheet.write('C4', total)
workbook.close()

# TODO: Send all this data ^ into an Excel file. Have tick marks for products if in inventory/found

