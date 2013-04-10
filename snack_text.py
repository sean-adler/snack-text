## Sean Adler ##

import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
from twilio.rest import TwilioRestClient
import twilio.twiml
from flask import Flask, request
import threading
import os
from ConfigParser import ConfigParser


PARSER = ConfigParser()
PARSER.read('app.cfg')
ACCOUNT_SID = PARSER.get('twilio', 'ACCOUNT_SID')
AUTH_TOKEN = PARSER.get('twilio', 'AUTH_TOKEN')

CLIENT = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

APP = Flask(__name__)

NUMBERS = set()  # Set of phone numbers we've gathered

def get_snack_msg(day):
    r = requests.get('http://www.cafebonappetit.com/menu/your-cafe/collins-cmc')
    soup = BeautifulSoup(r.text)

    today_div = soup.find('div', class_='date', id='menu-date-%d' % day)
    today_table = today_div.findNext('table')
    snack_tag = today_table.findAll('td', class_='description')[-1]
    return snack_tag.strong.text

def send_text(number, message):
    CLIENT.sms.messages.create(to=number,
                               from_='+18566725567',
                               body=message)

def send_mass_text(textfile):
    """Could save all numbers to textfile, or just use raw Python set."""
    with open(textfile, 'r') as f:
        for number in f:
            send_text(number)

def its_time():
    now = datetime.now()
    hour = now.hour
    second = now.second
    #return hour == 22 and second == 0
    return hour == 11

def main():
    global NUMBERS
    texted_today = False
    
    while True:
        hour = datetime.now().hour
        today = date.weekday(date.today()) + 1  ## Add 1 b/c of Collins HTML
        if hour == 0:
            texted_today = False  ## Reset at midnight
        
        if not texted_today and today in [1,2,3,4] and its_time():
            snack_msg = "Snack tonight is: %s" % get_snack_msg(today)
            for number in NUMBERS:
                send_text(number, snack_msg)
            texted_today = True

def start_loop():
    t = threading.Thread(target=main)
    t.start()

start_loop()

@APP.route('/', methods=['GET'])
def inc_text():    
    from_number = request.args.get('From')
    body = request.args.get('Body')

    if from_number is None or body is None:
        return str(NUMBERS)
    
    if body == 'UNSUB' and from_number in NUMBERS:
        NUMBERS.remove(from_number)
        send_text(from_number,
                  "You've been unsubscribed from the Snack Text.")

    if body == 'GIMME SNAX' and from_number not in NUMBERS:
        NUMBERS.add(from_number)
        send_text(from_number,
                  "You've been added to the Snack Text!")

    return str(NUMBERS)
    
def deploy(heroku=True):
    """Simple deploy script -- we use different host/port values depending on
       if we want to test this locally, or actually push it to Heroku."""
    if heroku == True:
        if __name__ == '__main__':
            ## Bind to PORT if defined, otherwise default to 5000.
            port = int(os.environ.get('PORT', 5000))
            APP.run(host='0.0.0.0', port=port)
    else:
        ## We run the app locally:
        if __name__ == '__main__':
            APP.run(debug=True)


deploy(heroku=True)
