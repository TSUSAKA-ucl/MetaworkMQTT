import argparse
import paho.mqtt.client as mqtt
import json
import time
import threading  # スレッドロックのために追加

TIMEOUT_HOUR = 1  # for More than 1 hour, we need to clear the device db.
# client robots should update there info for each 30min.

class MetaworkMQTT:
    def __init__(self, host, port, wss=False):
        self.host = host
        self.port = port
        self.mod = False  # アトミックに扱えるため、ロック外での読み書きを許容
        self._lock = threading.Lock()
        # self.username = username
        # self.password = password
        if wss:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                transport="websockets")
            self.client.tls_set(cert_reqs=0)
        else:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
        # self.client.username_pw_set(username, password)
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

    # register/unregister/request共にpayloadをjsonとして解釈するためここでjson.loadsする
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except json.JSONDecodeError:
            print("Invalid JSON in message on topic:", msg.topic, file=sys.stderr)
            return
        ## msg.payloadはそのままprintすると横に長過ぎるのでpretty printする
        # print("#### "+msg.topic+" "+str(msg.payload))
        print("#### "+msg.topic+" "+json.dumps(data, indent=2), flush=True)

        if msg.topic == "mgr/register":
            self.update_status()
            self.register(data)
        elif msg.topic == "mgr/unregister":    
            self.update_status()
            self.unregister(data)
        elif msg.topic == "mgr/request":    
            self.request(data)
        
    # we need to flush obsolute devices after TIMEOUT_HOUR
    def update_status(self):
        current_time = time.time()
        with self._lock:
            # イテレーション中の削除を避けるため、有効なものだけを残すリスト内包表記に変更
            valid_devices = []
            for d in self.devices:
                if current_time - d["registered"] > TIMEOUT_HOUR * 3600:
                    print("TIMEOUT: ", d)
                    self.mod = True  # 削除が発生したため変更フラグを立てる
                else:
                    valid_devices.append(d)
            self.devices = valid_devices
            
    def register(self, data):
        ver = data.get("version", "none")

        if "devId" not in data:
            return
        
        # registerはスパイク負荷がかかる可能性があるので削除したほうが良い
        # if "device" in data:
        #     print("register:", data["devId"][:4]+"-"+data["devId"][-4:],ver,data["device"]["agent"])
        # else:
        #     print("register:", data["devId"][:4]+"-"+data["devId"][-4:],ver)

        cType = data.get("type", data.get("codeType", "unknown"))
        optStr = data.get("optStr", "")

        # ロック内でリストの更新処理をアトミックに行う
        with self._lock:
            # 同じIDのデバイスがあるかを確認して削除
            self.devices = [d for d in self.devices if d["devId"] != data["devId"]]
            # 最後にappend する
            self.devices.append({
                "type": cType,
                "version": ver,
                "devId": data["devId"],
                "devType": data["devType"],
                "optStr": optStr,
                "date": data["date"],
                "registered": int(time.time())
            })
            self.mod = True

    def unregister(self, data):
        if "devId" not in data:
            return
        print("unregister:", data["devId"]) # スパイク負荷は無いとして残す

        with self._lock:
            # 同じIDのデバイスがあるかを確認して削除
            original_len = len(self.devices)
            self.devices = [d for d in self.devices if d["devId"] != data["devId"]]
            if len(self.devices) != original_len:
                self.mod = True

        # print("register")
        # self.client.publish("mgr/register", json.dumps(data))

    # 希望するタイプのデバイスがあるかを確認
    def request(self, data):
        # giant lockを避けるためスナップショットを作成
        with self._lock:
            rev_list = self.devices[::-1]

        try:
            for d in rev_list:
                if d["devType"] == "robot" and d["type"] == data["type"]:
                    # requestはブラウザごとなのでスパイク負荷の確率は低くprintを残す
                    print("Request found",d) # 本当は、現在使われているか、オーバライドか、などの情報を保持すべき
                    self.client.publish("dev/"+data["devId"], json.dumps(d))
                    self.pub_event({"event":"request", "from":data, "to":d, "date":time.ctime()})                
                    return
            
            # ループを抜けても見つからなかった場合（インデントを修正し try ブロック内に配置）
            print("not found request ", data["type"])
            self.client.publish("dev/"+data["devId"], json.dumps({"devId": "none"}))
        except Exception as e:
            print(f"error in request {data}: {e}", flush=True, file=sys.stderr)
    
    def get_devices_snapshot(self):
        """安全に現在のデバイスリストのコピーを取得する（ロック時間を極小化）"""
        with self._lock:
            return list(self.devices)

    def pub_status_snapshot(self, snapshot):
        """ロックの外で作られたスナップショットをシリアライズして送信（ノンブロッキング）"""
        payload = json.dumps(snapshot)
        self.client.publish("mgr/status", payload)
        
    def pub_event(self, event):
        self.client.publish("mgr/event", json.dumps(event))
        
    def print_devices_snapshot(self, snapshot):
        """ロックの外で安全にプリント処理を行う"""
        for i, r in enumerate(snapshot):
            print(i, json.dumps(r,indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Metawork MQTT Manager')
    parser.add_argument('--host', type=str, default='localhost', help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--wss', action='store_true', help='Use WSS')
    args = parser.parse_args()
    
    port = 8083 if args.wss and args.port == 1883 else args.port
    mq = MetaworkMQTT(args.host, port, args.wss)
    
    while True:
        time.sleep(1)
        # 1. 変更フラグをチェック（アトミックなのでロック不要）
        if mq.mod:
            # 2. 先に変更フラグを落とす（この後に登録があっても、次のループで拾える）
            mq.mod = False
            # 3. 一瞬だけロックして現在のリストのコピーを取得
            devices_snap = mq.get_devices_snapshot()
            
            # 4. ロックの外で、重いプリントとシリアライズ・送信を実行
            print("---- "+time.ctime()+" -------------")
            mq.print_devices_snapshot(devices_snap)
            mq.pub_status_snapshot(devices_snap)
