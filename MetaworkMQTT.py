# メタワーク用の MQTT manager

# internal instruction
# https://uclab.esa.io/posts/8825 (privavte)


import argparse
import paho.mqtt.client as mqtt
import json
import time

TIMEOUT_HOUR = 1  # for More than 1 hour, we need to clear the device db.
#client robots should update there info for each 30min.
class MetaworkMQTT:
    def __init__(self, host, port, wss=False): #, username, password):
        self.host = host
        self.port = port
        self.mod = False
#        self.username = username
#        self.password = password
        if wss:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                transport="websockets")
            self.client.tls_set(cert_reqs=0)
        else:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
#        self.client.username_pw_set(username, password)
        self.client.connect(host, port, 60)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
       
        self.devices = []
        
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("Connected with result code "+str(reason_code))
        client.subscribe("mgr/register")
        client.subscribe("mgr/unregister")
        client.subscribe("mgr/request")

    def on_message(self, client, userdata, msg):
        print("#### "+msg.topic+" "+str(msg.payload))
        if msg.topic == "mgr/register":
            self.update_status()
            self.register(msg)
        elif msg.topic == "mgr/unregister":    
            self.update_status()
            self.unregister(msg)
        elif msg.topic == "mgr/request":    
            self.request(msg)
        
    # we need to flush obsolute devices after TIMEOUT_HOUR
    def update_status(self):
        for d in self.devices:
            if (time.time())-d["registered"] > TIMEOUT_HOUR*3600:
                print("TIMEOUT: ",d) 
                self.devices.remove(d) # あれば、そのデータを消す            
            
    def register(self, msg):
        data = json.loads(msg.payload)
        ver = data.get("version", "none")

        if "devId" not in data:
            return
        
        if "device" in data:
            print("register:", data["devId"][:4]+"-"+data["devId"][-4:],ver,data["device"]["agent"])
        else:
            print("register:", data["devId"][:4]+"-"+data["devId"][-4:],ver)

        # 同じIDのデバイスがあるかを確認
        for d in self.devices:
            if d["devId"] == data["devId"]:
                self.devices.remove(d) # あれば、そのデータを消したうえで
                break
        # 最後にappend する

        # update for codeType -> type 
        cType ="" 
        if "type" in data:
            cType= data["type"]
        elif "codeType" in data:
            cType = data["codeType"]
        else:
            cType = "unknown"
        
        optStr = ""
        if "optStr" in data:
            optStr = data["optStr"]

        self.devices.append({
            "type": cType,
            "version":ver,
            "devId": data["devId"],
            "devType": data["devType"],
            "optStr": optStr,
            "date": data["date" ],
            "registered": int(time.time())
        })
        self.mod = True

    def unregister(self, msg):
        data = json.loads(msg.payload)
        if "devId" not in data:
            return
        print("unregister:", data["devId"])
        # 同じIDのデバイスがあるかを確認
        for d in self.devices:
            if d["devId"] == data["devId"]:
                self.devices.remove(d) # あれば、そのデータを消したうえで
                break
        self.mod = True
        
        
#        print("register")
#        self.client.publish("mgr/register", json.dumps(data))

#   希望するタイプのデバイスがあるかを確認
    def request(self, msg):
        data = json.loads(msg.payload)
        print("Request:",data)
        #逆に探すべし。
        rev_list = self.devices[::-1]
        try:
            for d in rev_list:
                if d["devType"] == "robot" and d["type"] == data["type"]:
                    print("Request found",d) # 本当は、現在使われているか、オーバライドか、などの情報を保持すべき
                    self.client.publish("dev/"+data["devId"], json.dumps(d))
                    self.pub_event({"event":"request", "from":data, "to":d, "date":time.ctime()})               
                    return
        except Exception :
            print("error in request",data)
            print("not found request ", data["type"])
            self.client.publish("dev/"+data["devId"], json.dumps({"devId": "none"}))
    
    def pub_status(self):
        self.client.publish("mgr/status", json.dumps(self.devices))
        
    def pub_event(self,event):
        self.client.publish("mgr/event", json.dumps(event))
        
            
    def print_devices(self):
        for i,r in enumerate(self.devices):
            print(i,r)
        self.mod = False
            


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Metawork MQTT Manager')
    parser.add_argument('--host', type=str, default='localhost', help='MQTT broker host (default: localhost)')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port (default: 1883)')
    parser.add_argument('--wss', action='store_true', help='Use WSS (default: False)')
    args = parser.parse_args()
    port = args.port
    if args.wss and port == 1883:
        port = 8083
    host = args.host
    mq = MetaworkMQTT(host, port, args.wss)
    
    while True:
        time.sleep(1)
        if mq.mod:
            print("---- "+time.ctime()+" -------------")
            mq.print_devices()
            mq.pub_status()
