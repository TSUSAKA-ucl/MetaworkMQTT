# MetaworkMQTT

[MQTT manager for SIP3-Metawork](https://uclab.esa.io/posts/8825)
(あるいはhttps://uclab.esa.io/posts/9599 参照)と、
フロントエンド用のJavaScriptライブラリと、
エッジサーバー上のMQTTクライアント用のpythonパッケージを集めてこのリポジトリで管理する。

## このリポジトリのディレクトリ構造
* [`frontend-lib`](./frontend-lib/)ディレクトリの下は
フロントエンド用JavaScriptのnpmパッケージ
* [`manager`](./manager/) MetaworkMQTT Manager `MetaworkMQTT.py`  
  過去からの経緯によりMQTT manager([`MetaworkMQTT.py`](./MetaworkMQTT.py))は
  当面このリポジトリトップレベルからリンクを張る  
  `Jun 17 17:39 2026` commit ID `df9f2a716e6482c62b1e40504c39901b8ba0ed76`までは
  `MetaworkMQTT.py`は最低限度の変更だったが、その次からはlockを入れる
* エッジサーバーライブラリ用ディレクトリは未整備
