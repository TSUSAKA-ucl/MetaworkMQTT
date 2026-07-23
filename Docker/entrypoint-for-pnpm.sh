#!/bin/sh
set -e

# 1. OverlayFS のセットアップ
# /mnt/ro_base: pnpmパッケージルート(ro) 旧/app, dockkerが起動時にマウント
# /mnt/rw_storage: tmpfs, dockerが起動時にマウント
# /app: read onlyおよびtmpfsのマウントポイント
mkdir -p /mnt/rw_storage/upper /mnt/rw_storage/work /app
# echo '##########'
# ls -l /mnt
# echo '##########'
mount -t overlay overlay \
      -o lowerdir=/mnt/ro_base,upperdir=/mnt/rw_storage/upper,workdir=/mnt/rw_storage/work \
      /app
# echo '##########'
# ls -l /app
# echo '##########'
cd /app
# 2. 本来実行したいコマンドに処理を引き継ぐ
# 引数（CMD）が指定されていない場合はデフォルトで sh を起動
if [ $# -eq 0 ]; then
  exec /bin/sh
else
  exec "$@"
fi
b
