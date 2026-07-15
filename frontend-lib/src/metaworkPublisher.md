# コンポーネント説明

## ライブラリ`metaworkMqttClient.js`

Metaworkプロトコル用のMQTTの管理は
[`metaworkMqttClient.js`](./metaworkMqttClient.js)で行う。
`metaworkMqttClient.js`はESモジュールであるためwindow内で1個だけ
(singleton)になることが保証される。window内でこのモジュールを使う
pub/subはすべて同じconnectionを使う。このモジュールのsubscribeは
subscribe登録とcallbackの登録を同時に行い、`on('message'`時の
dispatcherも内蔵している。

connect時のカスタムcallbackの登録は廃止する。`on('connect``で
登録される関数は自動再コネクト時にも実行されることになり

## コンポーネントの`init`, `remove`

`mgr/register`トピックのpublishは、`metaworkMqttClient.js`内の
connectで1回だけ行う(brokerとMQTT Managerは先に立ち上がっている必要がある)。
`mgr/request`のpublishは、本コンポーネントの`init`(DOMがマウントされた時、
コンポーネントがsetAttributeされた時)で行う。

`dev/${userUUID}`のsubscriber callbackで`dev/${robotId}`をpublishする
必要があり、`dev/${robotId}`をpublishした直後に`robot/${robotId}`が帰っ
てくる可能性があり`robot/${robotId}`が帰ってきたらVRの仮想ロボットのジョ
イント角をセットする必要があるため、後ろから純に、まず仮想ロボットの組
み立ての完了(`robot-registered`)を待つ。そのeventListenerの中で
`dev/${userUUID}`のsubscribe登録をしてから`mgr/request`のpublishを行う。
`dev/${userUUID}`のsubscribe callback内で`robot/${robotId}`のsubscribe
登録をしたあと`dev/${robotId}`をpublishする。

`remove`時(DOMアンマウント時)に、登録したsubscriber(含callback)は全て
消去する

## コンポーネントの`init`, `remove`

### プロトコル自体の変更案

### ロボットの`mgr/register`に個々のロボットのプロバティー情報が含まれていない
browserは、自分の仕事に必要なロボット(のセット)を選ぶ(割り当てられる)はずで、
その組み合わせをbrowserが選択するにせよManagerが

### `mgr/register`のaccept追加
`mgr/register`でregisterされたかどうかがわからない。現状はMQTT
Manager(`MetaworkMQTT.py`)は低負荷で処理が順序化されているためこの仕様
で動作するがマイクロタスクで非同期化するとregister直後にrequestを投げ
る現在の実装でも動かなくなる可能性がある。

### `mgr/request`に対するrejectの欠如
rejectが欠如しているためbrowserは`mgr/request`の
accept(`dev/${userUUID}`)を何時までまてば良いかわからない。現状のMQTT
Managerは、`mgr/request`を受ける前にrobotが登録されていないと全く返事
を返さない。認証は済んでいるはずなので沈黙せずにrejectの返答をしても問
題ないはず

#### `dev/${robotId}`のpublish廃止(プロトコルの問題点ではないので廃止しなくても良い)
ただしこの構造はややこしいので、実ロボットは`dev/+/${robotId}`を
subscribeしたあと**定期的に`robot/${robotId}`(status)を送り続ける**
(pub/subシステムの**ゆるいカップリング**)として順序関係の厳密性を要求しな
いようにしたほうが良い。

するとブラウザによる`dev/${robotId}`トピックのpublishは不要になり、
`dev/${userUUID}/`トピックは`dev/${userUUID}/${robotId}`とトピック名を
変更して、実ロボットは`dev/+/${robotId}`をsubscribeするようにすれば良
い。あるいは現状のまま`dev/+`をsubscribeしてplayloadの`devId`(robotId)
を確認して動作することにしても、このトピックは頻発されないため問題ない
だろう

### Robot controlの`control/{$userUUID}`トピック名にrobot IDが含まれない
browserからのrequestを割り当てられた

### 実装上の気になる点
`MetawarkMQTT.js`ライブラリ`MetaworkMQTT.py`(Manager)のみ。ロボット側の
clientについては触れない。

1. browserの`codeType`を`package.json`の`name`から取得している(意図不明)
2. Managerに登録されたbrowserの`codeType`は実は使われていない
3. subscriberのcallbackがトピック毎に分離されていないためMetaworkプロトコル部分をライブラリとして分離しづらい
4. `MetaworkMQTT.py`(Python)は`paho.mqtt`が使用されていて、mainと
   callbackはPython threadとして別threadだが、`self.devices`はmutable
   でdestructiveな操作をているにもかかわらず排他(lock)されていない


# `metawork-publisher`コンポーネント実装AI向け説明

`import * as metawork from '@ucl-nuee/metawork';`  
`import * as metawork from '@ucl-nuee/metawork/metaworkMqttClient.js';`  
`import * as metawork from './lib/metaworkMqttClient.js';`  
MQTT clientのシングルトンを提供するモジュールをimportする。将来的には
一番上の形式

`import {userUUID} from './lib/cookie_id.js';`  
userUUIDのシングルトンを提供する(流用)。将来的には同様


### `AFRAME.registerComponent('metawork-publisher'`
metawork用のmqtt clientは、metawork NPMパッケージの
`metaworkMqttClient.js`(`index.js`)モジュール内の`global`でシングルトンとなる。
本コンポーネントの`init`時は、適切に引数を作成して`get`を呼べば良い。
基本的にAFrameコンポーネントでは`end`は呼ばない。ブラウザのタブが破棄されればそれで
良いし、ReactでAFrame DOMを作成する前にgetしていれば対応するReactが`end`を呼ぶ
こととする。

`init`で、`this.client = metawork.get(callback1, regInfo, url)`を呼ぶ。
`regInfo`は.`.codeType`と`.version`だけ設定すれば良い。
urlは当面デフォルト(`wss://${window.location.hostname}:8888`)
callback1は、`'robot-registered'`(by `robot-loader`)を待って
`'dev/userid'`のcallback2をシングルトンの`topicHandlerMap`に登録してをsubscribe。
`'mgr/request'`をpublish。
さらにcallback2内で`'robot/robot-id'`トピックにcallback3をセットしsubscribeして
`'dev/robot-id'`をpublish
callback3は`joint-move-to`を呼ぶ(`setAttribute`)
ブラウザのロボットが`joint-move-to`指令に到着したかどうかはrobot側で判定(?)
(AFrame的には、こちらでeventで受取りロボット側に送ることも可能だが仕様に無い)



2台のロボットを分離するため`schema`の`topicExt`を使う。値は、劉versionに
合わせて`"right/joint"`,`"left/joint"`のようにする。`robot/${robotId}`の
payloadにも同様のプロパティー`ext`が付いていることを期待する。
`payload.ext`と`this.data.topicExt`が一致する場合のみ
`joint-move-to`を`setAttribute`する。`payload.ext`が無い場合は
`this.data.topicExt`が空文字列のときのみ`joint-move-to`を`setAttribute`する。
これら`setAttribute`できる(できた)ケースのみ`this.topicExtConsitent`をtrueに
して`tick`で`this.el.workerData.current.joints`をpayloadに載せて
`control/${userUUID}/${this.data.topicExt}/${this.robotId}`を
publishする。トピック名と順序は劉versionとの互換性のためこのようになっている。
