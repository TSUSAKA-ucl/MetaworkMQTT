"use client";
import { customLogger } from './customLogger.js';
globalThis.__customLogger = customLogger;
import AFRAME from 'aframe';

// モジュール自体の subscribe/publish 関数を直接使う（clientを直接触らない）
import * as metawork from './lib/metaworkMqttClient.js';
import { userUUID } from './lib/cookie_id.js';

AFRAME.registerComponent('metawork-publisher', {
  schema: {
    codeType: { type: 'string', default: 'v8' },
    topicExt: { type: 'string', default: '' },
    model: { type: 'string', default: '' },
  },

  handleJointMoveTo: function (payload) {
    // function to check payload and setAttribute 'joint-move-to' on the entity
    // 2台のロボットを分離するためtopicExtを使う。(ロボット側がpayloadに
    // extを含めて送信することとする)
    // 劉ver.に合わせて"right/joint", "left/joint"のようにする。
    if (payload.ext === this.data.topicExt ||
        (!payload.ext && !this.data.topicExt)) {
      this.topicExtConsistent = true;
      if (payload.joints) {
        this.el.setAttribute('joint-move-to', payload.joints);
      } else {
        globalThis.__customLogger.warn('Received payload without joints:',
                                       payload);
      }
    } else {
      this.topicExtConsistent = false;
      globalThis.__customLogger.warn('Received payload with inconsistent ext:',
                                     payload.ext, 'expected:', this.data.topicExt);
    }
  },

  init: function () {
    // 状態管理変数の初期化
    this.robotId = null;
    this.topicExtConsistent = false;
    this.unsubscribes = []; // 購読解除関数（クリーンアップ用）を保持する配列

    if (!this.data.model && this.el.components['robot-loader'] &&
        typeof this.el.components['robot-loader'].data.model === 'string') {
      this.data.model = this.el.components['robot-loader'].data.model;
    }

    // シングルトンが初期化されていなければ初期化
    metawork.connect({
      codeType: this.data.codeType,
      version: '0.0.1'
    }, null);

    // 'robot-registered' イベント発火を待ってから時の処理
    this.el.addEventListener('robot-registered', () => {
      
      // callback2: 'dev/userUUID' トピックのメッセージを受信したとき
      const callback2 = (payload) => {
        this.robotId = payload.robotId;

        // callback3: 'robot/robotId' トピックを購読
        const unsub3 = metawork.subscribe(`robot/${payload.robotId}`,
                                          (payload2) => {
                                            this.handleJointMoveTo(payload2);
                                          });
        if (unsub3) this.unsubscribes.push(unsub3); // 解除関数をストック

        // マネージャーへ JSON 文字列にして publish
        metawork.publish(`dev/${payload.robotId}`, JSON.stringify({
          controller: "browser",
          devId: userUUID,
        }));
      };

      // モジュール側の subscribe を使用し、解除関数を受け取る
      const unsub2 = metawork.subscribe(`dev/${userUUID}`, callback2);
      if (unsub2) this.unsubscribes.push(unsub2); // 解除関数をストック

      // 初期登録リクエストを送信
      metawork.publish('mgr/request', JSON.stringify({
        devId: userUUID,
        type: this.data.model,
        ext: this.data.topicExt,
      }));
    }, { once: true });

  },

  tick: function () {
    // 全ての条件が揃っている場合のみ毎フレーム送信
    if (this.el.workerData?.current?.joints && this.robotId && this.topicExtConsistent) {
      const jointData = this.el.workerData.current.joints;
      const payload = {
        timestamp: Date.now(),
        joint: jointData,
      };
      const topic = `control/${userUUID}/${this.data.topicExt}/${this.robotId}`;
      metawork.publish(topic, JSON.stringify(payload));
    }
  },

  // A-Frameコンポーネントがエンティティから削除されたとき、またはシーン解体時
  remove: function () {
    globalThis.__customLogger.log('metawork-publisher: Removing component, clearing sub-listeners...');
    
    // このコンポーネントが登録した callback2, callback3 のリスナーだけをピンポイントで解除
    this.unsubscribes.forEach(unsubscribe => {
      if (typeof unsubscribe === 'function') unsubscribe();
    });
    this.unsubscribes = [];
  }
});
