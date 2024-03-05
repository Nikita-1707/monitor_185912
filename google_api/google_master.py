import os
import pickle
from typing import List, Optional

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from base64 import urlsafe_b64decode


class GoogleMaster:
    # Request all access (permission to read/send/receive emails, manage the inbox, and more)
    SCOPES = ['https://mail.google.com/']
    TOKEN_FILENAME = os.path.expanduser('~/token.pickle')

    def __init__(
        self,
    ) -> None:
        self._service = self._auth()

    def _auth(self):
        creds = None
        # the file self.TOKEN_FILENAME stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists(self.TOKEN_FILENAME):
            with open(self.TOKEN_FILENAME, 'rb') as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(self.TOKEN_FILENAME, 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def search_messages(self, query):
        result = self._service.users().messages().list(userId='me', q=query).execute()
        messages = []

        if 'messages' in result:
            messages.extend(result['messages'])

        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = self._service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])

        return messages

    def read_message(self, message):
        msg = self._service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        # parts can be the message body, or attachments
        payload = msg['payload']
        headers = payload.get('headers')
        parts = payload.get('parts')

        data = payload.get('body', {}).get('data')
        not_part_text = ''
        if data:
            not_part_text = urlsafe_b64decode(data).decode()

        if headers:
            # this section prints email basic info & creates a folder for the email
            for header in headers:
                name = header.get('name')
                value = header.get('value')
                if name.lower() == 'from':
                    # we print the From address
                    print('From:', value)
                if name.lower() == 'to':
                    # we print the To address
                    print('To:', value)
                if name.lower() == 'subject':
                    print('Subject:', value)
                if name.lower() == 'date':
                    # we print the date when the message was sent
                    print('Date:', value)

        return self._parse_parts(parts) + [not_part_text]

    def read_accepting_email(self, message) -> Optional[str]:
        msg = self._service.users().messages().get(userId='me', id=message['id'], format='full').execute()

        payload = msg['payload']
        data = payload.get('body', {}).get('data')
        if data:
            return urlsafe_b64decode(data).decode()

        return None

    def _parse_parts(
        self,
        parts,
    ) -> List[str]:
        parts = parts or []
        results = []
        for part in parts:

            mimeType = part.get('mimeType')
            body = part.get('body')
            data = body.get('data')
            if part.get('parts'):
                # recursively call this function when we see that a part has parts inside
                self._parse_parts(part.get('parts'))

            if mimeType == 'text/plain':
                # if the email part is text plain
                if data:
                    text = urlsafe_b64decode(data).decode()
                    results.append(text)

            else:
                continue

        return results
