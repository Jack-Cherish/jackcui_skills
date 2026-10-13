# Painting Traveler · 画中穿越横版视频

一个给 **Claude Code** 和 **Codex** 用的 Agent Skill：让 AI 一步步带你做出「像素角色穿越一幅幅名画」的横版短片。

- 每进一幅画，角色换成那幅画的画风（画风迁移，不是贴图）
- 每章一个交互点：骑上岩画野牛、在莫奈睡莲上跳一跳、被皮影提线操纵、埃舍尔世界转 90°……
- 挥剑劈开空间裂缝进入下一幅；右上角标注画风与年代
- 原创配乐：同一主旋律，每章换乐器，音效对齐挥剑和交互
- 全部由代码完成：Canvas 引擎 + Playwright 逐帧渲染 + ffmpeg 合成，一个 `film.json` 驱动

---

## 目录结构

```
painting-traveler-video/
├── SKILL.md              # 给 AI 看的工作流（技能本体）
├── README.md             # 给人看的说明（本文件）
├── requirements.txt      # Python 依赖
├── scripts/              # 引擎与工具
│   ├── engine.js         #   时间轴、22 种交互预设、裂缝/撕纸/刷子转场
│   ├── styles.js         #   35 种画风迁移
│   ├── hero.js           #   角色精灵加载与像素化
│   ├── index.html        #   渲染页面
│   ├── cut_sheet.py      #   切动作表 / 表情表
│   ├── render.py         #   截图预览、画风一览、导出视频
│   └── score.py          #   合成配乐和音效
├── example/              # 可直接运行的示例项目
│   ├── film.json         #   14 章示例配置
│   ├── sprites/          #   切好的角色动作
│   ├── faces/            #   表情头像
│   └── plates/           #   34 张背景板
├── references/
│   ├── heroine/          # 角色设定表示范（洋红底、侧面朝右、每格一个动作）
│   └── examples/         # 成片效果参考图
```

## 环境要求

| 依赖 | 安装 |
|---|---|
| Python 3.9+ | — |
| Python 包 | `pip install -r requirements.txt` |
| Chromium（Playwright 用） | `python -m playwright install chromium` |
| ffmpeg | macOS `brew install ffmpeg` · Ubuntu `sudo apt install ffmpeg` · Windows `winget install ffmpeg` |

检查：

```bash
python -c "import playwright, scipy, PIL, numpy; print('ok')" && ffmpeg -version | head -1
```

## 不用 AI，先跑示例

```bash
git clone https://github.com/<你的用户名>/painting-traveler-video.git
cd painting-traveler-video
cp -r example traveler && cp scripts/* traveler/ && cd traveler

python render.py stills 1.0,7.3,13.9,18.75   # 预览截图 → stills/contact.jpg
python score.py                               # 配乐 → score.wav
python render.py video --mb 28                # 成片 → film.mp4（1080p，≤28MB）
```

---

## 在 Claude Code 里用

### 1. 安装

**全局安装**（所有项目可用）：

```bash
git clone https://github.com/<你的用户名>/painting-traveler-video.git ~/.claude/skills/painting-traveler-video
```

**只装在某个项目里**（会跟着仓库提交）：

```bash
cd 你的项目
git clone https://github.com/<你的用户名>/painting-traveler-video.git .claude/skills/painting-traveler-video
```

> Windows 把 `~/.claude` 换成 `%USERPROFILE%\.claude`。

### 2. 使用

在项目目录里启动 `claude`，然后二选一：

```
/painting-traveler-video
```

或直接说：

```
用我的角色做一个穿越 16 幅名画的横版视频，角色图在 ./hero.png
```

Claude 会自动加载技能，按步骤用选项卡问你：主角 → 几幅画 → 选画风 → 每章交互 → 转场方式 → 标注 → 音乐 → 预览修改 → 导出。不想选就回「你定」。

### 3. 更新

```bash
cd ~/.claude/skills/painting-traveler-video && git pull
```

---

## 在 Codex 里用

### 1. 安装

Codex 从 `.agents/skills` 目录读取技能。

**全局安装**：

```bash
git clone https://github.com/<你的用户名>/painting-traveler-video.git ~/.agents/skills/painting-traveler-video
```

**只装在某个仓库里**：

```bash
cd 你的仓库
git clone https://github.com/<你的用户名>/painting-traveler-video.git .agents/skills/painting-traveler-video
```

也可以在 Codex 里让自带的安装器装：

```
$skill-installer 从 https://github.com/<你的用户名>/painting-traveler-video 安装这个技能
```

装完没出现就重启 Codex。

### 2. 使用

启动 `codex`，然后：

```
$painting-traveler-video 用 ./hero.png 做一个穿越 8 幅画的视频
```

或输入 `/skills` 从列表里选，也可以直接描述需求让它自动匹配。

> Codex 没有选项卡，会用文字列出选项，回复编号或「你定」即可。
> Codex 默认在沙箱里运行，渲染要启动本地浏览器和 ffmpeg，如被拦截，请允许命令执行（或用 `codex --full-auto`）。

---

## 准备你自己的角色

1. 画一张**动作表**：纯洋红 `#FF00FF`（或绿幕）底，侧面朝右，每格一个动作。至少三行各 4 帧：待机、走路、挥剑。更多可选动作（跳、蹲、落地、叉腰、惊讶、伸手……）见 `SKILL.md` 第 1 步。
2. 可选：一张**表情头像表**（neutral / surprise / blush / smile / laugh …）。
3. 画法参考 `references/heroine/`。
4. 交给 AI 时告诉它文件路径即可，切图、命名、写配置都由它完成。缺的动作会自动用待机代替。

请使用原创角色，不要复刻已有版权角色。

## 自定义

- **改配置**：章节、画风、交互参数都在 `film.json`，字段说明见 `SKILL.md`。
- **新交互**：在 `engine.js` 的 `PRESETS` 里加函数。
- **新画风**：在 `styles.js` 的 `STYLES` 里加函数。
- **新乐器编制**：在 `score.py` 的 `K` 表里加一行。

## 常用命令

| 命令 | 作用 |
|---|---|
| `python cut_sheet.py 表.png --probe` | 查看动作表里每个人物的高度 |
| `python cut_sheet.py 表.png 名1,名2,... --scale 1.0` | 切动作 |
| `python cut_sheet.py 表情.png 名1,... --faces` | 切表情 |
| `python render.py sheet` | 35 种画风一览 → `style_sheet.png` |
| `python render.py stills 1.0,6.5,...` | 指定秒数截图 → `stills/contact.jpg` |
| `python score.py --mood adventure` | 配乐（adventure / dreamy / chip） |
| `python render.py video --workers 2 --mb 28` | 导出视频，`--mb` 控制文件大小 |

## 版权说明

- 代码：按你选择的开源协议发布（建议在仓库里加 `LICENSE`）。
- 示例角色：作者原创。
- 背景板：公有领域名画（北斋、莫奈、梵高、慕夏、维米尔、丢勒等）或按其画风生成、绘制的场景。替换成你自己的素材时，请确认有使用权。
