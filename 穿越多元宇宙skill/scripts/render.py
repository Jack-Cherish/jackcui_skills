"""渲染：python render.py stills 1.0,6.5,12  → stills/ 下的截图 + stills/contact.jpg
         python render.py sheet               → style_sheet.png（所有画风）
         python render.py video [--workers 2] [--mb 28] → frames/ → film.mp4（自动混 score.wav，控制在 mb 以内）"""
import base64, sys, os, json, time, subprocess, pathlib, shutil, argparse
from playwright.sync_api import sync_playwright
here = pathlib.Path(__file__).parent.resolve(); PORT = 8777
def serve(): p = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=here, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); return p
def page(p):
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1600, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_function('window.LOADED === true', timeout=120000); return b, pg, errs
def grab(pg, t): return base64.b64decode(pg.evaluate(f'frame({t})').split(',', 1)[1])
def worker(k, n, total, fps):
    with sync_playwright() as p:
        b, pg, errs = page(p)
        for i in range(k, total, n):
            f = here / 'frames' / f'{i:05d}.jpg'
            if not f.exists(): f.write_bytes(grab(pg, i / fps))
        b.close(); print('worker', k, 'done', errs[:3])
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('times', nargs='?', default=''); ap.add_argument('--workers', type=int, default=2); ap.add_argument('--mb', type=float, default=28); ap.add_argument('--fps', type=int, default=30); ap.add_argument('--worker', type=int, default=-1); o = ap.parse_args()
    if o.mode == 'worker':
        cfg = json.load(open(here / 'cues.json')); worker(o.worker, o.workers, int(cfg['DUR'] * o.fps), o.fps); sys.exit()
    srv = serve()
    try:
        with sync_playwright() as p:
            b, pg, errs = page(p); film = pg.evaluate('FILM'); json.dump(film, open(here / 'cues.json', 'w'), ensure_ascii=False); print('时长', round(film['DUR'], 1), '秒')
            if o.mode == 'sheet': (here / 'style_sheet.png').write_bytes(base64.b64decode(pg.evaluate('styleSheet()').split(',', 1)[1]))
            if o.mode == 'stills':
                out = here / 'stills'; shutil.rmtree(out, ignore_errors=True); out.mkdir(); ts = [float(x) for x in o.times.split(',') if x]
                for t in ts: (out / f'{t:07.2f}.jpg').write_bytes(grab(pg, t))
                from PIL import Image
                ims = [Image.open(f).resize((480, 270)) for f in sorted(out.glob('*.jpg'))]; cols = min(4, len(ims)); sheet = Image.new('RGB', (480 * cols, 270 * ((len(ims) + cols - 1) // cols)))
                for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
                sheet.save(out / 'contact.jpg', quality=85)
            b.close(); print('errors:', errs[:5])
        if o.mode == 'video':
            fr = here / 'frames'; shutil.rmtree(fr, ignore_errors=True); fr.mkdir()
            ps = [subprocess.Popen([sys.executable, __file__, 'worker', '--worker', str(k), '--workers', str(o.workers), '--fps', str(o.fps)]) for k in range(o.workers)]
            [q.wait() for q in ps]; dur = film['DUR']; vb = int((o.mb * 8 * 1024 * 1024 / dur - 128000) / 1000)
            base = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(o.fps), '-i', str(fr / '%05d.jpg')]; vf = ['-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vb}k', '-pix_fmt', 'yuv420p']
            subprocess.run(base + vf + ['-pass', '1', '-passlogfile', str(here / 'p'), '-an', '-f', 'mp4', os.devnull], check=True)
            aud = ['-i', str(here / 'score.wav'), '-c:a', 'aac', '-b:a', '128k', '-shortest'] if (here / 'score.wav').exists() else []
            subprocess.run(base + aud + vf + ['-pass', '2', '-passlogfile', str(here / 'p'), '-movflags', '+faststart', str(here / 'film.mp4')], check=True); print('film.mp4', round(os.path.getsize(here / 'film.mp4') / 1e6, 1), 'MB')
    finally: srv.terminate()
