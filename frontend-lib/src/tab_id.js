// uuid provider タブ固有のUUIDを作成する。タブが破棄された場合は新しくなる
// 
// ブラウザでの実行が約束されないNext.jsでは
// トップレベルで const uuid = getTabUuid(); とせず
// getTabUuid()のまま使用したほうが安全
// AFrameの場合や、viteでフロントエンドに固定されている場合は問題ない

let cachedUuid = null;

export function getTabUuid() {
  if (typeof window === 'undefined') return ''; // Next.jsで念の為crash防止
  
  if (cachedUuid) return cachedUuid;
  
  const key = 'tab_unique_uuid';
  cachedUuid = sessionStorage.getItem(key);
  
  if (!cachedUuid) {
    cachedUuid = crypto.randomUUID();
    sessionStorage.setItem(key, cachedUuid);
  }
  
  return cachedUuid;
}
