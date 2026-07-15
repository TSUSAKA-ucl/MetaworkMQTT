"use client";
// このファイルの名前は"metaworkMqttClient.ts"です
// modified by Gemini
import mqtt, { MqttClient } from 'mqtt';
import { userUUID } from './cookie_id';

// ハンドラーの型定義
type MessageHandler = (payload: any) => void;

let mqttclient: MqttClient | null = null;
// トピックごとのハンドラー管理（Set を使うことで重複登録を防止）
const topicHandlerMap = new Map<string, Set<MessageHandler>>();

// メッセージ受信時の共通ハンドラー
const handleMessage = (topic: string, message: Buffer): void => {
  let payload: any;
  try {
    payload = JSON.parse(message.toString());
  } catch (e) {
    console.error('Failed to parse MQTT message:', e);
    return;
  }

  // 完全一致でのハンドラー実行（※ワイルドカード対応が必要な場合は mqtt-match ライブラリ等の導入を推奨）
  const handlers = topicHandlerMap.get(topic);
  if (handlers) {
    handlers.forEach(handler => handler(payload));
  }
};

// 登録情報のインターフェース定義
interface RegistrationInfo {
  devType?: string;
  codeType?: string;
  version?: string;
}

// on-demand connect. 既にclientが存在する場合は何もせず、存在しない場合のみ接続する
export const connect = (
  registrationInfo: RegistrationInfo | null = null,
  broker_url: string | null = null
): void => {
  if (mqttclient == null) {
    const url = broker_url || `wss://${window.location.hostname}:8888`;
    
    // クライアント生成
    const client = mqtt.connect(url, {
      protocolVersion: 5,
    });

    // message ハンドラーは接続イベントの外側で、生成時に1度だけ登録する（最重要）
    client.on('message', handleMessage);

    client.on("connect", () => {
      console.log("Metawork MQTT Connected", client);
      const date = new Date();
      const devType = registrationInfo?.devType || "browser";
      const codeType = registrationInfo?.codeType || "unknown";
      const version = registrationInfo?.version || "unknown";
      
      const info = {
        date: date.toLocaleString(),
        device: {
          agent: navigator.userAgent,
          cookie: navigator.cookieEnabled
        },
        devType: devType,
        codeType: codeType,
        version: version,
        devId: userUUID
      };
      client.publish('mgr/register', JSON.stringify(info));
    });

    client.on('error', function (err: Error) {
      console.error('Metawork MQTT Connection error: ', err);
    });

    mqttclient = client;
  }
  return;
};

// 安全に購読し、解除用関数（unsubscribe）を返すように変更
export const subscribe = (topic: string, handler: MessageHandler): () => void => {
  if (mqttclient == null) {
    console.error('Metawork MQTT client not connected!');
    return () => {};
  }

  // Set を使って同一ハンドラーの重複登録を防ぐ
  if (!topicHandlerMap.has(topic)) {
    topicHandlerMap.set(topic, new Set<MessageHandler>());
  }
  const handlers = topicHandlerMap.get(topic)!;
  handlers.add(handler);

  // 実際の MQTT Subscribe
  mqttclient.subscribe(topic, { noLocal: true }, (err, granted) => {
    if (!err) {
      console.log('Metawork MQTT Subscribe topics', topic, granted);
    } else {
      console.error('Metawork MQTT Subscription error: ', err);
    }
  });

  // クリーンアップ関数（unsubscribe）を返却する
  return () => {
    const currentHandlers = topicHandlerMap.get(topic);
    if (currentHandlers) {
      currentHandlers.delete(handler);
      // そのトピックのリスナーがゼロになったら、マップから削除し、ブローカー側も unsubscribe する
      if (currentHandlers.size === 0) {
        topicHandlerMap.delete(topic);
        if (mqttclient) {
          mqttclient.unsubscribe(topic);
        }
      }
    }
  };
};

export const publish = (topic: string, msg: string | Buffer, qos: 0 | 1 | 2 = 0): void => {
  if (mqttclient == null) {
    console.error('Metawork MQTT client not connected!');
    return;
  }
  mqttclient.publish(topic, msg, { qos: qos });
};

export const end = (): void => {
  if (mqttclient != null) {
    // 引数に true を渡して強制かつ即座に終了、イベントリスナーも内部で全削除される
    mqttclient.end(true); 
    mqttclient = null;
    topicHandlerMap.clear();
    console.log('Metawork MQTT client ended and memory cleared.');
  }
};