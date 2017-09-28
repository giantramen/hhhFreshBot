from __future__ import print_function
import smtplib
import praw
import datetime
import time
import subscriberManager

server=smtplib.SMTP('smtp.gmail.com', 587, None, 30)
server.ehlo()
server.starttls()

with open('gmail_creds.txt') as f:
    credentials = [x.strip().split(':') for x in f.readlines()]

for username,password in credentials:
    server.login(username, password)

def updateSubscriberSeenPosts(phoneNumber, id):
    subscribers = subscriberManager.getSubscribers()
    subscriber = subscribers[phoneNumber]

    subscriber.seenPostIds.append(id)

    subscribers[phoneNumber] = subscriber
    subscriberManager.saveSubscribers(subscribers)

def emailSubscribers():
    reddit = praw.Reddit('hhhBot')
    subreddit = reddit.subreddit("hiphopheads")

    print('Emailing subscribers...' + str(datetime.datetime.now()))
    
    subscribers = subscriberManager.getSubscribers()

    for phoneNumber, subscriber in subscribers.items():

        for submission in subreddit.hot(limit=25):

            if 'fresh' in submission.title.lower() and submission.score >= subscriber.upvoteThreshold and submission.id not in subscriber.seenPostIds:
                    title = submission.title + ' (+' + str(submission.score) + ')'
                    text = 'New [FRESH] post trending right now!\n'

                    server.sendmail('hiphopheadsbot@gmail.com', subscriber.emailAddress, text+title)

                    updateSubscriberSeenPosts(phoneNumber, submission.id)


if __name__ == "__main__":
    while 1:
        try:
            subscriberManager.getAllNewUnsubscribes()
            subscriberManager.addNewSubscribers()
            emailSubscribers()
        except Exception as e:
            print('Error!')
            print(str(e))

        time.sleep(15)