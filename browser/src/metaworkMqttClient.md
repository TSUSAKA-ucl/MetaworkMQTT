```
export const codeType = package_info.customInfo.type; 
export const version = package_info.version; version number
global private variable
export var mqttclient = null;
export var idtopic = userUUID;
const MQTT_BROKER_URL = "wss://liust.local/mqtt";
export var mqttBrokerURL = MQTT_BROKER_URL;
```

mqttのclientを、このモジュールを使ってシングルトンにする。
外部からのclientの取り出しは変数でなくgetter関数でおこなう
このモジュールシングルトンでclientがconnect済(作成済)ならばgetterは単にclientを返す
getter関数(connectMQTTの代わり)は、オプション引数で`callback`の他に
`registrationInfo`と`broker_url`を取る
callback関数のデフォルトはnull
`registrationInfo`のデフォルトは情報なし(`package.json`からの読み取りが必要ならば
外部で行う)
`broker_url`のデフォルトは、HTML,JSをfetchしたサーバーのwss接続
`userUUID`は`./cookie_id.js`でシングルトン
on connectで最初にpublishする`mgr/register`トピックのpayloadの`devType`は
`location.pathname`依存でなく`registrationInfo`のプロパティーに明示的に記述されている
ものを使用。
~~export する関数の名前は適切に変更する。~~このモジュールをimportして
元々の`MetaworkMQTT.js`同じ働きをするモジュール(wrapper)は別途作成する
