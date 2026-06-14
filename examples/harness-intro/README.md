# 示例：harness-intro v1

> 🎬 **关于 harness 的技术介绍**（Claude Code 视角）
>
> 本示例是 multi-agent-tts-html Skill **首次端到端跑通**的真实产物，完整覆盖 4 个 Phase + 2 个 GATE。

---

## 📊 基础信息

| 项 | 值 |
|---|---|
| **主题** | harness 是什么？（Claude Code 视角）|
| **字数** | 184 中文字 |
| **时长** | **34.19 秒**（实际音频 34.16s）|
| **分辨率** | 1920 × 1080 |
| **帧率** | 30 fps |
| **视频编码** | H.264 + AAC 48kHz 立体声 |
| **总文件** | 8 件（md / mp3 / srt / vtt / json / html / mp4 / mapping）+ 1 件 过程.md |
| **MP4 大小** | 1.91 MB |

---

## 🎨 4 页设计

| 页 | 时段 | 版式 | 关键元素 |
|---|------|------|---------|
| 1 | 0-7s | cover-magazine | 240px "Harness?" 巨幅渐变标题 + 装饰网格 + 三色径向光晕 |
| 2 | 7-17s | three-pillars | 3 个玻璃拟态卡片（调工具 / 读文件 / 跑命令）+ 巨型半透明编号 + emoji 图标 |
| 3 | 17-27s | terminal | 多层阴影终端窗口 + 闪烁绿光标 + 脉冲点 + 虚线分隔 |
| 4 | 27-34.16s | manuscript | 220px 巨型引号 + "对话就停了" + 90% 数字渐变 + 圆角 CTA 徽章 |

**翻页节奏核查**：7s / 10s / 10s / 7.16s，均在 3-12s 区间 ✅

---

## 🎬 字幕规范（v1.4.0）

| 属性 | 值 |
|------|-----|
| 字体大小 | 42px |
| 字体粗细 | 700 |
| 位置 | `bottom: 118px` |
| 背景 | **无**（禁用黑色容器）|
| text-shadow | **3 层堆叠**（8px 实心 + 16px 中距 + 28px 长距）|
| 字幕条数 | 13 cue（每句独立 `<div class="sub-cue clip">`）|

完整规范见 [SKILL.md 🎬 字幕样式规范](../../SKILL.md#-字幕样式规范v140-标准化)。

---

## 📁 产物清单（9 件）

| 文件 | 大小 | 用途 |
|------|------|------|
| [`20260614_harness-intro_v1.md`](20260614_harness-intro_v1.md) | 657 B | 口播稿（已通过 GATE 1）|
| [`20260614_harness-intro_v1.mp3`](20260614_harness-intro_v1.mp3) | 548 KB | TTS 音频（MiniMax 国语男声）|
| [`20260614_harness-intro_v1.srt`](20260614_harness-intro_v1.srt) | 1 KB | SRT 字幕 |
| [`20260614_harness-intro_v1.vtt`](20260614_harness-intro_v1.vtt) | 1 KB | WebVTT 字幕 |
| [`20260614_harness-intro_v1.segments.json`](20260614_harness-intro_v1.segments.json) | 2 KB | JSON 时间戳 |
| [`20260614_harness-intro_v1_hf.html`](20260614_harness-intro_v1_hf.html) | 17 KB | HyperFrames HTML 配方（GSAP timeline）|
| [`20260614_harness-intro_v1_mapping.md`](20260614_harness-intro_v1_mapping.md) | 4 KB | GATE 2 内容映射表（防虚构核查）|
| **`20260614_harness-intro_v1.mp4`** | **1.91 MB** | 🎬 **最终视频**（1080p / 30fps）|
| [`过程.md`](过程.md) | 6 KB | 完整生成过程记录 |

---

## 🚀 复现命令

```bash
# 0. 准备口播稿
# 见 20260614_harness-intro_v1.md

# 1. TTS + 字幕（必须带 --gate1-approved）
python scripts/tts-with-subs.py 20260614_harness-intro_v1.md \
  --md --output 20260614_harness-intro_v1 --all-subs --gate1-approved

# 2. HTML 排版：见 20260614_harness-intro_v1_hf.html
#    4 页设计 + 13 字幕 + GSAP timeline

# 3. 渲染 MP4
hyperframes init /tmp/harness-intro --example blank --non-interactive --skip-skills
cp 20260614_harness-intro_v1_hf.html /tmp/harness-intro/index.html
cp 20260614_harness-intro_v1.mp3 20260614_harness-intro_v1.vtt /tmp/harness-intro/
cd /tmp/harness-intro && hyperframes render . -o 20260614_harness-intro_v1.mp4 \
  --fps 30 --quality high --resolution 1080p --non-interactive
```

---

## 💡 本次生成遇到的问题（已修复进 Skill）

| ID | 问题 | 修复版本 |
|----|------|----------|
| F-007 | AI 把产物存到 examples/ 子目录（违反约定）| v1.1.1 |
| F-008 | 浏览器打开 HTML 全黑屏 | v1.1.2 |
| F-009 | F-002 复现（CSS 特异性冲突导致 4 页重叠）| v1.2.1 |
| F-010 | GATE 1 仅文档约束易绕过 | v1.3.0 |
| F-011 | 字幕样式每次重新调试 | v1.4.0 |

完整过程记录见 [`过程.md`](过程.md)。

---

## 🔗 关联资源

- [SKILL.md](../../SKILL.md) — 完整流水线文档
- [references/script-writer.md](../../references/script-writer.md) — 反 AI 味 10 条铁律
- [references/content-mapping-template.md](../../references/content-mapping-template.md) — 7 条防虚构戒律
- [references/failure_case_log.md](../../references/failure_case_log.md) — 11 条错误案例
- [references/test_pool.md](../../references/test_pool.md) — 11 条回归测试
- [grading.json](../../grading.json) — 4 维审核评分报告