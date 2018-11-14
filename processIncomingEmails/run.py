import numpy as np
import spacy
import helper as fx
import json
import uuid, pymongo, requests, sys, json, os
from azure.servicebus import ServiceBusService, Message, Queue
from bson.json_util import dumps, loads
from hashlib import md5
import urllib

req = {}

req['messaging.outlook.access'] = 'Messaging Generic Request'
req['messaging.email.forwarding'] = 'Messaging Generic Request'
req['intel.generic'] = 'Intel Generic Request'

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
    print ('Error while loading state....Exit-1 : ' + str(e))
    sys.exit(1)



#Fix String data Type
text_body = data['text_body'].encode('ascii',errors = 'ignore').decode()
subject = data['subject'].encode('ascii',errors = 'ignore').decode()
frm = data['from']['name']

#Get Email Data structure and intent
emails = fx.process(text_body,frm,subject)
intent = fx.getIntent(emails)

#Prepare the doc
doc = {}
doc['emails'] = emails
doc['intent'] = intent
if (intent.get('intent')):
    doc['request'] = req[intent['intent']]


#update the collection
result = collection.update_one({'caseid':data['caseid']}, {"$set":doc}, upsert=False)

#send Message to reply queue
url = "https://sd-ui.azurewebsites.net/task/"+data['caseid']
msg= {}
msg['item_id'] = data['item_id']
msg['type'] = 'link_generated'
msg['url'] = url
event = Message(json.dumps(msg))
nttBus.send_queue_message('htn.reply.email', event)
