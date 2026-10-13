"""把纯色背景（洋红/绿幕）的角色动作表切成单帧：每帧 362×362，脚底在 y=356，水平居中。
用法: python cut_sheet.py SHEET.png 名字1,名字2,... [--scale 1.0] [--out sprites] [--faces]
  名字按「从上到下、从左到右」的顺序对应表里的每个角色；--faces 输出原尺寸的表情头像到 faces/。
  --scale：让站立的人物高约 345px（看 --probe 打印的高度来定）。--probe 只打印检测到的每个人物尺寸。"""
import sys, os, argparse, numpy as np
from PIL import Image
from scipy import ndimage
def bgmask(a, key):
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    if key == 'green': return (g > 150) & (r < 120) & (b < 120)
    return (r > 110) & (b > 110) & (g < 120) & (np.abs(r - b) < 110) & (np.minimum(r, b) - g > 40)
def figures(a, key, min_area=4000):
    m = ~bgmask(a, key); lab, n = ndimage.label(ndimage.binary_dilation(ndimage.binary_opening(m), iterations=6)); out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if (lab[sl] == i).sum() >= min_area: out.append((sl[0].start, sl[0].stop, sl[1].start, sl[1].stop))
    out.sort(key=lambda b: (b[0] + b[1]) / 2); rows = []
    for b in out:
        cy = (b[0] + b[1]) / 2
        if rows and abs(cy - rows[-1][0]) < (b[1] - b[0]) * 0.5: rows[-1][1].append(b)
        else: rows.append([cy, [b]])
    return [b for _, bs in rows for b in sorted(bs, key=lambda b: b[2])]
def clean(crop, key):
    m = ~bgmask(crop, key); lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
    if n > 1: sz = ndimage.sum(m, lab, range(1, n + 1)); m &= lab == (np.argmax(sz) + 1)
    return Image.fromarray(np.dstack([crop, (m * 255).astype(np.uint8)]), 'RGBA')
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('sheet'); ap.add_argument('names', nargs='?', default=''); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--out', default=None)
    ap.add_argument('--faces', action='store_true'); ap.add_argument('--probe', action='store_true'); ap.add_argument('--key', default='magenta'); o = ap.parse_args()
    a = np.array(Image.open(o.sheet).convert('RGB')); bs = figures(a, o.key)
    if o.probe:
        for i, b in enumerate(bs): print(i, 'h', b[1] - b[0], 'w', b[3] - b[2])
        sys.exit()
    names = [n for n in o.names.split(',') if n]; out = o.out or ('faces' if o.faces else 'sprites'); os.makedirs(out, exist_ok=True)
    if len(names) != len(bs): print(f'警告：检测到 {len(bs)} 个人物，给了 {len(names)} 个名字')
    for n, (y0, y1, x0, x1) in zip(names, bs):
        img = clean(a[y0:y1, x0:x1], o.key)
        if o.faces: img.save(f'{out}/{n}.png'); continue
        if o.scale != 1: img = img.resize((round(img.width * o.scale), round(img.height * o.scale)), Image.NEAREST)
        if img.width > 358 or img.height > 352: s = min(358 / img.width, 352 / img.height); img = img.resize((round(img.width * s), round(img.height * s)), Image.NEAREST)
        cell = Image.new('RGBA', (362, 362)); cell.paste(img, (181 - img.width // 2, 356 - img.height), img); cell.save(f'{out}/{n}.png'); print(n, img.size)
