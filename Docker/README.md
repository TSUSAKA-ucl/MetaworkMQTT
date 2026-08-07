# docker composeのための`up.sh`の説明

## 概要

npmパッケージルートで、`${PathToComposeDir}/up.sh .`を実行すると、
mosquitto,manager(`MetaworkMQTT.py`)とdevサーバーがcomposeで立ち上がる。
`${PathToThisDir}/down.sh .`で落とす。

* `./up.sh`の様に引数なしで呼ぶと、mosquittoとmanager(`MetaworkMQTT.py`)だけ立ち上げる。
* `./MetaworkMQTT/Docker/up.sh .`のように引数をつけ、第一引数がディレクトリだと
  そこをnpmパッケージのルートと見なして、mosquitto,managerに加えてdevサーバー(
  デフォルトは`pnpm dev`)を立ち上げる。第二引数が有る場合は、第一引数がマウントポイント
  第二引数がマウントポイントからの(パッケージルートの)相対パスとする。モノレポ(pnpm
  workspace)対応のため。
* `./up.sh ${PathToPackage}`のようにdevサーバを立ち上げたときは、`./down.sh ${PathToPackage}`
  のように`down.sh`も引数付きで呼ばないとdevサーバーのコンテナだけ残る。
* 独自CA等でホストのcertとkeyがあれば、`~/.local/share/ssl/`に置くか、SANに拘らず
  `localhost.pem`と`localhost-key.pem`という名前にして
  npmパッケージの`localcerts/`ディレクトリに置くことを期待している(`package.json`次第)
* mosquittoも同じcertとkeyをバインドマウントして使用する。
  さらにmosquittoはCA(`トップレベル/Mosquitto/certs/rootCA.pem`)も設定しているが、
  brokerは1つだけなので多分使用していないと思う
* `MetaworkMQTT.py`(manager)のコンテナにも一応同じCAを渡しているが、brokerを同一composeで
  立ち上げるので、必ずしも暗号化とサーバー認証は必要ない。

## サーバー認証用ホスト鍵の置き場所と環境変数によるコントロール

環境変数`CertsDir`が設定されているとその下の`localhost.pem`と`localhost-key.pem`を
devサーバーとmosquittoが使用する。環境変数に無い場合npmパッケージルートの`localcerts`の
下のそれらを使用する。`localhost.pem`と`localhost-key.pem`が無い場合は`~/.local/share/ssl/`からの
コピーを試みる。

環境変数`CADir`が設定されていると`"$CADir"/rootCA.pem`(公開鍵)をmosquittoと`MetaworkMQTT.py`が
使用する。環境変数に無い場合は`トップレベル/Mosquitto/certs/rootCA.pem`を使用する。公開鍵なので参考に
このgitリポに入れてある

もしdevサーバー起動コマンドを変更したければ環境変数`DevCmd`で
`DevCmd=dev-mkcert ./MetaworkMQTT/Docker/up.sh .`のように変更できる。
composeが立ち上げるときの、バインドマウント、ボリュームマウント、個々のCMDは
[`compose.yaml`](./compose.yaml)参照。
