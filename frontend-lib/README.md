# Metaworkプロトコル関係のfrontend用の共通コード置き場

* [`MetaworkMQTT.js`](./src/MetaworkMQTT.js) 劉さん使用バージョンをそのまま置く
* [`cookie_id.js`](./src/cookie_id.js) ページ用のUUID作成。劉さんバージョンそのまま
* [`metaworkMqttClient.js`](./src/metaworkMqttClient.js)
  簡単MQTTシングルトン用、汎用ライブラリ。`connect`,`subscribe`,`publish`,`end`
  だけで簡単利用。同一ページの諸々のモジュールから混ざって呼べるようにシングルトンにする。  
  `connect`はオンデマンド。reconnectに対応している(つもり)。  
  managerへのregister(だけ)はシングルトンにしたいため、(面倒なので)このライブラリー内で
  行っている。本来はこの簡単MQTTと`mgr/register`は分離すべきかもしれないが、ここは
  ユーザー認証が入ったら変わるはずなので気にしないことにする  
  以下、注意事項(値の設定は初回`connect`呼び出し時のみ有効)
  * brokerのURLのデフォルトはHTMLをfetchしたサーバーのwss接続ポート8333  
	`connect`の`broker_url`引数で変更可能
  * `mgr/register`のUUIDは`cookie_id.js`流用
  * `mgr/register`の`codeType`と`version`は、このpackageのnameを取り出しても
	意味がないので`registrationInfo`引数のキーバリューで与える仕様
