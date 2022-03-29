import paho.mqtt.client as mqtt
import time
import json
import threading
import logging

from first_task.file_manager import FileManager
from first_task.db_provider import DbProvider
from first_task.decoder import data_decode

logging.basicConfig(level=logging.INFO)

clients=[
{"broker":"localhost","port":1883,"name":"file_manager","sub_topics":["decoder/json_data", "decoder/raw_error_data"],"pub_topics":["file_manager/raw_data"]},
{"broker":"localhost","port":1883,"name":"decoder","sub_topics":["file_manager/raw_data"],"pub_topics":["decoder/json_data", "decoder/raw_error_data"]},
{"broker":"localhost","port":1883,"name":"db_provider","sub_topics":["decoder/json_data"],"pub_topics":[]}
]

filemanager = FileManager()

nclients=len(clients)
message="test message"

def Connect(client,broker,port,keepalive,run_forever=False):
    """Attempts connection set delay to >1 to keep trying
    but at longer intervals. If runforever flag is true then
    it will keep trying to connect or reconnect indefinetly otherwise
    gives up after 3 failed attempts"""
    connflag=False
    delay=5
    #print("connecting ",client)
    badcount=0 # counter for bad connection attempts
    while not connflag:
        logging.info("connecting to broker "+str(broker))
        #print("connecting to broker "+str(broker)+":"+str(port))
        print("Attempts ",str(badcount))
        time.sleep(delay)
        try:
            client.connect(broker,port,keepalive)
            connflag=True

        except:
            client.badconnection_flag=True
            logging.info("connection failed "+str(badcount))
            badcount +=1
            if badcount>=3 and not run_forever: 
                return -1
                raise SystemExit #give up


                
    return 0
    #####end connecting
def wait_for(client,msgType,period=1,wait_time=10,running_loop=False):
    """Will wait for a particular event gives up after period*wait_time, Default=10
seconds.Returns True if succesful False if fails"""
    #running loop is true when using loop_start or loop_forever
    client.running_loop=running_loop #
    wcount=0  
    while True:
        logging.info("waiting"+ msgType)
        if msgType=="CONNACK":
            if client.on_connect:
                if client.connected_flag:
                    return True
                if client.bad_connection_flag: #
                    return False
                
        if msgType=="SUBACK":
            if client.on_subscribe:
                if client.suback_flag:
                    return True
        if msgType=="MESSAGE":
            if client.on_message:
                if client.message_received_flag:
                    return True
        if msgType=="PUBACK":
            if client.on_publish:        
                if client.puback_flag:
                    return True
     
        if not client.running_loop:
            client.loop(.01)  #check for messages manually
        time.sleep(period)
        wcount+=1
        if wcount>wait_time:
            print("return from wait loop taken too long")
            return False
    return True

def client_loop(client,broker,port,keepalive=60,loop_function=None,\
             loop_delay=1,run_forever=False):
    """runs a loop that will auto reconnect and subscribe to topics
    pass topics as a list of tuples. You can pass a function to be
    called at set intervals determined by the loop_delay
    """
    client.run_flag=True
    client.broker=broker
    print("running loop ")
    client.reconnect_delay_set(min_delay=1, max_delay=12)
      
    while client.run_flag: #loop forever

        if client.bad_connection_flag:
            break         
        if not client.connected_flag:
            print("Connecting to ",broker)
            if Connect(client,broker,port,keepalive,run_forever) !=-1:
                if not wait_for(client,"CONNACK"):
                   client.run_flag=False #break no connack
            else:#connect fails
                client.run_flag=False #break
                print("quitting loop for  broker ",broker)

        client.loop(0.01)

        if client.connected_flag and loop_function: #function to call
                loop_function(client,loop_delay) #call function
    time.sleep(1)
    print("disconnecting from",broker)
    if client.connected_flag:
        client.disconnect()
        client.connected_flag=False
    
def on_log(client, userdata, level, buf):
    print(buf)
def on_message(client, userdata, message):

    for c in clients:
        if client == c["client"]:

            if c["name"] == "decoder":

                if message.topic == 'file_manager/raw_data':

                    received_raw_data = message.payload.decode('UTF-8')
                    json_acceptable_data = received_raw_data.replace("'", "\"")
                    received_raw_dict_data = json.loads(json_acceptable_data)
                    data, state = data_decode(received_raw_dict_data)
                    if state == 1:
                        client.publish(topic='decoder/json_data', payload = str(data))
                    else:
                        client.publish(topic='decoder/raw_error_data', payload = str(data))
        
            if c["name"] == "file_manager":

                    if message.topic == 'decoder/json_data':
                        received_json_data = message.payload.decode('UTF-8')
                        json_acceptable_data = received_json_data.replace("'", "\"")
                        received_json_dict_data = json.loads(json_acceptable_data)
                        filemanager.create_json_file(received_json_dict_data)

                    if message.topic == 'decoder/raw_error_data':

                        received_raw_error_data = message.payload.decode('UTF-8')
                        json_acceptable_data = received_raw_error_data.replace("'", "\"")
                        received_error_data = json.loads(json_acceptable_data)
                        filemanager.create_error_file(received_error_data)

            if c["name"] == "db_provider":

                    if message.topic == "decoder/json_data":
                        dbprovider = DbProvider()
                        received_json_data = message.payload.decode('UTF-8')
                        json_acceptable_data = received_json_data.replace("'", "\"")
                        received_json_dict_data = json.loads(json_acceptable_data)
                        dbprovider.provide_to_database(received_json_dict_data)

    
    
def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        for c in clients:
          if client==c["client"]:
              if c["sub_topics"]!=[]:
                  for topic in c.get("sub_topics"):
                    client.subscribe(topic)
          
        #print("connected OK")
    else:
        print("Bad connection Returned code=",rc)
        client.loop_stop()  
def on_disconnect(client, userdata, rc):
   client.connected_flag=False #set flag
   #print("client disconnected ok")
def on_publish(client, userdata, mid):
   time.sleep(1)
   print("In on_pub callback mid= "  ,mid)

def pub(client,loop_delay):
    for c in clients:
        if client == c["client"]:
            if c["name"] == "file_manager":
                raw_data = filemanager.get_raw_data()
                if len(raw_data) > 0:
                    for data in raw_data:
                        print(data)
                        client.publish(topic = 'file_manager/raw_data', payload=str(data))
                        
                    raw_data.clear()
                time.sleep(0.5)
    pass    

def Create_connections():
   for i in range(nclients):
        client = mqtt.Client(clients[i]["name"])             #create new instance
        clients[i]["client"]=client
        broker=clients[i]["broker"]
        port=clients[i]["port"]
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        #client.on_publish = on_publish
        client.on_message = on_message
        t = threading.Thread(target\
            =client_loop,args=(client,broker,port,60,pub))
        print(clients[i]["name"], "+++++++++++++++")
        threads.append(t)
        t.start()


mqtt.Client.connected_flag=False #create flag in class
mqtt.Client.bad_connection_flag=False #create flag in class

threads=[]
print("Creating Connections ")
no_threads=threading.active_count()
print("current threads =",no_threads)
print("Publishing ")
Create_connections()

print("All clients connected ")
no_threads=threading.active_count()
print("current threads =",no_threads)
print("starting main loop")
try:
    while True:
        time.sleep(10)
        no_threads=threading.active_count()
        print("current threads =",no_threads)
        for c in clients:
            if not c["client"].connected_flag:
                print("broker ",c["broker"]," is disconnected")
    

except KeyboardInterrupt:
    print("ending")
    for c in clients:
        c["client"].run_flag=False
time.sleep(10)