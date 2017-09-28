from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = ('https://www.googleapis.com/auth/gmail.readonly ' + 'https://www.googleapis.com/auth/gmail.modify')
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, 'hhhBot')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def getNumbersToRemove():
    #Checks unread emails, and returns phone numbers of emails sent with the body "stop" or similar

    phoneNumbersToRemove=[]

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    results = service.users().messages().list(userId='me', labelIds='UNREAD').execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        for m in messages:
            message = service.users().messages().get(userId='me', id=m['id'], format='full').execute()

            #mark emails as read, regardless of content
            body = {"removeLabelIds": ["UNREAD"], "addLabelIds": []}
            service.users().messages().modify(userId='me', id=m['id'], body=body).execute()
            for name in message['payload']['headers']:
                if (name['name']=='From'):
                    if (message['snippet'].lower()=='stop' or message['snippet'].lower()=='stop '):
                        emailAddress=(name['value'])
                        phoneNumber=emailAddress.split('@')[0]
                        phoneNumbersToRemove.append(phoneNumber)

    return phoneNumbersToRemove