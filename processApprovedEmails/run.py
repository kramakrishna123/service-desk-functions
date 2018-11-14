import uuid, pymongo, requests, sys, json, os
from azure.servicebus import ServiceBusService, Message, Queue
from bson.json_util import dumps, loads
from hashlib import md5
import urllib,pprint

#Service Now Configuration
snow_url = 'https://dev46006.service-now.com/api/now/table/incident'
snow_user = 'admin'
snow_pass = 'm4p4CyPyUZBo'

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
except Exception as e:
    print ('Error while loading state....Exit-1 : ' + str(e))
    sys.exit(1)

body={}
body['short_description'] = data['intent']['text']
body['description'] = data['text_body']

headers = {"Content-Type":"application/json","Accept":"application/json"}
response = requests.post(snow_url, auth=(snow_user, snow_pass), headers=headers ,data=json.dumps(body))

if response.status_code == 201:
    result = json.loads(response.text)
    #pprint.pprint(result)
    inc = result['result']['number']
    

    #update db
    doc={}
    doc['ticket'] = inc
    result = collection.update_one({'caseid':data['caseid']}, {"$set":doc}, upsert=False)

    #send Message to reply queue
    msg= {}
    msg['item_id'] = data['item_id']
    msg['caseid'] = data['caseid']
    msg['type'] = 'ticket_created'
    msg['ticket'] = inc
    event = Message(json.dumps(msg))
    nttBus.send_queue_message('htn.reply.email', event)
else:
    print(response)

