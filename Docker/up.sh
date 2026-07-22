#!/bin/bash
ThisDir=$(cd $(dirname $0); pwd -P)
# UID,GID環境変数をセットする
if [ "$UID" != `id -u` ]; then
    unset UID
    export UID=$(id -u)
fi
export GID=$(id -g)

# $1が存在すればそこをNext.jsのパッケージルートとしてNEXT_PKG環境変数にセットする
if [ "$1" != "" ] && [ -d "$1" ]; then
    export NEXT_PKG=$(cd "$1"; pwd -P) || exit 1
    shift
fi
# ホスト認証鍵はlocalhost以外も認証することを推奨。SANに必要なIP,DNSを入れる

# Next.js,Viteのdevサーバー用のcertsを"$CertsDir"にコピーする
# $CertsDirが定義されていなければ、"$NEXT_PKG"/localcerts/をCertsDirにする
# $NEXT_PKGすなわち$1も無ければ../../localcerts/をCertsDirにする
if [ "$NEXT_PKG" = "" ]
then CERT_ROOT="$ThisDir"   # "./../.."
else CERT_ROOT="$NEXT_PKG"
fi
echo CERT_ROOT="$CERT_ROOT"
if [ "$CertsDir" = "" ]
then [ -e "$CERT_ROOT"/localcerts ] || mkdir "$CERT_ROOT"/localcerts || exit 2
     [ -d "$CERT_ROOT"/localcerts ] || exit 2
     export CertsDir="$CERT_ROOT"/localcerts
fi
echo CertsDir = "$CertsDir"
if [ ! -f "$CertsDir"/localhost.pem ] || [ ! -f "$CertsDir"/localhost-key.pem ]
then if [ -x "$CertsDir"/copy-certs.sh ]
     then "$CertsDir"/copy-certs.sh "$CertsDir" || exit 1
     else "$ThisDir"/copy-certs.sh "$CertsDir" || exit 1
     fi
fi

# さらにbrokerは、"$CertsDir"/localhost.pem, "$CertsDir"/localhost-key.pem 及び
# "$CADir"/rootCA.pemをバインドマウントして使う
[ "$CADir" = "" ] && export CADir="$ThisDir"/../Mosquitto/certs/

export RootDir="$ThisDir"/..
# env |grep CertsDir
# env |grep CADir
# env |grep NEXT_PKG
# Docker Compose で全サービスを立ち上げ。loggerとdevサーバーは明記しないと立ち上がらない
# docker compose up mqtt_logger nextjs-dev
if [ "$NEXT_PKG" = "" ]
then 
     env |grep CertsDir
     env |grep CADir
     env |grep NEXT_PKG
     pwd
     docker compose -f "$ThisDir"/compose.yaml up "$@"
else 
     env |grep CertsDir
     env |grep CADir
     env |grep NEXT_PKG
     pwd
     echo docker compose -f "$ThisDir"/compose.yaml "$@" up
     docker compose -f "$ThisDir"/compose.yaml --profile dev-server "$@" up
fi
