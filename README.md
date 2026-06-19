<div align="center">

# 🎬 multi-agent-tts-html

**从口播稿到 MP4 视频，端到端一条流水线**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.5.3-blue.svg)](SKILL.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](requirements.txt)
[![Node](https://img.shields.io/badge/node-20%2B-green.svg)](https://nodejs.org)
[![Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](SKILL.md)

口播稿 → GATE 1 → TTS + 字幕 → 内容映射 → HyperFrames HTML → GATE 2 → MP4

[快速开始](#-快速开始) · [核心特性](#-核心特性) · [流水线](#-流水线) · [示例](#-示例作品) · [架构](#-架构) · [排错](#-排错)

</div>

---

## ✨ 这是什么

**multi-agent-tts-html** 是一个 Claude Code Skill，把"写口播稿 → 生成 MP4 视频"这条流水线标准化、自动化、可审核。

**核心理念**：写完口播稿，跑一条命令，30 分钟内拿到 1080p MP4 + SRT/VTT/JSON 字幕 + HyperFrames HTML 配方。

### 🎯 解决什么问题

| 痛点 | 解决方案 |
|------|---------|
| 写完口播稿直接调 TTS，AI 味爆表 | **GATE 1 强制审核**（10 项自检 + 人工签字）|
| 排版虚构内容（数字/人名/场景） | **7 条防虚构戒律** + 内容映射表 100% 覆盖 |
| 翻页节奏失控（8 分钟做 4 页） | **硬约束**：每页 10s ± 2s（封面/收尾 3-8s）|
| 字幕错位 / 黑屏 / 重叠 | HyperFrames timed div + GSAP timeline |
| 渲染时音视频不同步 | ffprobe 归一化（精度 ±0.3s）|
| 重复返工浪费 API 配额 | 硬约束 #1 **技术阻断**：不传 `--gate1-approved` 直接 exit(1) |
| 口播稿带"我跟你说/我有个朋友"等第一人称模板 | **硬约束 #5**：禁用第一人称，GATE 1 核查 `我` count = 0 |
| 视觉风格飘忽（深/浅混搭、字号混乱） | **🎨 视觉风格规范（v1.5.0）**：浅色风格色板 + 首页封面模板 + 8 页版式 |
| 首页文字偏小没封面观感 | **首页封面规范（v1.5.0 强制）**：148px / 900 字重 + 角标 + 页码 + 渐变背景 |
| 字幕太碎（"<10 字句"过多，观众跟不上画面） | **硬约束 #6**：每段字幕中文字符数 ≥ 10 字，min_chars=10/ideal=18/max=22，SubsGen.py 默认值已改 |
| 字幕切散自然句（次级标点优先级过强，"过去的玩法是做一个 App，大家来用"被拆成两半破坏语义）| **🎯 v1.5.3 第一原则：按自然句断句**：自然句边界（。！？）神圣不可破，次级标点（,;:、——）只在单自然句 > 22 字时作为内部拆分点，绝不跨自然句切句 |

---

## 🚀 快速开始

### 环境要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.10 | TTS 脚本运行环境 |
| Node.js | ≥ 20 | HyperFrames 渲染器 |
| ffmpeg + ffprobe | 最新版 | 音视频处理 |
| **hyperframes** | ≥ 0.6 | [安装](https://www.npmjs.com/package/hyperframes) |

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/muruai2021/multi-agent-tts-html.git
cd multi-agent-tts-html

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装 HyperFrames（Node 全局包）
npm install -g hyperframes

# 4. 检查环境
hyperframes doctor
```

### 配置 API Key（可选，无 Key 走 Edge TTS 兜底）

```bash
# MiniMax TTS（推荐，6 个中文音色）
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY
# 申请地址: https://platform.minimaxi.com
```

### 30 分钟出片

```bash
# 1. 写口播稿（按 references/script-writer.md 10 条铁律）
# 2. 完成 GATE 1 审核（10 项自检全过 + 人工确认 A 通过）

# 3. TTS + 字幕（必须带 --gate1-approved，否则拒绝运行）
python scripts/tts-with-subs.py <口播稿.md> --md \
  --output <项目名> --all-subs --gate1-approved

# 4. HyperFrames HTML 排版（参照 SKILL.md Phase 3 规范）

# 5. 完成 GATE 2 审核（内容映射表 100% 覆盖）

# 6. 渲染 MP4
hyperframes init /tmp/<项目名> --example blank --non-interactive --skip-skills
cp <项目名>_hf.html /tmp/<项目名>/index.html
cp <项目名>.mp3 <项目名>.vtt /tmp/<项目名>/
cd /tmp/<项目名> && hyperframes render . -o <输出>.mp4 \
  --fps 30 --quality high --resolution 1080p --non-interactive
```

**输出**：1080p MP4（~2 MB / 30s 视频）+ SRT/VTT/JSON 字幕 + HyperFrames HTML 配方。

---

## 🎯 核心特性

### 🛡️ 4 条硬约束（必须死守）

| # | 约束 | 实现方式 |
|---|------|----------|
| 1 | **口播稿必须经 GATE 1 人工审定** | **技术阻断**：`--gate1-approved` flag 必传，否则 exit(1) |
| 2 | HTML 排版必须经 GATE 2 人工审定 | 文档约束 + 内容映射表审查 |
| 3 | **翻页节奏：每 10 秒一页**（封面/收尾 3-8s）| 模板内置时间计算 |
| 4 | **不虚构数字/场景/人物** | 7 条防虚构戒律 + 内容映射表 100% 覆盖 |

### 🎬 字幕规范（v1.4.0 标准化）

经多次实际渲染验证的最优值：

```css
#sub-bar { position: absolute; bottom: 118px; ... }
.sub-cue {
  font-size: 42px; font-weight: 700;
  padding: 21px 60px; letter-spacing: 1.5px;
  background: none;        /* ⚠️ 禁用黑色背景容器 */
  text-shadow:
    0 0 8px  rgba(0,0,0,1),
    0 2px 16px rgba(0,0,0,0.9),
    0 4px 28px rgba(0,0,0,0.7);   /* 三层阴影替代背景 */
}
```

### 🔄 自我迭代机制（v1.1.0 引入）

| 文件 | 作用 |
|------|------|
| `references/failure_case_log.md` | 三区错误案例日志（🔴未修复 / 🟡修复中 / ✅已修复）|
| `references/self-review-template.md` | 5 步复盘流程（现象→5 Why→影响→改进→闭环）|
| `references/test_pool.md` | 4 类测试（TC-SYN/FUNC/BOUND/SEC）+ 回归测试（RE-XXX）|

**闭环**：错误 → 复盘 → 修复 → 写测试 → 下次发布前回归验证。

### 🛠️ 引擎自动降级

```
有 MINIMAX_API_KEY → MiniMax TTS（中文 6 音色）
       ↓ 失败（rate limit / 网络）
       ↓
自动切 Edge TTS（pip install edge-tts，0 配额消耗）
       ↓
无 API Key → 直接 Edge TTS
```

---

## 📐 流水线

```
Phase 0.1  写口播稿（script-writer.md）
         ↓
      ⛔ GATE 1（人工审定，必停）—— 必须 --gate1-approved
         ↓
Phase 0.2  TTS 生成 MP3
         ↓
Phase 0.3  字幕生成（SRT / VTT / JSON）
         ↓
Phase 1     收集 3 个源
         ↓
Phase 2     内容映射表（防虚构关键）
         ↓
Phase 3     HyperFrames HTML 排版
         ↓
      ⛔ GATE 2（人工审定，必停）
         ↓
Phase 4     HyperFrames 渲染 MP4
```

**GATE 1 / GATE 2 是强制阻断点，未通过不能进入下游。**

详细规范见 [SKILL.md](SKILL.md)。

---

## 📁 目录结构

```
multi-agent-tts-html/
├── SKILL.md                      ← 主入口（v1.4.0 完整规范）
├── README.md                     ← 本文件
├── LICENSE                       ← MIT
├── requirements.txt              ← Python 依赖锁定
├── grading.json                  ← 4 维审核评分报告
├── .env.example                  ← 环境变量模板
│
├── references/                   ← 参考文档
│   ├── script-writer.md          ← 反 AI 味 10 条铁律
│   ├── content-mapping-template.md ← 7 条防虚构戒律
│   ├── failure_case_log.md       ← 错误案例日志
│   ├── self-review-template.md   ← 5 步复盘模板
│   └── test_pool.md              ← 测试用例池
│
└── scripts/                      ← 工具脚本
    ├── md2mp3.py                 ← MD → MP3（带 --gate1-approved 拦截）
    ├── tts-gen.py                ← 通用 TTS（MiniMax + Edge 兜底）
    ├── tts-with-subs.py          ← TTS + 字幕一键生成（带 --gate1-approved 拦截）
    └── SubsGen.py                ← 字幕生成模块（切句/时间戳/格式）
```

---

## 🎨 示例作品

**harness-intro v1**（首次完整使用本 skill 生成）

| 属性 | 值 |
|------|----|
| 主题 | 关于 harness 的技术介绍（Claude Code 视角）|
| 字数 | 184 中文字 |
| 时长 | 34.19 秒 |
| 分辨率 | 1920 × 1080 |
| 文件大小 | 1.91 MB |
| 翻页 | 4 页（cover / three-pillars / terminal / manuscript）|

**4 页设计**：

| 页 | 时段 | 版式 | 关键元素 |
|---|------|------|---------|
| 1 | 0-7s | cover-magazine | 240px "Harness?" 巨幅渐变标题 + 装饰网格 + 三色径向光晕 |
| 2 | 7-17s | three-pillars | 3 个玻璃拟态卡片 + 巨型半透明编号 + emoji 图标 |
| 3 | 17-27s | terminal | 多层阴影终端窗口 + 闪烁绿光标 + 脉冲点 |
| 4 | 27-34.16s | manuscript | 220px 巨型引号 + "对话就停了" + 圆角 CTA 徽章 |

**字幕**：13 cue，全部按 v1.4.0 规范（42px / 三层 text-shadow / 禁容器）。

完整产物在 `E:\work\video\harness视频\`（项目内未追踪，参考 [examples/](https://github.com/muruai2021/multi-agent-tts-html/tree/main/examples)）。

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│           Claude Code (宿主)                │
│                                             │
│  用户输入 → Skill 路由 → 加载 SKILL.md     │
│                ↓                            │
│  AI 调度：写稿 → 跑脚本 → 跑渲染器         │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│   scripts/  (Python)                        │
│   • tts-with-subs.py  → MiniMax / Edge TTS │
│   • SubsGen.py        → 字幕切句/归一化     │
│   • 内置 GATE 1 拦截（--gate1-approved）   │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│   references/  (Markdown)                   │
│   • script-writer.md   → 反 AI 味铁律      │
│   • content-mapping    → 防虚构戒律         │
│   • failure_case_log   → 自我迭代           │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│   HyperFrames CLI  (Node.js)                │
│   • Puppeteer headless Chrome               │
│   • GSAP timeline 驱动                      │
│   • ffmpeg 编码 H.264 + AAC                 │
└─────────────────────────────────────────────┘
```

---

## 📊 质量评分（4 维审核）

| 维度 | 得分 | 权重 |
|------|------|------|
| 🔒 安全性 | 94 | 30% |
| 🧩 逻辑性 | 94 | 25% |
| 🏗️ 稳定性 | 78 | 25% |
| 🔄 自我迭代 | 75 | 20% |
| **总分** | **86** | **优秀** |

完整报告见 [grading.json](grading.json)。

---

## 🔧 排错

### Q1: 字幕只有第一句 / 全黑屏
**原因**：JS visibility 切换在 HyperFrames 渲染时不工作。
**解决**：用 timed div 方案（每句独立 `class="clip"`）+ GSAP timeline，不要写 imperative `audio.play()`。详见 [SKILL.md Phase 3 章节](SKILL.md#phase-3--hyperframes-html-排版)。

### Q2: 页面全部重叠
**原因**：CSS 特异性冲突或缺 `visibility: hidden`。
**解决**：用 `.clip { visibility: hidden; }` + `.clip.active { visibility: visible; }`，不要加 `.clip[data-start="0"]` 兜底（会引发 F-002 复现）。

### Q3: TTS rate limit
**原因**：MiniMax RPM 配额用尽。
**解决**：自动降级 Edge TTS（无需 API Key），6 个中文内置音色。

### Q4: HyperFrames 渲染失败
**原因**：缺 `data-composition-id` / `class="clip"` / `audio id`。
**解决**：
```bash
hyperframes lint /tmp/<项目名>  # 看具体错误
```

### Q5: 音频与字幕不同步
**原因**：ffprobe 未归一化。
**解决**：提供 `audio_path` 参数触发 ffprobe 归一化（`tts-with-subs.py --audio-only` 模式）。

### Q6: GATE1 BLOCKED
**原因**：未传 `--gate1-approved` flag。
**解决**：
```bash
# 错误：python scripts/tts-with-subs.py 稿子.md --md --output x --all-subs
# 正确：python scripts/tts-with-subs.py 稿子.md --md --output x --all-subs --gate1-approved
```

更多问题见 [SKILL.md 排错表](SKILL.md#常见问题排查)。

---

## 📦 文件存放约定

> ⚠️ **重要**：所有**用户产物**（口播稿/音频/字幕/HTML/MP4）保存在**执行命令时的当前工作目录**，**不是** skill 安装目录、**也不是** `examples/` 子目录。

```bash
# 检查当前位置
pwd                    # macOS / Linux
cd                    # Windows CMD
```

**用户产物 7 类**：

```
<当前工作目录>/
├── <YYYYMMDD>_<关键词>_v1.md             ← 口播稿
├── <YYYYMMDD>_<关键词>_v1.mp3            ← TTS 音频
├── <YYYYMMDD>_<关键词>_v1.srt            ← SRT 字幕
├── <YYYYMMDD>_<关键词>_v1.vtt            ← WebVTT 字幕
├── <YYYYMMDD>_<关键词>_v1.segments.json  ← JSON 时间戳
├── <YYYYMMDD>_<关键词>_v1_hf.html        ← HyperFrames 配方
└── <YYYYMMDD>_<关键词>_v1.mp4           ← 最终视频
```

**常见错误**：在 skill 安装目录里跑命令，会污染 skill 源码。**先 cd 到项目目录再开工**。

---

## 🤝 贡献

欢迎贡献！请按以下流程：

1. **新错误录入**：触发 bug 后追加到 `references/failure_case_log.md`
2. **5 步复盘**：按 `references/self-review-template.md` 根因分析
3. **写回归测试**：在 `references/test_pool.md` 加 RE-XXX 用例
4. **修复代码** + 写 commit message（参考 git log）
5. **更新版本号** + 更新日志（`SKILL.md` 顶部）

**Commit 格式**：`<type>: <description>`（types: feat/fix/refactor/docs/test/chore/perf/ci）

**审核前必跑**：
```bash
hyperframes lint <项目>
python -m py_compile scripts/*.py
pytest tests/  # 如有
```

---

## 📜 许可证

[MIT](LICENSE) © 2026 Muru AI

---

## 🔗 关联资源

- [HyperFrames 官方文档](https://hyperframes.heygen.com)
- [MiniMax TTS 平台](https://platform.minimaxi.com)
- [Edge TTS (pip)](https://pypi.org/project/edge-tts/)
- [Claude Code Skills 文档](https://docs.claude.com/en/docs/claude-code/skills)

---

## 📝 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **1.4.0** | 2026-06-14 | 🎬 字幕样式规范固化：42px / 三层 text-shadow / 禁容器 / bottom 118px |
| **1.3.0** | 2026-06-14 | 🛑 GATE 1 强制阻断：脚本必须传 `--gate1-approved` 否则 exit(1) |
| **1.2.1** | 2026-06-14 | 🐛 F-002 复现修复（CSS 特异性冲突）|
| **1.2.0** | 2026-06-14 | 🎨 HTML 排版升级（巨幅标题 + 玻璃拟态 + 渐变光晕）|
| **1.1.2** | 2026-06-14 | 🐛 HTML 黑屏 bug 修复 |
| **1.1.1** | 2026-06-14 | 📁 文件存放约定固化 |
| **1.1.0** | 2026-06-14 | 📝 4 维审核 + 三大自我迭代文件 |
| **1.0.0** | 2026-06-14 | 🎉 初始版本：整合 multi-agent-mmx-tts + HyperFrames 渲染 |

完整变更见 [SKILL.md 更新日志](SKILL.md#更新日志)。

---

<div align="center">

**[⬆ 回到顶部](#-multi-agent-tts-html)**

Made with ❤️ by [Muru AI](https://github.com/muruai2021)

</div>