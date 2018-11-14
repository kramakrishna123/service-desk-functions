from datetime import timedelta
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, ServiceAccount, \
    EWSDateTime, EWSTimeZone, Configuration, NTLM, CalendarItem, Message, \
    Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, \
    Body, HTMLBody, Build, Version
import json
import uuid, pymongo, requests,sys
from azure.servicebus import ServiceBusService, Message, Queue
from bson.json_util import dumps
import hashlib 
import urllib


def getContact(mailbox):
    return {'name':mailbox.name, 'email':mailbox.email_address}

def getContacts(mailboxes):

    return [getContact(i) for i in mailboxes]


try:
    credentials = Credentials(username='@.com', password='')
    account = Account(primary_smtp_address='@.com', credentials=credentials,autodiscover=True, access_type=DELEGATE)
    print ('Connected to email server')
    client = pymongo.MongoClient('mongodb://serivice-desk-store:pMzmGDeCcbMZEJ7hVirY9YEA7NMm6abpGF6oNz32D6MNTqsmdqzvdg3MLVw80eMlztxPP03vxsKxtatgPOiCFg==@serivice-desk-store.documents.azure.com:10255/?ssl=true&replicaSet=globaldb')
    db = client.hilton
    collection  = db.emails
    print ('Connected to cosmosdb/mongodb')
    nttBus = ServiceBusService(service_namespace='ntt-bus',shared_access_key_name='RootManageSharedAccessKey',shared_access_key_value='ak9L18tmI2FssJBIZLz3OCs8U55rcYZaSbwgAR6/B34=')
    print ('Conected to nttbus')
except Exception as e:
    print ('Error Connecting to external service' +str(e))
    sys.exit(1)

n=1
unread  = account.inbox.filter(is_read=False).only('sender','to_recipients','cc_recipients','subject','datetime_received','text_body','body','conversation_id','message_id','body').order_by('-datetime_received')[:n]
emails = [i for i in unread]
print(str(len(emails)))
for email in emails:
    try:

        # if data = None => No existing case found.....continue
        data = collection.find_one({"caseid":hashlib.md5(email.conversation_id.id.encode()).hexdigest()})
        if data is not None:
            print ('already have a caseid')
            continue

        doc = {}
        doc['message_id'] = email.message_id
        doc['from'] = getContact(email.sender)
        if email.to_recipients:
            doc['to'] = getContacts(email.to_recipients)
        if email.cc_recipients:
            doc['cc'] = getContacts(email.cc_recipients) 
        doc['subject'] = email.subject.strip().encode('ascii',errors = 'ignore').decode("utf-8")
        doc['text_body'] = email.text_body.encode('ascii',errors = 'ignore').decode("utf-8")
        doc['html_body'] = email.body
        doc['caseid'] = hashlib.md5(email.conversation_id.id.encode()).hexdigest()
        doc['item_id'] = email.item_id
        doc['handoff'] = False
        doc['botHasReplied'] = False
        doc['approved'] = False
        #print docid

        #### To be Or not to be Check

        if 'htnsvcdsk' not in doc['subject'].lower():
            print('Not a service desk email')
            continue
        
        if 're' in doc['subject'][0:3].lower():
            print('it is a reply')
            continue


        #############################

        
        #Send Message to Incoming Queue
        data = doc
        del(data['html_body'])
        event = Message(json.dumps(data))
        nttBus.send_queue_message('htn.incoming.emails', event)
        print ('queue : ' +  email.message_id)
        #Insert into Dd
        docid = collection.insert_one(doc).inserted_id
        print ('dbase : ' +  str(docid))
    except Exception as e:
        print(str(e))
        pass