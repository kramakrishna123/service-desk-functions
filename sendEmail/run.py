from datetime import timedelta
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, ServiceAccount, \
    EWSDateTime, EWSTimeZone, Configuration, NTLM, CalendarItem, \
    Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, \
    Body, HTMLBody, Build, Version

import exchangelib
import json
import uuid, pymongo, requests,sys
from bson.json_util import dumps
from azure.servicebus import ServiceBusService, Message, Queue
from hashlib import md5
import urllib,pprint,os,sys


try:
    credentials = Credentials(username='@.com', password='$')
    account = Account(primary_smtp_address='@.com', credentials=credentials,autodiscover=True, access_type=DELEGATE)
    print ('Connected to email server')
    client = pymongo.MongoClient('mongodb://serivice-desk-store:pMzmGDeCcbMZEJ7hVirY9YEA7NMm6abpGF6oNz32D6MNTqsmdqzvdg3MLVw80eMlztxPP03vxsKxtatgPOiCFg==@serivice-desk-store.documents.azure.com:10255/?ssl=true&replicaSet=globaldb')
    db = client.hilton
    collection  = db.emails
    print ('Connected to cosmosdb/mongodb')
    nttBus = ServiceBusService(service_namespace='ntt-bus',shared_access_key_name='RootManageSharedAccessKey',shared_access_key_value='ak9L18tmI2FssJBIZLz3OCs8U55rcYZaSbwgAR6/B34=')
    print ('Conected to nttbus')
    msg = open(os.environ['doc']).read()
    data = json.loads(msg,strict=False)
    pprint.pprint(data)
except Exception as e:
    print ('Error Connecting to external service' +str(e))
    sys.exit(1)



try:
    client = pymongo.MongoClient('mongodb://serivice-desk-store:pMzmGDeCcbMZEJ7hVirY9YEA7NMm6abpGF6oNz32D6MNTqsmdqzvdg3MLVw80eMlztxPP03vxsKxtatgPOiCFg==@serivice-desk-store.documents.azure.com:10255/?ssl=true&replicaSet=globaldb')
    db = client.hilton
    collection  = db.emails
    print('Connected to mongodb')
    nttBus = ServiceBusService(
        service_namespace='ntt-bus',
        shared_access_key_name='RootManageSharedAccessKey',
        shared_access_key_value='ak9L18tmI2FssJBIZLz3OCs8U55rcYZaSbwgAR6/B34=')
    print('NTT-bus connected')
    msg = open(os.environ['doc']).read()
    data = json.loads(msg,strict=False)
    print (data)
    print('Incoming Email Loaded')
except Exception as e:
    print ('Error while loading state....Exit-1')
    print(str(e))
    sys.exit(1)

#Get the email
item_id = data['item_id']
email = account.inbox.get(item_id=item_id)

# Copy Email 
kwargs = {f.name: getattr(email, f.name) for f in email.supported_fields()}
del(kwargs['attachments'])
reply = exchangelib.Message(**kwargs)
reply.account = account
reply.subject = 'RE: '+ email.subject
reply.consersation_id = email.conversation_id
if email.sender not in reply.to_recipients:
    reply.to_recipients.append(reply.sender)


if data['type'] == 'link_generated':
    link = '<a href ="' + data['url'] +'">here</a>'
    body =  '<html>'
    body += '<body>'
    body += 'Hi! Manager/Service Desk <br/>'
    body += 'Please validate the request ' 
    body += link
    body += '<br/>'

if data['type'] == 'ticket_created':    
    body =  '<html>'
    body += '<body>'
    body += 'Incident ticket ' + data['ticket'] + ' has been created for this issue';
    body += '<br/>'

print(body)
reply.body = HTMLBody(body)
reply.send_and_save()

if(data['type']) == 'ticket_created':
    result = collection.update_one({'caseid':data['caseid']}, {"$set":{'botHasReplied':True,'handoff':True}}, upsert=False)

    #email.is_read = True
    #email.save()
    pass

