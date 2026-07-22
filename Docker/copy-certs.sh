#!/usr/bin/bash
# このホストのサーバー認証用のcertとkeyのコピーをここにつくる
if [ "$1" = "" ]
then DestDir=$(cd $(dirname $0); pwd -P)
else DestDir=$(cd "$1"; pwd -P)
fi
# 証明書のディレクトリ
SrcDir="${HOME}/.local/share/ssl"
# $SrcDirに *.pemと*-key.pemの2個があれば、それらを
# (locahost専用でなくても)localhost.pemとlocalhost-key.pemにコピーする
#
cd "$SrcDir"
KeyFileCount=$(ls -1 *-key.pem 2>/dev/null | wc -l)
if [ $KeyFileCount -eq 1 ]; then
    KeyFile=$(ls -1 *-key.pem)
    CertFileName=$(echo "$KeyFile" | sed 's/-key\.pem$/.pem/')
    if [ -f "$CertFileName" ]; then
	# cd "$DestDir"
	echo cp -p "$SrcDir/$CertFileName" "$DestDir/localhost.pem"
	echo cp -p "$SrcDir/$KeyFile" "$DestDir/localhost-key.pem"
	echo chmod 600 "$DestDir/localhost.pem" "$DestDir/localhost-key.pem"
	echo "Copy cert and key files to $DestDir"
	exit 0
    else
	echo "Error: Corresponding certificate file $CertFileName not found for key $KeyFile"
    fi
else
    echo "Error: Expected exactly one key file in $SrcDir, found $KeyFile
"
fi
exit 1
