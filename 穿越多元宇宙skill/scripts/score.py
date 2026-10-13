"""配乐：python score.py [--mood adventure|dreamy|chip] [--no-sfx] → score.wav（读 render.py 写出的 cues.json）
同一段主旋律贯穿全片；每章按画风换乐器（KIT 表）；挥剑、裂缝、交互点音效按时间点放。"""
import json, argparse, pathlib, numpy as np, scipy.signal as sg, scipy.io.wavfile as wf
here = pathlib.Path(__file__).parent; ap = argparse.ArgumentParser(); ap.add_argument('--mood', default='adventure'); ap.add_argument('--no-sfx', action='store_true'); O = ap.parse_args()
SR = 44100; C = json.load(open(here / 'cues.json')); L, DUR, CUES = C['L'], C['DUR'], C['cues']; N = int((DUR + 2) * SR); rng = np.random.default_rng(7)
BUS = {k: np.zeros(N) for k in ('lead', 'harm', 'bass', 'drum', 'sfx')}; S16 = L / 32
def T(d): return np.arange(max(1, int(d * SR))) / SR
def env(n, a=0.005, r=0.08): e = np.ones(n); na = max(1, min(n // 2, int(a * SR))); nr = max(1, min(n // 2, int(r * SR))); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def filt(x, f, kind='low'): b, a = sg.butter(2, np.clip(np.array(f) / (SR / 2), 0.001, 0.99), kind); return sg.lfilter(b, a, x)
def put(bus, t0, x, g=1.0):
    i = int(t0 * SR)
    if 0 <= i < N: x = x[:N - i]; BUS[bus][i:i + len(x)] += x * g
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def add(f, d, amps, dec):
    t = T(d); return sum(a * np.sin(2 * np.pi * f * h * t) * np.exp(-t * dc) for h, (a, dc) in enumerate(zip(amps, dec), 1) if f * h < SR / 2.2)
# ---- 乐器 ----
def pluck(f, d, br=1.2, dc=3.0): d += 0.4; return add(f, d, [h ** -br for h in range(1, 13)], [dc * (1 + h * 0.5) for h in range(1, 13)]) * env(int(d * SR), 0.002, 0.05)
def piano(f, d): d += 0.6; return add(f, d, [h ** -1.6 for h in range(1, 10)], [1.2 + h * 0.9 for h in range(1, 10)]) * env(int(d * SR), 0.002, 0.1)
def bell(f, d, idx=3.0, ratio=3.5, dc=2.2): t = T(d + 0.8); return np.sin(2 * np.pi * f * t + idx * np.exp(-t * 4) * np.sin(2 * np.pi * f * ratio * t)) * np.exp(-t * dc) * env(len(t), 0.002, 0.05)
def saw(f, d, H=12, a=0.01, r=0.08): t = T(d); return sum((-1) ** (h + 1) / h * np.sin(2 * np.pi * f * h * t) for h in range(1, H + 1) if f * h < SR / 2.2) * env(len(t), a, r)
def vib(f, d, depth, rate=5.5): t = T(d); return 2 * np.pi * f * np.cumsum(1 + depth * np.sin(2 * np.pi * rate * t) * np.clip(t * 3 - 0.3, 0, 1)) / SR, t
def brass(f, d): ph, t = vib(f, d, 0.004); return sum(np.sin(h * ph) / h * (1 - np.exp(-t * 30 / h)) for h in range(1, 11) if f * h < SR / 2.2) * env(len(t), 0.03, 0.08)
def suona(f, d): ph, t = vib(f, d, 0.012, 6.5); return filt(sum(h ** -0.7 * np.sin(h * ph) for h in range(1, 12) if f * h < SR / 2.2), 4500) * env(len(t), 0.02, 0.06) * 0.6
def flute(f, d): ph, t = vib(f, d, 0.006, 5); return (np.sin(ph) + 0.15 * np.sin(2 * ph) + 0.12 * filt(rng.normal(0, 1, len(t)), f * 2)) * env(len(t), 0.06, 0.1)
def organ(f, d): t = T(d); return sum(a * np.sin(2 * np.pi * f * h * t) for h, a in [(0.5, .5), (1, 1), (2, .6), (3, .35), (4, .25)]) * env(len(t), 0.03, 0.15) * 0.6
def strings(f, d): return filt(sum(saw(f * (1 + q), d, 9, 0.25, 0.3) for q in (-0.004, 0, 0.005)) / 3, 2600)
def square(f, d, duty=0.5): t = T(d); return np.where((f * t) % 1 < duty, 1.0, -1.0) * env(len(t), 0.002, 0.03) * 0.5
def tri(f, d): t = T(d); q = np.floor(4 * np.abs((f * t) % 1 - 0.5) * 8) / 8; return (q * 2 - 1) * env(len(t), 0.002, 0.02) * 0.6
def sbass(f, d): t = T(d); return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.005, 0.06)
def epiano(f, d): t = T(d + 0.5); return np.sin(2 * np.pi * f * t + 1.6 * np.exp(-t * 2.5) * np.sin(2 * np.pi * f * t)) * np.exp(-t * 1.6) * env(len(t), 0.003, 0.2)
V = dict(pluck=pluck, koto=lambda f, d: pluck(f, d, 0.9, 2.2), oud=lambda f, d: pluck(f, d, 0.8, 3.5), harpsi=lambda f, d: pluck(f, d, 0.6, 4.0) * 0.8, uke=lambda f, d: pluck(f, d, 1.6, 5), surf=lambda f, d: np.tanh(pluck(f, d, 0.5, 2) * 3) * 0.4,
         piano=piano, bell=bell, musicbox=lambda f, d: bell(f * 2, d, 1.5, 5, 3.5) * 0.8, kalimba=lambda f, d: bell(f, d, 0.9, 5.4, 4.5), chipbell=lambda f, d: square(f * 2, d, 0.125) * np.exp(-T(d) * 6), epiano=epiano,
         saw=lambda f, d: filt(saw(f, d), 3500), brass=brass, mute=lambda f, d: filt(brass(f, d), 1800) * 1.3, suona=suona, flute=flute, organ=organ, strings=strings, square=square, pulse=lambda f, d: filt(square(f, d, 0.25) + square(f * 1.005, d, 0.25), 3000),
         tri=tri, sbass=sbass, tuba=lambda f, d: filt(saw(f, d, 10, 0.02, 0.06), 600) * 1.6, synbass=lambda f, d: filt(saw(f, d, 16, 0.003, 0.05), 900) * 1.2)
# ---- 鼓 ----
def noise(d): return rng.normal(0, 1, max(1, int(d * SR)))
def kick(g=1): t = T(0.45); return np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 7) * g
def snare(g=1): t = T(0.25); return (filt(noise(0.25), 1500, 'high') * np.exp(-t * 18) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.6) * g
def hat(g=1): t = T(0.07); return filt(noise(0.07), 7000, 'high') * np.exp(-t * 60) * 0.5 * g
def tom(f=150, g=1): t = T(0.4); return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t * 20))) / SR) * np.exp(-t * 8) * g
def wood(f=1100, g=1): t = T(0.08); return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.6 * t)) * np.exp(-t * 60) * g
def chipn(g=1, d=0.08): t = T(d); return np.repeat(rng.choice([-1.0, 1.0], len(t) // 20 + 1), 20)[:len(t)] * np.exp(-t * 40) * 0.4 * g
DF = dict(k=kick, s=snare, h=hat, t=lambda g: tom(110, g), T=lambda g: tom(70, g) * 1.4, w=wood, W=lambda g: wood(800, g), c=lambda g: chipn(g), C=lambda g: filt(square(80, 0.08), 400) * np.exp(-T(0.08) * 30) * 2 * g)
# 一小节 16 格：每个字符一格，'.' 空，大写=重音
DR = {'none': '', 'light': 'k...h.......h...', 'rock': 'k.h.s.h.k.k.s.h.', 'four': 'k.h.k.h.k.h.k.h.', 'jazz': 'k...w..hk...w..h', 'tribal': 'T..t..t.T..t.t.t', 'taiko': 'T.....T.T...w.w.', 'darbuka': 't..WW.t.W.W.t.W.',
      'wood': 'w...W...w...W.w.', 'march': 'k...s.s.k...ss.s', 'chip': 'C.c.c.c.C.c.c.c.', 'tick': 'W...W...W...W...', 'lofi': 'k...s..k....s...'}
# 画风 → (主旋律, 八度, 和声, 和声型, 贝斯, 贝斯型, 鼓, 五声音阶)
KIT = {'base': ('piano', 0, 'strings', 'pad', 'sbass', 'whole', 'none', 0), 'pixel': ('square', 12, 'square', 'arp16', 'tri', 'pulse8', 'chip', 0),
 'porcelain': ('pluck', 0, 'pluck', 'arp8', 'sbass', 'whole', 'wood', 1), 'cave': ('flute', 0, None, None, 'sbass', 'quarter', 'tribal', 1), 'sand': ('kalimba', 12, 'kalimba', 'arp16', 'sbass', 'whole', 'light', 1),
 'glass': ('organ', 0, 'organ', 'pad', 'organ', 'whole', 'none', 0), 'stitch': ('musicbox', 0, 'musicbox', 'arp8', None, None, 'none', 0), 'engraving': ('harpsi', 0, 'harpsi', 'arp16', 'harpsi', 'quarter', 'none', 0),
 'mucha': ('pluck', 12, 'strings', 'pad', 'sbass', 'whole', 'light', 0), 'shoujo': ('bell', 12, 'strings', 'pad', 'sbass', 'half', 'light', 0), 'ukiyoe': ('flute', 12, 'koto', 'arp8', 'sbass', 'whole', 'taiko', 1),
 'monet': ('piano', 12, 'piano', 'arp8', 'sbass', 'whole', 'none', 0), 'turner': ('strings', 0, 'strings', 'pad', 'strings', 'whole', 'taiko', 0), 'vermeer': ('harpsi', 12, 'strings', 'pad', 'sbass', 'half', 'none', 0),
 'noir': ('mute', 0, 'piano', 'stab', 'sbass', 'walk', 'jazz', 0), 'rubberhose': ('piano', 12, 'piano', 'oom', 'tuba', 'oom', 'wood', 0), 'vangogh': ('strings', 12, 'piano', 'arp16', 'sbass', 'whole', 'light', 0),
 'klimt': ('bell', 12, 'strings', 'pad', 'sbass', 'half', 'light', 0), 'futurism': ('saw', 0, 'saw', 'stab', 'synbass', 'pulse8', 'march', 0), 'thermal': ('pulse', 12, 'pulse', 'arp16', 'synbass', 'pulse8', 'four', 0),
 'deco': ('brass', 0, 'piano', 'stab', 'sbass', 'walk', 'jazz', 0), 'ink': ('flute', 12, 'pluck', 'arp8', 'sbass', 'whole', 'none', 1), 'puppet': ('pluck', 12, 'pluck', 'arp16', 'sbass', 'quarter', 'wood', 1),
 'papercut': ('suona', 12, 'pluck', 'arp8', 'sbass', 'quarter', 'wood', 1), 'felt': ('uke', 12, 'kalimba', 'arp8', 'sbass', 'half', 'light', 0), 'blueprint': ('pulse', 0, 'square', 'arp16', 'sbass', 'pulse8', 'tick', 0),
 'paint': ('square', 12, 'organ', 'stab', 'synbass', 'quarter', 'rock', 0), 'escher': ('harpsi', 0, 'harpsi', 'arp16', 'harpsi', 'quarter', 'tick', 0), 'ps1': ('epiano', 12, 'strings', 'pad', 'synbass', 'half', 'lofi', 0),
 'pop': ('surf', 0, 'surf', 'stab', 'synbass', 'pulse8', 'rock', 0), 'flash': ('saw', 12, 'pulse', 'arp16', 'synbass', 'pulse8', 'four', 0), 'dressup': ('chipbell', 12, 'bell', 'arp8', 'sbass', 'half', 'four', 0),
 'vapor': ('epiano', 0, 'strings', 'pad', 'synbass', 'half', 'lofi', 0), 'nes': ('square', 12, 'square', 'arp16', 'tri', 'pulse8', 'chip', 0), 'ascii': ('square', 0, None, None, 'tri', 'quarter', 'chip', 0)}
SCALE = [0, 2, 4, 5, 7, 9, 11] if O.mood == 'dreamy' else [0, 2, 3, 5, 7, 8, 10]; PENTA = [0, 3, 5, 7, 10]
CHA, CHB = ([[53, 57, 60, 64], [55, 59, 62]], [[52, 55, 59], [57, 60, 64]]) if O.mood == 'dreamy' else ([[57, 60, 64], [53, 57, 60]], [[48, 52, 55], [55, 59, 62]])
MELA = [(0, 0, 3), (3, 2, 1), (4, 4, 4), (8, 3, 2), (10, 2, 2), (12, 1, 4), (16, 2, 3), (19, 4, 1), (20, 5, 4), (24, 4, 2), (26, 6, 2), (28, 7, 4)]
MELB = [(0, 4, 3), (3, 5, 1), (4, 7, 4), (8, 6, 2), (10, 5, 2), (12, 4, 4), (16, 3, 3), (19, 2, 1), (20, 1, 4), (24, 0, 2), (26, 1, 2), (28, 0, 4)]
def note(d, penta):
    o, i = divmod(d, 7); m = 69 + 12 * o + SCALE[i]; r = (m - 69) % 12
    if penta and r not in PENTA: m += min((p - r for p in PENTA + [12]), key=lambda x: (abs(x), -x))
    return m
SUS = {'flute', 'strings', 'brass', 'mute', 'suona', 'organ', 'saw', 'pulse'}
for c in CUES:
    k, t0 = c['k'], c['t0']; last = k == len(CUES) - 1; lead, lo, harm, hp, bass, bp, drums, penta = KIT['nes'] if O.mood == 'chip' else KIT.get(c['style'], KIT['base'])
    mel = (MELA if k % 2 == 0 else MELB)[6 if k == 0 else 0:]; chords = CHA if k % 2 == 0 else CHB
    for st, d, ln in mel: put('lead', t0 + st * S16, V[lead](hz(note(d, penta) + lo), ln * S16 * (1 if lead in SUS else 0.95)), 0.32)
    for b in range(2):
        cb = [m + (12 if harm in ('bell', 'musicbox', 'kalimba') else 0) for m in chords[b]]; tb = t0 + b * 16 * S16; r = chords[b][0] - (24 if chords[b][0] > 50 else 12)
        if not harm: pass
        elif hp == 'pad': [put('harm', tb, V[harm](hz(m), 16 * S16), 0.10) for m in cb]
        elif hp in ('arp8', 'arp16'): stp = 2 if hp == 'arp8' else 1; sq = cb + [cb[1], cb[2] + 12, cb[1]]; [put('harm', tb + s * S16, V[harm](hz(sq[i % len(sq)]), stp * S16 * 1.5), 0.09) for i, s in enumerate(range(0, 16, stp))]
        elif hp == 'stab': [put('harm', tb + s * S16, V[harm](hz(m), S16 * 1.6), 0.07) for s in (2, 6, 10, 13) for m in cb]
        elif hp == 'oom': [put('harm', tb + s * S16, V[harm](hz(m), S16 * 2), 0.08) for s in (4, 12) for m in cb]
        if bass:
            pat = {'whole': [(0, 0, 16)], 'half': [(0, 0, 8), (8, 7, 8)], 'quarter': [(s, [0, 0, 7, 12][s // 4], 4) for s in (0, 4, 8, 12)], 'pulse8': [(s, 12 if s % 4 == 2 else 0, 2) for s in range(0, 16, 2)],
                   'walk': [(s, [0, 3, 5, 7][s // 4], 4) for s in (0, 4, 8, 12)], 'oom': [(0, 0, 3), (8, 7, 3)]}[bp]
            [put('bass', tb + s * S16, V[bass](hz(r + iv), ln * S16 * 0.92), 0.33) for s, iv, ln in pat]
        if 0 < k and not last:
            for s, ch in enumerate(DR[drums]):
                if ch != '.': put('drum', tb + s * S16, DF[ch](1.0 if ch.isupper() else 0.6), 0.5)
    if last: [put('harm', t0 + 1.4, piano(hz(m), 4.0), 0.12) for m in (57, 60, 64, 69, 76)]; put('bass', t0 + 1.4, sbass(hz(33), 4.0), 0.4)
# ---- 音效 ----
def sweep(d, f0, f1, nb=6):
    n = noise(d); y = np.zeros(len(n)); fs = np.geomspace(f0, f1, nb); cc = np.linspace(0, nb - 1, len(n))
    for j, f in enumerate(fs): y += filt(n, [f * 0.7, min(18000, f * 1.4)], 'band') * np.clip(1 - np.abs(cc - j), 0, 1)
    return y
def whoosh(d=0.35, f0=500, f1=4000, g=1): return sweep(d, f0, f1) * np.sin(np.pi * T(d) / d) ** 2 * g * 1.5
def slurp(f0, f1, d=0.3, g=1): t = T(d); return np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR) * env(len(t), 0.005, 0.05) * g
def crackle(d=0.5, g=1):
    y = np.zeros(int(d * SR))
    for _ in range(60): i = int(rng.uniform(0, 0.8) * len(y)); s = y[i:i + 180]; s += rng.normal(0, 1, len(s)) * np.exp(-np.arange(len(s)) / 40) * rng.uniform(0.3, 1)
    return filt(y, 1200, 'high') * np.exp(-T(d) * 3) * g
def boom(g=1): t = T(1.4); return (np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.5) + filt(noise(1.4), 300) * np.exp(-t * 6) * 0.5) * g
def arp(fs, step=0.05, g=1, kind='sq'):
    y = np.zeros(int((len(fs) * step + 0.1) * SR))
    for i, f in enumerate(fs): x = square(f, step * 1.1) if kind == 'sq' else np.sin(2 * np.pi * f * T(step * 1.1)) * env(int(step * 1.1 * SR)); j = int(i * step * SR); y[j:j + len(x)] += x[:len(y) - j]
    return y * g
def ding(f=1568, g=0.5): return bell(f, 0.5, 1.2, 2.0, 3.0) * g
def mixn(*xs): n = max(len(x) for x in xs); y = np.zeros(n); [y.__setitem__(slice(0, len(x)), y[:len(x)] + x) for x in xs]; return y
SFX = {'ding': lambda a: ding(a or 1568), 'thud': lambda a: mixn(tom(70), filt(noise(0.15), 500) * np.exp(-T(0.15) * 30) * 0.5), 'stomp': lambda a: mixn(tom(60, 0.6), filt(noise(0.1), 300) * 0.4),
 'whoosh': lambda a: whoosh(0.4, 400, 3000, 0.6), 'charge': lambda a: slurp(150, 600, 0.25, 0.25), 'boing': lambda a: slurp(200, 500, 0.15, 0.35), 'plop': lambda a: slurp(900, 300, 0.18, 0.5), 'slurpdown': lambda a: slurp(600, 120, 0.8, 0.4),
 'shimmer': lambda a: mixn(*[np.pad(ding(f, 0.3), (int(i * 0.06 * SR), 0)) for i, f in enumerate([1568, 1976, 2349, 2637, 3136])]), 'beep': lambda a: arp([1800], 0.06, 0.25, 'sine'), 'beep2': lambda a: arp([a or 800], 0.05, 0.2),
 'shatter': lambda a: crackle(0.8, 1.0), 'slam': lambda a: mixn(tom(70, 0.6), wood(600, 0.2)), 'knock': lambda a: wood(500, 0.5), 'tick': lambda a: wood(3000, 0.25), 'snapthread': lambda a: crackle(0.3, 0.6),
 'rumble': lambda a: filt(noise(1.2), 120) * np.sin(np.pi * T(1.2) / 1.2) * 3 * 0.8, 'glitch': lambda a: chipn(0.8, 1.2), 'complete': lambda a: arp([784, 988, 1175, 1568], 0.07, 0.25), 'starfall': lambda a: arp([2637, 2349, 2093, 1760, 1568, 1319, 1175, 1047], 0.12, 0.2, 'sine'),
 'wind': lambda a: filt(noise(1.0), [300, 1600], 'band') * np.sin(np.pi * T(1.0)) ** 2 * 0.5, 'datafall': lambda a: arp([1200 - i * 90 for i in range(10)], 0.06, 0.15), 'datarise': lambda a: arp([300 + i * 90 for i in range(10)], 0.05, 0.15)}
if not O.no_sfx:
    AE = C['AE']
    for c in CUES:
        t0 = c['t0']
        if c['k'] < len(CUES) - 1: put('sfx', t0 + AE + 0.12, whoosh(0.32, 600, 5000), 0.25); put('sfx', t0 + AE + 0.24, mixn(*[np.sin(2 * np.pi * f * T(0.9)) * np.exp(-T(0.9) * 4) for f in (2637, 3951, 5274)]) * 0.25, 0.35); put('sfx', t0 + AE + 0.28, crackle(0.6), 0.5); put('sfx', t0 + AE + 0.3, boom(0.5), 0.4); put('sfx', t0 + L - 0.65, sweep(0.65, 300, 6000) * (T(0.65) / 0.65) ** 2 * 1.5, 0.18)
        if c['k'] > 0: put('sfx', t0, boom(), 0.35); put('drum', t0, filt(noise(1.6), 4000, 'high') * np.exp(-T(1.6) * 2.5) * 0.45, 0.4)
        for ev in c.get('sfx', []): put('sfx', t0 + ev[0], SFX.get(ev[1], lambda a: np.zeros(10))(ev[2] if len(ev) > 2 else None), 0.7)
# ---- 混音 ----
ir = filt(noise(1.8) * np.exp(-T(1.8) * 4.5), 5000); ir /= np.sqrt(np.sum(ir ** 2))
out = sum((filt(BUS[k], 30, 'high') * g + w * sg.fftconvolve(BUS[k], ir)[:N] * g) for k, (g, w) in {'lead': (1, .28), 'harm': (.9, .35), 'bass': (1, .05), 'drum': (.85, .12), 'sfx': (.9, .2)}.items())
out = np.tanh(out / (np.max(np.abs(out)) + 1e-9) * 1.6) * 0.89; end = int(DUR * SR); out[end - int(1.5 * SR):end] *= np.linspace(1, 0, int(1.5 * SR)); out = out[:end]
wf.write(here / 'score.wav', SR, (np.stack([out, np.roll(out, 220) * 0.98], 1) * 32767).astype(np.int16)); print('score.wav', round(len(out) / SR, 1), 's')
