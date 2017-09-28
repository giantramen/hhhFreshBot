from __future__ import print_function
import re
import smtplib
import os
import httplib2
import pickle
import gmailReader
from classes.subscriber import Subscriber

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

server=smtplib.SMTP('smtp.gmail.com', 587, None, 30)
server.ehlo()
server.starttls()

with open('gmail_creds.txt') as f:
    credentials = [x.strip().split(':') for x in f.readlines()]

for username,password in credentials:
    server.login(username, password)

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'HHHBot'
SPREADSHEET_ID = '1HlQYa4FoJKX9ytXgD8Dobr1DxY_0GDfMh-r3TW_dsfg'

#indexing for google sheets
TIMESTAMP_INDEX=0
PHONE_NUMBER_INDEX=1
CARRIER_INDEX=2
UPVOTE_THRESHOLD_SHEETS_INDEX=3


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
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


## Remove Subscribers ##################################################################################################


def getNewUnsubscribesFromForm():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    rangeName = 'Unsubscribers!A2:B'
    result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for i, row in enumerate(reversed(values)):
            rowNumber = len(values)-i
            if getLatestUnsubscribeIndex() < rowNumber:
                phoneNumber = row[PHONE_NUMBER_INDEX].replace("-", "")
                unsubscribePhoneNumber(phoneNumber)
            else:
                break
            updateLatestUnsubscribeIndex(len(values))


def getNewUnsubscribesFromMail():
    phoneNumbers = gmailReader.getNumbersToRemove()
    for number in phoneNumbers:
        unsubscribePhoneNumber(number)


def getAllNewUnsubscribes():
    getNewUnsubscribesFromForm()
    getNewUnsubscribesFromMail()


def updateLatestUnsubscribeIndex(index):
    pickle.dump(index, open("latest_unsubscribe_index.pickle", "wb"))


def getLatestUnsubscribeIndex():
    if os.stat('latest_unsubscribe_index.pickle').st_size == 0:
        return 0
    return pickle.load(open("latest_unsubscribe_index.pickle", "rb"))


def unsubscribePhoneNumber(phoneNumber):
    subscribers = getSubscribers()
    print('unsubscribing ' + phoneNumber)
    subscribers.pop(phoneNumber, None)
    saveSubscribers(subscribers)


## New Subscribers #####################################################################################################


def addNewSubscribers():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    rangeName = 'Subscribers!A2:D'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for i, row in enumerate(reversed(values)):
            rowNumber = len(values) - i
            if getLatestSubscriberIndex() < rowNumber:
                phoneNumber = row[PHONE_NUMBER_INDEX].replace("-", "")
                carrier = row[CARRIER_INDEX]
                upvoteThreshold = int(re.findall('\d+', row[UPVOTE_THRESHOLD_SHEETS_INDEX])[0])
                email = getEmailAddress(phoneNumber, carrier)
                createSubscriber(phoneNumber, carrier, email, upvoteThreshold)
            else:
                break

        updateLatestSubscriberIndex(len(values))


def getEmailAddress(phoneNumber, carrier):
    if carrier == 'AT&T':
        return phoneNumber + '@mms.att.net'
    if carrier == 'Verizon':
        return phoneNumber + '@vzwpix.com'
    if carrier == 'Sprint':
        return phoneNumber + '@pm.sprint.com'
    if carrier == 'T-Mobile':
        return phoneNumber + '@tmomail.net'
    if carrier == 'Virgin Mobile':
        return phoneNumber + '@vmpix.com'
    if carrier == 'U.S. Cellular':
        return phoneNumber + '@mms.uscc.net'
    if carrier == 'Boost Mobile':
        return phoneNumber + '@myboostmobile.com'


def getLatestSubscriberIndex():
    if os.stat('latest_subscriber_index.pickle').st_size == 0:
        return 0
    return pickle.load(open("latest_subscriber_index.pickle", "rb"))


def updateLatestSubscriberIndex(index):
    pickle.dump(index, open("latest_subscriber_index.pickle", "wb"))


def createSubscriber(phoneNumber, carrier, email, upvoteThreshold):
    subscribers = getSubscribers()

    newSubscriber = Subscriber()
    newSubscriber.phoneNumber = phoneNumber
    newSubscriber.carrier = carrier
    newSubscriber.emailAddress = email
    newSubscriber.upvoteThreshold = upvoteThreshold

    print("adding/updating subscriber " + phoneNumber)
    text = 'Welcome to the /r/HipHopHeads [FRESH] Bot! Text STOP to quit'
    server.sendmail('hiphopheadsbot@gmail.com', email, text)

    subscribers[phoneNumber] = newSubscriber

    saveSubscribers(subscribers)


## General functions ###################################################################################################
def getSubscribers():
    try:
        subscribers = pickle.load(open("subscribers.pickle", "rb"))
    except:  # if the file is empty, i.e. running script for first time
        subscribers = {}
    return subscribers


def saveSubscribers(subscribers):
    pickle.dump(subscribers, open("subscribers.pickle", "wb"), pickle.HIGHEST_PROTOCOL)