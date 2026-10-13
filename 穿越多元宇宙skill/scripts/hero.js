// hero.js — 角色精灵：每格 362×362，脚底基线 y=356，水平中心 x=181（cut_sheet.py 的输出规格）。
// heroFrame(name) 把一格缩成 90×90 的像素网格（颜色 + 明暗档 + 轮廓），供 styles.js 做画风迁移。
const CELL = 362, BASE = 356, CX = 181, HW = 90, HH = 90, SCL = CELL / HW;
const SPR = {}, FACE = {}, HERO_CACHE = {};
let POSES = {}; // { idle:[...], walk:[...], slash:[...], front:[...], leap:'leap', ... } 来自 film.json
async function loadHero(cfg) {
  POSES = cfg.poses; const names = new Set();
  Object.values(POSES).forEach(v => (Array.isArray(v) ? v : [v]).forEach(n => names.add(n)));
  const load = (n, dir, store) => new Promise(r => { const im = new Image(); im.onload = () => { store[n] = im; r(); }; im.onerror = () => { console.warn('missing ' + dir + n); r(); }; im.src = `${dir}/${n}.png`; });
  await Promise.all([...names].map(n => load(n, 'sprites', SPR)).concat((cfg.faces || []).map(n => load(n, 'faces', FACE))));
}
const hasPose = k => POSES[k] && (Array.isArray(POSES[k]) ? POSES[k].every(n => SPR[n]) : SPR[POSES[k]]);
function frameName(kind, p = 0) { let L = POSES[kind]; if (!L || !hasPose(kind)) L = POSES.idle; if (!Array.isArray(L)) return L; return L[Math.max(0, Math.min(L.length - 1, Math.floor(p * L.length + 1e-6)))]; }
const lum3 = (r, g, b) => (r * 0.3 + g * 0.59 + b * 0.11) / 255;
function heroFrame(kind, p) {
  const name = frameName(kind, p); if (HERO_CACHE[name]) return HERO_CACHE[name];
  const c = document.createElement('canvas'); c.width = CELL; c.height = CELL; const g = c.getContext('2d'); g.drawImage(SPR[name], 0, 0);
  const d = g.getImageData(0, 0, CELL, CELL).data, N = HW * HH, rgb = new Float32Array(N * 3), a = new Uint8Array(N), lum = new Float32Array(N), tone = new Uint8Array(N), edge = new Uint8Array(N);
  for (let y = 0; y < HH; y++) for (let x = 0; x < HW; x++) {
    let n = 0, R = 0, G = 0, B = 0;
    for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) { const X = Math.min(CELL - 1, Math.round(x * SCL + i)), Y = Math.min(CELL - 1, Math.round(y * SCL + j)), o = (Y * CELL + X) * 4; if (d[o + 3] < 128) continue; n++; R += d[o]; G += d[o + 1]; B += d[o + 2]; }
    if (n < 6) continue; const k = y * HW + x; a[k] = 1; rgb[k * 3] = R / n; rgb[k * 3 + 1] = G / n; rgb[k * 3 + 2] = B / n; lum[k] = lum3(R / n, G / n, B / n); tone[k] = lum[k] < 0.3 ? 0 : lum[k] < 0.62 ? 1 : 2;
  }
  for (let y = 0; y < HH; y++) for (let x = 0; x < HW; x++) { const k = y * HW + x; if (!a[k]) continue; if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([u, v]) => { const X = x + u, Y = y + v; return X < 0 || Y < 0 || X >= HW || Y >= HH || !a[Y * HW + X]; })) edge[k] = 1; }
  return (HERO_CACHE[name] = { name, src: SPR[name], rgb, a, lum, tone, edge });
}
