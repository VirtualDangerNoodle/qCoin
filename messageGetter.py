from __future__ import print_function

import base64
import os.path
from bs4 import BeautifulSoup
import warnings
import requests

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


# Retrieves message list with IDs from mail #TODO: Only grab x mails from y date or date range
def get_msgList():
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me').execute()
        message_list = results.get('messages', [])
        id_list = [message['id'] for message in message_list]
        return id_list
    except HttpError as error:
        print(f'An error occurred: {error}')


# Retrieves message body content
def get_msgContent(message_id):
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
                body.append(sender)
        # Turn soup objects into strings, otherwise can't parse
        return body
    except HttpError as error:
        print(f'An error occurred: {error}')


# Take items from URL and extract price
def priceInspector(item_url):
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


for mid in get_msgList():
    print('Processing ID Nº: ' + mid + '\nFrom: ' + get_msgContent(mid)[-1])
    price = 0
    for url in get_msgContent(mid):
        if 'offer' in url:
            price = price + priceInspector(url)
        if 'item' in url:
            price = price + priceInspector(url)
    print('Total price is %s Rub' % price)

# TODO: Send all this data ^ into an Excel file. Have tick marks for products if in inventory/found
