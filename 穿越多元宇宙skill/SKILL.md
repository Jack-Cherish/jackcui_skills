---
name: painting-traveler-video
description: 做「横版像素角色穿越不同画作」短片：每进一幅画角色换成该画风，挥剑劈开裂缝进入下一幅，每章一个交互点，右上角标注，配原创配乐。用户想做画中穿越、画风切换类视频时使用。
---

# 画中穿越横版视频（Painting Traveler）

效果：一个像素角色从左往右走，穿过一幅接一幅的画作（青花瓷、岩画、浮世绘、莫奈、梵高、8-bit……）。
- 每进一幅画，角色本身换成那幅画的画风（不是贴原图，是画风迁移）。
- 每章约 5.5 秒：走几步 → 一个交互点（骑上画里的野牛、跳一跳踩荷叶、被提线操纵、世界转 90°……）→ 挥剑劈开空间裂缝 → 走进下一幅；裂缝边扫过身体时，进缝的那一半先变成新画风。
- 右上角标注「编号 / 画风名 / 年代」，可选左上角表情头像框；原创配乐同一主旋律、每章换乐器，音效对齐挥剑和交互点。

全部由代码完成：`traveler/` 下的引擎（Canvas + Playwright 逐帧渲染 + ffmpeg）由一个 `film.json` 驱动。

## 包内文件
- `scripts/`：引擎和工具（`hero.js styles.js engine.js index.html cut_sheet.py render.py score.py`），开工时复制到项目目录 `traveler/`。
- `example/`：一个能直接跑的示例项目——原作女主切好的动作（sprites/）、表情（faces/）、34 张背景板（plates/）和 14 章的 `film.json`（覆盖 intro/birds/ride/hop/charge/panels/rain/seam/rods/rotate/loading/fallin/ascii/outro）。
  ```bash
  cp -r <skill目录>/example traveler && cp <skill目录>/scripts/* traveler/ && cd traveler
  python render.py stills 1.0,7.3,13.9,18.75 && python score.py && python render.py video --mb 28
  ```
- `references/heroine/`：女主原始设定表（侧面、正面、部件拆分、补充动作、跌落落地、表情），用来示范动作表应该怎么画——洋红底、侧面朝右、每格一个动作。
- `references/examples/`：成片效果参考——每章交互点总览、裂缝穿越瞬间、35 种画风一览、交互样片关键帧。给用户解释效果或自查画面时打开看。

## 工作流：逐步让用户选择

每一步都用 AskUserQuestion 给出选项（附推荐项），用户答完再进下一步；用户说「你定」就用推荐项并在回复里写明。每一步产出的东西立刻落到 `film.json` 或素材目录里。

### 第 0 步：搭项目（不用问）
1. 在工作目录建 `traveler/`，把本 skill 的 `scripts/` 下 7 个文件复制进去（想先看效果，就按「包内文件」里的命令先跑 example）。
2. 建子目录 `sprites/ faces/ plates/`。
3. 检查依赖：`python3 -c "import playwright, scipy, PIL, numpy"`、`ffmpeg -version`；缺什么就 `pip install --break-system-packages` 装什么，Chromium 用环境里已装的（不要 `playwright install`，除非确实没有浏览器）。

### 第 1 步：主角
问：「主角用什么？」
- **用你的像素动作表（推荐）**：纯洋红（或绿幕）底、侧面朝右。最少要三行各 4 帧：待机 idle、走路 walk、挥剑 slash。可选：正面 front、单张动作（leap 跳、crouch 蹲、land_crouch 落地、hips 叉腰、surprise 惊讶、reach 伸手、point 指、think 托腮、laugh 开心、shy 害羞、push 推、pull 拉、tired 累、fall_up1/fall_up2 下坠、kneel 跪、rise 起身），以及表情头像表（neutral/surprise/worry/sideeye/determined/blush/smile/laugh…）。
- 动作表的画法参考 `references/heroine/`。
- **只有一张角色图**：请用户按上面的清单出动作表（AI 生图或画师），先用现有的跑通；缺的动作引擎会自动用 idle 代替。
- 不要复刻已有版权角色（动漫/游戏角色、品牌吉祥物），用原创角色。

切图：
```bash
cd traveler
python cut_sheet.py 动作表.png --probe                     # 看每个人物的高度
python cut_sheet.py 动作表.png side_00,side_01,...  --scale 1.0   # 站立人物高约 345px 时 scale=1；否则 scale=345/高度
python cut_sheet.py 表情表.png neutral,surprise,... --faces
```
名字按「从上到下、从左到右」对应。然后把名字写进 `film.json.hero.poses`（idle/walk/slash/front 是 4 帧数组，其他是单张名字）和 `hero.faces`。
切完立刻 `python render.py sheet` 出 `style_sheet.png`（角色在 35 种画风下的样子）给用户看。

### 第 2 步：规模
问：「做几幅画？」选项：8 幅（约 55 秒）/ 16 幅（约 1 分 40 秒）/ 32 幅（约 3 分钟）/ 自定。
总时长 = (画作数 + 1) × chapterLen + 4.6 秒，chapterLen 默认 5.5（4.5–7 之间可调，越长交互越从容）。第一章是开场（空白画布 + intro），最后一章是结尾（outro），不计入编号。

### 第 3 步：选画作和画风
给用户看「画风目录」（下表），问要哪些（multiSelect，可分几轮问，每轮最多 4 项，或者先由你按「古→今」排好一版让用户删改）。

| style 键 | 适合的画作/世界 | 标注示例 |
|---|---|---|
| porcelain | 青花瓷 | 青花瓷 · 明代瓷绘 |
| cave | 洞穴岩画 | 洞穴岩画 · 旧石器时代 |
| sand | 灯箱沙画 | 沙画 |
| glass | 哥特彩色玻璃 | 彩色玻璃 · 13 世纪 |
| stitch | 十字绣 | 十字绣 · 民间刺绣 |
| engraving | 丢勒铜版画 | 铜版画 · 丢勒 1515 |
| mucha | 慕夏新艺术 | 新艺术运动 · 1900 |
| shoujo | 70 年代少女漫画 | 少女漫画 · 1970s |
| ukiyoe | 北斋浮世绘 | 浮世绘 · 1831 |
| monet | 莫奈睡莲 | 印象派 · 1899 |
| turner | 透纳风暴 | 浪漫主义 · 1842 |
| vermeer | 维米尔室内 | 荷兰黄金时代 |
| noir | 黑色电影 | 1940 年代 |
| rubberhose | 30 年代橡皮管动画 | 1930s |
| vangogh | 梵高星夜 | 后印象派 · 1889 |
| klimt | 克里姆特金色时期 | 维也纳分离派 |
| futurism | 未来主义 | 1910s |
| thermal | 热成像 | 红外 |
| deco | 装饰艺术海报 | 1930s |
| ink | 水墨写意 | 宋元 |
| puppet | 皮影戏 | 中国民间 |
| papercut | 剪纸 | 中国民间 |
| felt | 毛毡手作 | 手作 |
| blueprint | 工程蓝图 | 晒图 |
| paint | Windows 画图 | 1998 |
| escher | 埃舍尔不可能空间 | 1953 |
| ps1 | PS1 低多边形 | 1990s |
| pop | 波普漫画 | 1960s |
| flash | Flash 动画 | 2000s |
| dressup | 换装网页 | 2000s |
| vapor | 蒸汽波 | 2010s |
| nes | 8-bit 红白机 | 1980s |
| ascii | 字符画 | ASCII |
| pixel / base | 原样像素 / 原图 | 开场、结尾 |

**背景板（plates/）**：每章一张图，任何尺寸都行（会铺满 1600×900 再放大 1.3 倍供横移），画面里**不要有人物**，地面大约在画面下方 4% 处（角色脚踩 y=866/900）。来源三选一（每章可不同，问用户）：
- 用户自己的图（判断能否直接当背景：太小、有人物、有水印的不行）；
- 公有领域名画（作者去世超过 70 年，如北斋、莫奈、梵高、慕夏、维米尔、丢勒）；
- 你用 Canvas 代码画一张该画风的场景：**先用网络搜索找参考图，再画**；要模仿质感（笔触、网点、刻线、针脚），不要用细线去“描”。画好用 Playwright 截成 PNG 放进 plates/。

每章写进 film.json：`{ "plate": "plates/xx.png", "name": "画风名", "era": "年代", "style": "键", "color": "#裂缝和标注的主色" }`。

### 第 4 步：每章的交互点
先按下表给每章配一个推荐交互（参考「推荐」列），整理成一张表给用户看，再问「哪些要换？」。用户换的章节逐一给 2–4 个候选。

| act.type | 发生什么 | 参数 | 需要的动作（缺了用 idle） | 推荐用在 |
|---|---|---|---|---|
| intro | 开场：待机→托腮→指向前方→出发 | – | think, point | 开场 |
| outro | 结尾：停下、开心、转正面、淡出 | – | laugh, front | 结尾 |
| walk | 只走路 | – | – | 任意 |
| birds | 走近时画里的鸟惊飞，她停下伸手 | color | reach | 青花瓷、剪纸、埃舍尔 |
| ride | 画里的物体活过来变大，她跳上去骑一段 | crop[x,y,w,h]（原图坐标），rideScale，patch[dx,dy]，dust | leap, hips, land_crouch | 岩画（野牛）、细密画 |
| charge | 画里的物体冲过来，她转正面跳起躲开再叉腰 | crop, patch, jump | surprise, leap, land_crouch, hips | 铜版画（犀牛） |
| hop | 跳一跳：蓄力→跳到下一个落点，计分「+2 完美!」 | points[[x,y]…]（pan=0 时的屏幕坐标，选画里的荷叶/石头） | crouch, leap, land_crouch, hips | 莫奈、浮世绘 |
| rain | 连劈两剑，金箔/花瓣/毛毡球/金币落下堆在地上 | kind: gold/petals/felt/coins，colors | slash, laugh | 克里姆特、少女漫画 |
| frame | 画框落下，时间静止，她走出画框留下肖像 | – | think | 维米尔 |
| shadow | 影子先她一步走掉 | – | surprise, think | 黑色电影 |
| panels | 画面分成漫画格：全身 + 表情特写 + 拟声字 | look: shoujo/pop，faces[2]，text，pose | shy/point + 表情头像 | 少女漫画、波普 |
| target | 准星锁定 → 劈碎 | text | surprise | 热成像 |
| rods | 提线木偶：杆子接上手，被操纵，砍断 | – | fall_up1/2, surprise, leap | 皮影戏 |
| rotate | 整个世界绕脚下转 90°，接着在墙上走 | – | surprise | 埃舍尔 |
| glitch | 穿模/录像带撕裂 | – | tired | PS1、蒸汽波 |
| ascii | 身体散成字符落下再重组 | color | surprise | 字符画 |
| fallin | 从天上掉进来：下坠→落地→跪→起身→害羞 | color | fall_up1/2, land_crouch, kneel, rise, shy | 毛毡 |
| loading | 加载条挡路，她跳上去走到 100% | – | leap | Flash |
| poster | 光柱 + 标题字一个个砸下来，海报定格 | text, pose, color | hips | 装饰艺术、慕夏 |
| starcatch | 一颗星/光球旋转落到她举起的手上，光圈荡开 | color, color2 | reach, laugh | 梵高 |
| wind | 顶风前进，阵风把她往后推 | color | push | 透纳 |
| seam | 针在前方绣出一列十字针脚，她拉线，劈缝时挑断 | color [r,g,b] | pull | 十字绣 |

头像框：`"portraits": [["surprise", 1.0, 1.8]]`（表情名, 出现秒, 消失秒），建议放在惊讶/得意的时刻；头像会按画风自动变色。

### 第 5 步：穿越方式
问：「怎么进入下一幅？」
- **rift 劈开空间裂缝（推荐）**：挥剑 → 发光锯齿裂缝 → 撑满画面。
- **tear 撕纸**：下一幅从右往左像撕开的纸一样扫过来。
- **wipe 刷子**：一笔宽笔刷扫过换画。
写进 `"crossing"`。

### 第 6 步：标注与头像
问：「右上角标注要吗？头像框要吗？」默认都要。`"label": false` 关闭标注；头像框按第 4 步的 portraits 增删。

### 第 7 步：音乐
问：「配乐风格？」
- **adventure（推荐）**：A 小调冒险，每章换乐器（青花瓷古筝、浮世绘尺八太鼓、黑色电影弱音小号、8-bit 方波……）。
- **dreamy**：大调、柔和。
- **chip**：全程 8-bit 芯片音乐。
- **不要音乐**：只渲染画面。
是否要音效（挥剑、裂缝、交互点）：默认要；不要就加 `--no-sfx`。

### 第 8 步：预览和修改（必做）
```bash
python render.py sheet                          # 画风一览 style_sheet.png
python render.py stills 1.0,7.2,12.9,...         # 每章交互高潮时刻（第 k 章 = k×chapterLen + 秒数）→ stills/contact.jpg
```
**自己先看一遍 contact.jpg**，常见问题：
- 角色被背景吃掉 → 换 color 或画风；
- ride/charge 的 crop 框偏了 → 看原图坐标重框；
- hop 的落点不在叶子上 → 改 points；
- 背景里有烘焙进去的阴影或人物 → 换背景。

修好再发给用户，按反馈改 film.json 或背景，重复直到满意。

### 第 9 步：导出
```bash
python render.py stills 0.1                     # 顺便写出 cues.json（配乐要用）
python score.py --mood adventure                 # → score.wav
python render.py video --workers 2 --mb 28       # → film.mp4，1080p，两遍编码控制在 28MB 内（便于发送）
```
要高画质发布，就把 `--mb` 调大（如 120）。交付时附一张每章交互点的截图总览。

## film.json 示例

```json
{
  "title": "穿越者",
  "chapterLen": 5.5,
  "crossing": "rift",
  "hero": {
    "poses": {
      "idle": ["side_00","side_01","side_02","side_03"],
      "walk": ["side_10","side_11","side_12","side_13"],
      "slash": ["side_20","side_21","side_22","side_23"],
      "front": ["front_00","front_01"],
      "leap": "leap", "crouch": "crouch", "land_crouch": "land_crouch", "hips": "hips",
      "surprise": "surprise", "reach": "reach", "point": "point", "think": "think", "laugh": "laugh", "shy": "shy"
    },
    "faces": ["neutral","surprise","blush","smile","laugh"]
  },
  "chapters": [
    { "plate": "plates/blank.png", "name": "空白画布", "era": "起点", "style": "base", "color": "#ffffff", "act": { "type": "intro" }, "portraits": [["neutral", 0.55, 1.5]] },
    { "plate": "plates/cave.png", "name": "洞穴岩画", "era": "旧石器时代", "style": "cave", "color": "#ffb24a", "act": { "type": "ride", "crop": [950, 490, 220, 150], "rideScale": 1.9 } },
    { "plate": "plates/monet.png", "name": "印象派", "era": "莫奈 · 1899", "style": "monet", "color": "#ffe6a0", "act": { "type": "hop", "points": [[655,784],[945,676],[1356,868],[1697,883]] } },
    { "plate": "plates/shoujo.png", "name": "少女漫画", "era": "1970 年代", "style": "shoujo", "color": "#ffb8d6", "act": { "type": "panels", "look": "shoujo", "faces": ["surprise","blush"] } },
    { "plate": "plates/blank.png", "name": "空白画布", "era": "回到起点", "style": "base", "color": "#ffffff", "act": { "type": "outro" }, "portraits": [["smile", 2.3, 4.0]] }
  ]
}
```

## 坐标与时间约定
- 画面 1600×900（导出放大到 1920×1080）。角色站在屏幕 x=620，脚底 y=866；背景向左横移制造前进感。
- 背景图先等比铺满 1600×900，再放大 1.3 倍；原图坐标 (x,y) → 屏幕 (x·s − pan, y·s − 上下裁掉的一半)，`s = max(1600/宽, 900/高)×1.3`。ride/charge 的 crop 用原图坐标。hop 的 points 用 pan=0 时的屏幕坐标。
- 每章：0 → AE（= chapterLen − 1.5）是交互段；AE 挥剑；AE+0.3 裂缝打开；最后 0.65 秒裂缝撑满全屏，进入下一章。
- 预设里的时间都是「章内秒数」，按 5.5 秒章节设计；chapterLen 改动较大时检查一遍 stills。

## 扩展
- **新交互**：在 `engine.js` 的 `PRESETS` 里加一个函数，返回 `{ v 或 pan, hero, draw, sfx }`：
  - `v(lt)` 是背景横移速度（像素/秒），`hero(lt)` 返回姿势 `{kind, p, dx, dy, rot, sx, sy, ground, hidden, clip, fill}`；
  - `draw(ctx, lt, layer, E)` 在 back / front / post 三层画东西（E.Pn 是当前横移量，E.st 是当前姿势，E.style 是本章画风）；
  - `sfx` 是 `[[秒, 音效名, 参数]]`。
  - 用 `seq([[截止秒, 姿势函数], …])` 和 `vseq` 拼时间轴，最后一段之后自动接挥剑。
- **新画风**：在 `styles.js` 的 `STYLES` 里加一个函数，可用 `flat`（逐像素换色）、`cells`（每格画图形）、`glow`、`over`、`grain`、`thick` 这些工具；输入的每个像素有原色 c、明暗档 t（0/1/2）、是否轮廓 e。
- **新乐器编制**：在 `score.py` 的 `K` 表里按 style 键加一行（主旋律音色、八度、和声音色、和声型、贝斯音色、贝斯型、鼓型、是否五声音阶、增益）。
