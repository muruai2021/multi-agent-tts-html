---
name: multi-agent-tts-html
description: "Use when 用户需要：口播稿写作（反 AI 味 + 禁用第一人称）、MiniMax TTS 语音合成、Edge TTS 兜底、字幕轨生成（SRT/VTT/JSON，每段 ≥10 字 + 按自然句断句）、16:9 视频化 HTML 排版（HyperFrames，唯一浅色风格 + 首页加大加粗封面，标准模板 `templates/light-style-wx-agent-ai.html`）、一键渲染 MP4 视频。**核心流程**：口播稿 → GATE1 → TTS+字幕 → 内容映射 → HyperFrames HTML排版 → GATE2 → 渲染 MP4。**一条命令出片**。**硬约束**：GATE1 必过 / GATE2 必过 / 翻页每 10s / 不虚构数字/场景/人物 / 禁用第一人称 / 字幕≥10字 / 按自然句断句。兼容触发词：MiniMax TTS / mmx-tts / MD转MP3 / 反AI味 / 浅色风格 / 封面。"
version: 1.5.4
author: Muru AI
license: MIT
platforms: [linux, macos, windows]
metadata:
  default_voice: moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85
  default_volume: 1.5
  default_speed: 1.0
  default_output_dir: ./output
  edge_tts_fallback: zh-CN-YunjianNeural
---

# 口播视频一键生成技能（multi-agent-tts-html）

> 核心理念：**一条流水线，从口播稿到 MP4 视频，无需手动拼接。**
> 口播稿经过 GATE 审定、TTS 生成、字幕对齐、HyperFrames 排版，到最终 MP4 输出，全流程闭环。

---

## 流水线总览

```
Phase 0.1  写口播稿（script-writer.md）
         ↓
      ⛔ GATE 1（人工审定，必停）
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

**GATE 1 和 GATE 2 是强制阻断点，未通过不能进入下游。**

---

## 📁 文件存放约定（先看这条，再开工）

> **重要**：本技能的所有**用户产物**（口播稿 / 音频 / 字幕 / HTML / MP4）都保存在**执行命令时的当前工作目录**，**不是** skill 安装目录、**也不是** `examples/` 子目录。

### 用户产物 7 类

```
<当前工作目录>/
├── <YYYYMMDD>_<关键词>_v1.md             ← 口播稿（Phase 0.1 输出）
├── <YYYYMMDD>_<关键词>_v1.mp3            ← TTS 音频（Phase 0.2 输出）
├── <YYYYMMDD>_<关键词>_v1.srt            ← SRT 字幕（Phase 0.3 输出）
├── <YYYYMMDD>_<关键词>_v1.vtt            ← WebVTT 字幕
├── <YYYYMMDD>_<关键词>_v1.segments.json  ← JSON 时间戳
├── <YYYYMMDD>_<关键词>_v1_hf.html        ← HyperFrames 配方（Phase 3 输出）
└── <YYYYMMDD>_<关键词>_v1.mp4           ← 最终视频（Phase 4 输出）
```

### 命名规范

| 字段 | 规则 | 示例 |
|------|------|------|
| `YYYYMMDD` | 生成日期（无分隔符）| `20260614` |
| `关键词` | 英文/拼音，≤ 20 字 | `harness-intro` |
| `vN` | 版本号，每次修订 +1 | `v1` / `v2` |

### 检查当前位置（开工前必跑）

```bash
# 确认当前目录
pwd                    # macOS / Linux
cd                    # Windows CMD（显示当前目录）
```

> ⚠️ **常见错误**：在 skill 安装目录（如 `~/.claude/skills/multi-agent-tts-html/`）里跑命令，会把所有产物混进 skill 源码目录，污染 skill 本身。**先 cd 到你想存放视频的目录再开工**。

---

## When to Use

**触发词（满足任一即可）：**
- "口播视频" / "做视频" / "视频化"
- "口播稿" / "写脚本" / "脚本写手"
- "TTS" / "语音合成" / "文字转语音" / "MiniMax TTS"
- "Edge TTS 兜底"
- "字幕轨" / "SRT" / "VTT" / "带字幕"
- "HyperFrames" / "HTML 视频" / "16:9 排版"
- "渲染 MP4" / "render"

**排除词（满足任一不触发整个流水线，引导用户到对应子模块）：**
- "只要字幕" / "只生成 SRT/VTT" → 直接用 `SubsGen.py`，跳过 TTS
- "只要 HTML 排版" / "只要 HyperFrames" → 跳到 Phase 3 入口
- "只要 TTS" / "不要字幕" → 用 `tts-gen.py`，跳过 `--all-subs`
- "只要 MP3" / "只转换文字" → 用 `md2mp3.py`

---

## 🚨 硬约束（6 条，必须死守）

| # | 硬约束 | 触发时机 | 违规动作 |
|---|--------|----------|----------|
| 1 | ⛔ **口播稿必须经 GATE 1 人工审定**（**技术阻断**：脚本会拒绝运行）| Phase 0.1 完成后 | 写完直接调 TTS |
| 2 | ⛔ **HTML 排版必须经 GATE 2 人工审定** | Phase 3 完成后 | 写完直接渲染 |
| 3 | **翻页节奏：每 10 秒一页** | Phase 3 排版时 | 8 分钟做 4 页 ❌ |
| 4 | **不虚构数字/场景/人物** | Phase 2/3 全程 | 排版出现字幕里没有的内容 |
| 5 | ⛔ **禁用第一人称**（"我跟你说"、"我跟你讲"、"我有个朋友"、"反正我..."） | Phase 0.1 写稿 | "我" 出现次数 > 0 |
| 6 | ⛔ **字幕字数 ≥ 10 字**（每段字幕中文字符数，含停顿符号但不含标点空白）| Phase 0.3 字幕生成 | 出现 < 10 字的字幕句（除全文末句） |

---

## 🛑 GATE 1 技术阻断机制（硬约束 #1 的强制执行）

> **从 v1.2.0 起，`tts-with-subs.py` 默认拒绝生成音频**。必须显式传入 `--gate1-approved` 参数，证明你已经审核通过口播稿，否则脚本直接 `exit(1)` 拒绝运行。

### 错误示范（脚本会拒绝）

```bash
# ❌ 不会跑，会报错：
python scripts/tts-with-subs.py 20260614_harness-intro_v1.md --md --output harness-intro --all-subs
# 输出: [GATE1 BLOCKED] 未通过人工审核，禁止调用 TTS API。请先用 SKILL.md「GATE 1」清单自检，
#       然后回 A 通过；或在命令中显式加 --gate1-approved 表示你已审核。
```

### 正确用法（审核通过后才加 flag）

```bash
# ✅ 你已经完成 GATE 1 审核（10 项自检全过 + 人工确认 A 通过）
python scripts/tts-with-subs.py 20260614_harness-intro_v1.md --md --output harness-intro --all-subs --gate1-approved
```

### 跳过审核的代价

| 后果 | 说明 |
|------|------|
| **浪费 MiniMax API 配额** | 一段 30s 音频 = 1 次 TTS 调用，浪费在没审核的稿子上 |
| **AI 味爆表** | 没禁黑话 / 没加停顿 / 没具体场景，播出后听众立刻划走 |
| **虚构数字 / 人名** | 字幕与口播对不上，GATE 2 必然被打回 |
| **返工成本** | Phase 0.2/0.3 重做 ≈ 30s/次，重做成本远超审核成本 |

> 💡 **经验法则**：审核一次 ≈ 1 分钟；返工一次 ≈ 5-10 分钟 + API 配额。**审核永远更便宜**。

---

---

## Phase 0.1 — 写口播稿

### 反 AI 味 10 条铁律

**禁用词**：
| 禁用词 | 替代 |
|--------|------|
| 赋能/抓手/闭环/底层逻辑 | 帮上忙/切入点/完整流程 |
| 痛点/维度/链路/壁垒 | 烦心事/方面/路子/门槛 |
| 在当今...时代/随着...发展 | 直接说事 |
| 让我们共同.../综上所述 | 别说"我们"/收尾要轻 |
| **⛔ 第一人称"我"**（我跟你说/我跟你讲/我有个朋友/反正我.../我直说...）| 说白了/其实/告诉你/想象一下/嗯/知道吧 |

**禁用结构**：
- 三段排比、工整对仗、金句三连
- 总结升华结尾、宏大叙事开场
- 小标题堆叠（连续 10 个 `##`）

**句长控制**：
- 理想 15-25 字，最大 35 字，超过必断句
- 单段不超过 3 句话

**人味注入**（全文 ≥ 5 处）：
- 语气词：嗯/其实/说白了/你知道吧
- 停顿符号：`...`（0.8s）/ `——`（1.0s）
- 自我纠正、半截话、轻微重复（留 30% 不完美）

**数字具体化**：
- ❌ "很多人" → ✅ "见过 30 多家公司里，有 27 家..."
- ❌ "一段时间" → ✅ "连续 3 个月，每天加班到 11 点"

### 10 种钩子模板

| # | 类型 | 例子 |
|---|------|------|
| 1 | 颠覆认知 | "你可能不信，但做了 5 年 XX 的人，90% 都做错了" |
| 2 | 痛点直击 | "说真的，这个事儿快把人气死了" |
| 3 | 反差冲击 | "花了 30 万买的教训，今天免费告诉你" |
| 4 | 悬念 | "你知道为什么 XX 总是失败吗？" |
| 5 | 数字碾压 | "一秒钟，损失 800 块" |
| 6 | 场景代入 | "想象一下，你周一早上刚到工位..." |
| 7 | 故事开场 | "有个朋友，在大厂干了 8 年" |
| 8 | 反问 | "你有没有这种感觉？" |
| 9 | 否定常识 | "直说吧，XX 这事儿其实没必要做" |
| 10 | 冒犯型（慎用） | "说真的，听完这段的人 90% 还在用错误的方法" |

### 口播稿格式

```markdown
---
voice: 国语男声
speed: 1.0
volume: 1.5
insert_pauses: true
pause_ms: 600
---

# 标题（不读出）

正文（会读出）。
可以用 ... 表示停顿。
用 —— 表示强调停顿。
```

### 自检清单（10 项，写完必须全过）

- [ ] 开头 5 秒内有钩子？
- [ ] 无"赋能/抓手/底层逻辑"等黑话？
- [ ] 至少 3 个具体场景/时间/人物？
- [ ] 至少 5 个语气词或停顿？
- [ ] 每段不超过 3 句话？
- [ ] 无"在当今...时代"宏大开场？
- [ ] 结尾无"让我们一起..."升华？
- [ ] 闭眼读一遍像在跟朋友说话？
- [ ] 字数 / 240 = 时长符合预期？
- [ ] 至少 3 处用了 `...` 或 `——` 标记停顿？
- [ ] **⛔ 第一人称"我"出现次数 = 0**（GATE 1 必查）

---

## ⛔ GATE 1 — 口播文案审定（必须停下）

**AI 必做动作**：
1. 跑完 10 项自检（打勾结果）
2. 将口播稿**正文完整粘贴**在审核申请里
3. 写入「用户当前工作目录」`<YYYYMMDD>_<关键词>_v1.md`
4. 提交审核申请，明确等待指令

**审核申请模板**：
```markdown
## ⛔ GATE 1 审核申请

**项目**：<name>
**文件**：<当前目录>/<YYYYMMDD>_<关键词>_v1.md
**字数**：XXX（目标 800-1200）
**时长预估**：X.X 分钟

### 10 项自检
- [ ] 1. 开头有钩子
- [ ] 2. 无禁用词
- [ ] 3. 场景/人物 ≥ 3
- [ ] 4. 语气词/停顿 ≥ 5
- [ ] 5. 每段 ≤ 3 句
- [ ] 6. 无宏大开场
- [ ] 7. 无升华结尾
- [ ] 8. 像在说话
- [ ] 9. 字数/时长合适
- [ ] 10. 停顿符号 ≥ 3

### 口播稿正文
> ...完整正文...

### 🎯 请回复
- A 通过 → 进 Phase 0.2 TTS
- B 改 X 处 → 指出具体行
- C 重写 → 回到 Phase 0.1
```

---

## Phase 0.2 — TTS 生成 MP3

**工具**：`scripts/tts-with-subs.py`（一键 TTS + 字幕）

```bash
python scripts/tts-with-subs.py <口播稿.md> --md --output <项目名> --all-subs
```

**引擎优先级**：
1. MiniMax TTS（`speech-02-hd`，需 `MINIMAX_API_KEY` 环境变量）
2. Edge TTS 兜底（`pip install edge-tts`，无需 API Key）

**TTS 引擎自动降级**：
- 有 `MINIMAX_API_KEY` → MiniMax
- MiniMax 失败（rate limit / 网络错误）→ 自动切 Edge TTS
- 无 API Key → 直接 Edge TTS

**默认配置**：
- 音色：`moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85`（国语男声）
- 音量：1.5 | 语速：1.0 | 停顿：600ms

---

## Phase 0.3 — 字幕生成

**工具**：`scripts/tts-with-subs.py`（一次性生成 SRT + VTT + JSON）

```bash
python scripts/tts-with-subs.py <口播稿.md> --md --output <项目名> --all-subs
# 输出：
#   <项目名>.mp3        ← 音频
#   <项目名>.srt        ← SRT 字幕
#   <项目名>.vtt        ← WebVTT 字幕
#   <项目名>.segments.json ← JSON 时间戳
```

### 📏 字幕字数硬约束（v1.5.2）

> **每段字幕中文字符数 ≥ 10 字**（不含标点和空白）。
> 这是从 2026-06-19 微信 Agent 案例复盘中总结的硬约束——上次默认 6 字导致 27/39 句字幕碎到 <10 字（69% 字幕太短），观众眼睛跟不上画面切换。

| 参数 | 值 | 来源 |
|------|-----|------|
| **`min_chars`**（最短）| **10 字** | 硬约束，避免碎句 |
| `ideal_chars`（理想）| 18 字 | 默认值 |
| `max_chars`（最长）| 22 字 | 默认值（避免一行字太满） |
| `max_chars` 软上限 | 26 字 | split_to_caption_sentences 兜底 |

**为什么是 10 字**：
- < 6 字：单字/双字句太碎，观众还没看清就切了
- 6-9 字：还行但偏短，本案例 27 句属此类
- **10-22 字**：黄金区间，**4.0 字/秒朗读节奏下停留 2.5-5.5s**，正好读一遍
- > 26 字：单句超过 6.5s，画面静止太久无变化

### 字幕切句规则（SubsGen.py v1.5.3）

> **🎯 第一原则：按自然句断句**。
> 自然句 = 以 `。！？` 结尾的完整语句，是字幕的**最优边界**。
> 次级标点（`,;:、——`）只在自然句**过长**时作为内部拆分点使用，**绝不跨自然句硬切**。

#### 5 步切句规则（优先级递减）

| 步 | 动作 | 触发条件 | 边界 |
|----|------|----------|------|
| **1** | **自然句切分** | 全文 | 按 `。！？` 切成 N 个自然句 |
| **2** | **短句合并** | 自然句 < 10 字 | 与相邻自然句合并（**不破坏自然句完整性**） |
| **3** | **合并仍 < 10 字** | Step 2 合并后仍不足 | 继续向后合并下一个自然句（**自然句完整优先于字数硬约束**） |
| **4** | **超长自然句内部拆分** | 单个自然句 > 22 字 | 在**自然句内部**按次级标点 `,;:、——` 拆 |
| **5** | **兜底硬拆** | 单自然句 > 26 字且无次级标点 | 在最近可切点拆（保证两段都 ≥ 5 字） |

#### 边界优先级

```
自然句边界（。！？）  >>>  次级边界（,;:、——）  >>>  兜底硬拆
   不可破坏                  不可破坏              极少见
```

#### 停顿加成

| 标点 | 时长加成 |
|------|----------|
| `...` | +0.5s |
| `——` | +0.3s |
| `,;:` | +0.15s |

#### 硬规则

- ❌ **绝不允许 < 10 字**（Step 3 兜底合并到 ≥ 10 字；末句允许 ≥ 5 字）
- ❌ **绝不允许硬切单词**（不让一个汉字单独成句）
- ❌ **绝不允许跨自然句切句**（自然句边界神圣不可破）
- ✅ 提供音频路径时用 ffprobe 归一化到真实时长

#### 时间精度

- `base_speed = 4.0 字/秒`（240 字/分，与 SKILL 一致）
- ffprobe 归一化后精度 ±0.3-1s

#### 验证脚本（GATE 1 通过前必跑）

```python
import json, re
data = json.load(open('<项目名>.segments.json'))
violations = [t for t in data['timestamps']
              if len(re.findall(r'[一-鿿]', t['text'])) < 10]
print(f'cues < 10 chars: {len(violations)} / {len(data["timestamps"])}')
# 期望输出：cues < 10 chars: 0 / 39
```

---

## Phase 1 — 收集 3 个源

| 来源 | 文件 |
|------|------|
| 字幕源 | `<项目名>.vtt` / `.srt` |
| 口播稿 | `<项目名>.md` |
| 时间戳 | `<项目名>.segments.json` |

---

## Phase 2 — 内容映射表（防虚构关键）

**核心原则**：屏幕上显示的每一条文字，都必须在字幕里有对应内容。

| 画面元素 | 字幕对应 | 时段 | 状态 |
|---------|---------|------|------|
| 标题"..." | "..."（XX:XX 处字幕原话） | 0-10s | ✅ 对齐 |
| 数字 "200 万" | ❌ 字幕无此数字 | 15-25s | ⛔ 删除/改写 |

**状态说明**：
- ✅ 对齐：字幕原文有，页面有，完全对应
- ⛔ 删除/改写：页面有，字幕无 → **必须删除该元素，或改写页面元素对齐字幕原文（不是改字幕）**

**7 条戒律（每条都要过）**：

| # | 戒律 | 反例 |
|---|------|------|
| 1 | 不虚构人名 | 口播"一个朋友" → 排版写"王磊 CTO" |
| 2 | 不虚构数字 | 口播无具体数字 → 排版写"200 万" |
| 3 | 不虚构场景 | 口播"5 种角色" → 排版写"北京海淀" |
| 4 | 不虚构比喻 | 口播"串台" → 排版写"10 个一模一样的抽屉" |
| 5 | 不虚构代码 | 口播"CLAUDE.md" → 排版写 12 行业务代码 |
| 6 | 不虚构流程 | 口播无流程 → 排版写 D1-D7 七步 |
| 7 | 不虚构采访 | 口播无采访 → 排版写"李婷/高远/周明" |

---

## Phase 3 — HyperFrames HTML 排版

### HyperFrames 格式规范（必须遵守）

**根容器属性**：
```html
<div class="hf-root"
     data-composition-id="项目名"
     data-width="1920"
     data-height="1080"
     data-start="0">
```

**每个 timed 元素**（页面/字幕/媒体）：
```html
<section class="slide clip"
         data-start="0"
         data-duration="11"
         data-track-index="0">
```

| 属性 | 说明 | 示例 |
|------|------|------|
| `class="clip"` | HyperFrames 管理 visibility | **必须** |
| `data-start` | 开始时间（秒） | `"0"` `"11"` |
| `data-duration` | 持续时长（秒） | `"11"` |
| `data-track-index` | 轨道编号 | `"0"` |

**媒体元素**：
```html
<audio src="audio.mp3"
       data-start="0"
       data-duration="44.388">
```

### 字幕 bar（推荐方案：timed div）

每个字幕 cue 是独立 div，靠 `data-start`/`data-duration` 自动显示/隐藏：

```html
<div id="sub-bar">
  <div class="sub-cue clip"
       data-start="0"
       data-duration="1.757"
       data-track-index="1">有没有这种感觉？</div>
  <div class="sub-cue clip"
       data-start="1.757"
       data-duration="4.462"
       data-track-index="1">学了一堆 AI 工具...</div>
  <!-- 共 N 句，每句独立 div -->
</div>
```

```css
/* ✅ v1.4.0 标准化字幕样式 — 见下方「🎬 字幕样式规范」 */
#sub-bar {
  position: absolute; bottom: 118px; left: 0; right: 0;
  display: flex; flex-direction: column; align-items: center;
  pointer-events: none; z-index: 50;
}
.sub-cue {
  position: absolute; top: 0; left: 0; right: 0;
  background: none;                         /* ⚠️ 不要黑色背景容器 */
  color: #fff;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 42px; font-weight: 700;
  padding: 21px 60px; text-align: center;
  width: 100%; white-space: nowrap;
  letter-spacing: 1.5px;
  /* 三层 text-shadow 替代背景容器，确保亮/暗背景都可读 */
  text-shadow:
    0 0 8px  rgba(0,0,0,1),
    0 2px 16px rgba(0,0,0,0.9),
    0 4px 28px rgba(0,0,0,0.7);
}
```

---

## 🎬 字幕样式规范（v1.4.0 标准化）

> **所有 harness-intro 系列视频必须使用此规范**。已通过多次实际渲染验证：42px 是 1920×1080 视频的最佳可读尺寸，三层 text-shadow 替代传统黑色背景容器，整体观感更轻盈现代。

### 强制规范

| 属性 | 值 | 原因 |
|------|-----|------|
| **`font-size`** | **`42px`** | 1920×1080 视频下既清晰又不抢主体 |
| **`font-weight`** | **`700`** | 加粗确保外发光阴影下边缘锐利 |
| **`padding`** | **`21px 60px`** | 上下 padding 等于字高一半，形成呼吸感 |
| **`letter-spacing`** | **`1.5px`** | 略宽于默认，提升可读性 |
| **`bottom`** | **`118px`** | 距底边约 2.8 倍字高，离主体元素有视觉留白 |
| **`background`** | **`none`** | 禁用黑色/渐变背景容器 |
| **`text-shadow`** | **3 层堆叠**（8px 实心 + 16px 中距 + 28px 长距）| 替代背景，确保任何页面背景上都清晰 |

### ❌ 反例（不允许出现）

```css
/* ❌ 太小抢不到主体 */
.sub-cue { font-size: 28px; }

/* ❌ 太大盖住内容 */
.sub-cue { font-size: 56px; }

/* ❌ 黑色背景容器破坏现代感 */
.sub-cue { background: rgba(0,0,0,.82); }

/* ❌ 单层阴影不够强，亮背景下糊成一团 */
.sub-cue { text-shadow: 0 2px 4px rgba(0,0,0,0.5); }

/* ❌ 离底边太近，和页面底部元素挤在一起 */
#sub-bar { bottom: 30px; }
```

### ✅ 推荐完整模板（直接复制）

```html
<div id="sub-bar">
  <div class="sub-cue clip" data-start="0"     data-duration="2.69" data-track-index="1">字幕文本 1</div>
  <div class="sub-cue clip" data-start="2.741" data-duration="2.49" data-track-index="1">字幕文本 2</div>
  <!-- 时长建议比精确值少 0.05s（留 50ms gap 防浮点重叠）-->
</div>
```

```css
#sub-bar {
  position: absolute; bottom: 118px; left: 0; right: 0;
  display: flex; flex-direction: column; align-items: center;
  pointer-events: none; z-index: 50;
}
.sub-cue {
  position: absolute; top: 0; left: 0; right: 0;
  background: none;
  color: #fff;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 42px; font-weight: 700;
  padding: 21px 60px; text-align: center;
  width: 100%; white-space: nowrap;
  letter-spacing: 1.5px;
  text-shadow:
    0 0 8px  rgba(0,0,0,1),
    0 2px 16px rgba(0,0,0,0.9),
    0 4px 28px rgba(0,0,0,0.7);
}
```

### 🔧 微调指引

| 反馈 | 调整 |
|------|------|
| 字幕太小 | `font-size: 42px → 48px`，同步 `padding: 21px → 24px` |
| 字幕太大 | `font-size: 42px → 36px`，同步 `padding: 21px → 18px` |
| 字幕太靠下 | `bottom: 118px → 140px`（每次 +22px ≈ 半字高） |
| 字幕太靠上 | `bottom: 118px → 96px`（每次 -22px） |
| 暗背景下模糊 | 加第 4 层 `text-shadow: 0 0 4px rgba(0,0,0,1)` |
| 亮背景下糊 | `text-shadow` 颜色改为 `rgba(0,0,0,0.95)` 加深 |

---

## 🎨 视觉风格规范（v1.5.0 标准化）

> **唯一风格**：浅色风格（米白 + 微信绿点缀），沉淀自 `templates/light-style-wx-agent-ai.html`。
> 适用于商业/科技/财经/微信生态等口播视频。**不再支持深色风格**（v1.4.0 前的暗色模板已废弃）。

### 1. 浅色风格色板（强制标准）

| 角色 | 颜色 | 用途 |
|------|------|------|
| **底色（主）** | `#FAFAF7` 米白 | 默认页面背景，温柔不刺眼 |
| **底色（封面/重点页）** | `linear-gradient(135deg, #FFFFFF 0%, #F0F4F1 100%)` | 封面、结论页增加呼吸感 |
| **底色（纯白）** | `#FFFFFF` | 收尾页、卡片背景 |
| **品牌主色** | `#07C160` 微信绿 | 强调字、装饰线、icon、按钮描边 |
| **文字主色** | `#1A1A1A` 深灰黑 | 标题、主文案（**不用纯黑 #000，更柔和**） |
| **文字次色** | `#333` / `#555` / `#666` / `#888` | 副标、注释、辅助文字（按权重递减） |
| **文字点缀** | `#999` | 弱化标签、角标、页码 |
| **分割线/装饰** | `#07C160` 或 `#E8F8EF` 极浅绿 | 短粗分割线、阴影块 |

**强制规则**：
- ❌ **禁用**纯黑 `#000` 背景
- ❌ **禁用**深色卡片（卡片永远是白底 + 浅阴影）
- ✅ 主标题可用 `text-shadow: 0 4px 24px rgba(7,193,96,0.08)` 加品牌色微光

### 2. 字体与字重

```css
/* 渲染时统一用 sans-serif（hyperframes 不识别 PingFang SC） */
font-family: sans-serif;
```

**字重阶梯**：
- 标题：`font-weight: 900` (黑体) 或 `800`
- 副标：`font-weight: 700`
- 正文：`font-weight: 500`
- 辅助：`font-weight: 400`

### 3. 首页封面规范（v1.5.0 强制标准）

> **首页必须加大加粗，兼顾杂志封面观感**。所有口播视频首页都应遵循此规范。

#### 强制参数

| 元素 | 字号 | 字重 | 颜色 | 位置 |
|------|------|------|------|------|
| **主标题** | `148px` | `900` | `#111` | 居中，最大宽 1700px |
| **品牌副标** | `36px` | `600` | `#07C160` | 标题上方，letter-spacing 8px |
| **副标解释** | `46px` | `500` | `#555` | 标题下方，letter-spacing 4px |
| **角标** | `28px` | `700` | `#888` | 左上角，14px 绿点 + 大写英文 |
| **页码** | `24px` | `600` | `#999` | 右下角，"01 / 08" 格式 |

#### 视觉细节 CSS

```css
/* 渐变背景（封面/结论页）*/
background: linear-gradient(135deg, #FFFFFF 0%, #F0F4F1 100%);

/* 标题微光 */
text-shadow: 0 4px 24px rgba(7,193,96,0.08);

/* 强调词用 brand color */
.title .accent { color: #07C160; }

/* 角标前缀小绿点 */
.corner-mark::before {
  content: ""; display: inline-block;
  width: 14px; height: 14px; background: #07C160;
  border-radius: 50%; margin-right: 14px;
  vertical-align: middle;
}
```

### 4. 标准化 8 页版式（与模板文件 1:1 对应）

> **以下 8 页版式必须严格按 `templates/light-style-wx-agent-ai.html` 实现**。修改版式时同步修改模板文件。

| 页 | 时段 | 版式 | 关键元素（CSS 类名） |
|---|------|------|---------------------|
| 1 | 0-10s | **cover-magazine** | `.corner-mark` + `.kicker` + `.title` (`.accent`) + `.subtitle` + `.corner-num`，渐变背景 |
| 2 | 10-21s | **big-stats** | `.label` + `.bignum` (280px) + `.bignum-sub` + `.arrow` 箭头胶囊 |
| 3 | 21-32s | **pull-quote** | `.quote-mark` (240px 引号) + `.quote` (84px) + `.divider` (6px) + `.cite` |
| 4 | 32-43s | **chat-mockup** | `.label` + `.phone` 框（白底+浅阴影） + `.phone-header` + `.msg.user` (绿) / `.msg.ai` (灰) + `.phone-foot` + `.caption` |
| 5 | 43-52s | **number-list** | `.label` + `.big-num` (360px 编号) + `.heading` (72px) + `.desc` |
| 6 | 52-64s | **three-pillars** | `.label` + `.tri` 容器 + `.card`（白底+8px 顶部绿条+浅阴影）+ `.num` + `.card h3` + `.card p` + `.foot` |
| 7 | 64-74s | **pull-quote** | `.kicker` + `.rule` (8px 绿条) + `.main` (120px 900) + `.sub`，渐变背景 |
| 8 | 74-77s | **outro** | `.dot` (36px 绿点) + `.out` (96px 900) + `.sign` 尾签 |

### 5. 完整 HTML 模板（lint 全过版）

> **🔗 唯一模板文件**：`templates/light-style-wx-agent-ai.html`
>
> **使用方式**：
> 1. 复制 `templates/light-style-wx-agent-ai.html` 到用户工作目录
> 2. 文件名改为 `<YYYYMMDD>_<关键词>_v1_hf.html`
> 3. 全局替换 `wx-agent-ai` → 你的 composition-id
> 4. 替换 `wx-agent-ai.mp3` → 你的音频文件名
> 5. 替换 `data-composition-id="wx-agent-ai"` → 你的 ID
> 6. 替换 8 页内容文字（保留 class 名不变）
> 7. 替换 39 句字幕文字（保留 class/data-start/data-duration 模式）

模板已通过 `hyperframes lint` 0 errors 验证，包含：
- ✅ audio `id="voiceover"`
- ✅ 所有 page slide duration 减 0.05s 防浮点重叠
- ✅ 所有 sub-cue duration 减 0.005s
- ✅ `window.__timelines` gsap 注册
- ✅ `font-family: sans-serif` 兜底
- ✅ `.slide.clip` 默认隐藏 / `.active` 显式激活

### 6. lint 预检（强制）

```bash
hyperframes lint <project>
# 期望：0 errors（49 warnings 是 studio_missing_editable_id，非阻塞）
```

| 错误 | 原因 | 修复 |
|------|------|------|
| `missing_timeline_registry` | 未注册 `window.__timelines` | 模板已带，复制即可 |
| `media_missing_id` | audio 无 id | 模板已带 `id="voiceover"` |
| `overlapping_clips_same_track` | clip 间浮点重叠 | 模板已减 0.05s gap |
| `font_family_without_font_face` | 用 PingFang SC | 模板用 `sans-serif` 兜底 |

---

### 翻页节奏（硬约束 3）

```
页数 = round(音频总时长 / 10)
每页 10s ± 2s（8s~12s 合规）
超过 12s → 拆分
低于 8s → 合并
第 1 页封面：允许 3-8s
最后一页结尾：允许 3-8s
```

> **8 页版式参考**：见上方「🎨 视觉风格规范 → 4. 标准化 8 页版式」章节，与 `templates/light-style-wx-agent-ai.html` 1:1 对应。

---

## ⛔ GATE 2 — HTML 排版审定（必须停下）

**审核申请模板**：
```markdown
## ⛔ GATE 2 审核申请

**项目**：<name> 16:9 HyperFrames 排版
**文件**：<当前目录>/<YYYYMMDD>_<关键词>_v1_hf.html
**总页数**：X 页 | **总时长**：XX:XX | **平均页**：X.X 秒

### 5 项自检
- [ ] 1. 7 条戒律核查（grep 无虚构）
- [ ] 2. 内容映射表 100% 覆盖
- [ ] 3. 字幕同步（timed div，每句有 data-start/duration）
- [ ] 4. 翻页节奏（每页 10s ± 2s）
- [ ] 5. 文件命名规范（YYYYMMDD_关键词_vN）

### 🎯 请回复
- A 通过 → 进 Phase 4 渲染
- B 改 X 处 → 指出具体页/行
- C 重做
```

---

## Phase 4 — HyperFrames 渲染 MP4

### 前置条件

```bash
# 1. 安装 hyperframes（Node.js 全局包）
npm install -g hyperframes

# 2. 检查环境
hyperframes doctor
```

### 项目初始化

```bash
# 创建空白 HyperFrames 项目
hyperframes init /tmp/<项目名> --example blank

# 复制配方和素材
cp <项目名>_hf.html /tmp/<项目名>/index.html
cp <项目名>.mp3          /tmp/<项目名>/
cp <项目名>.vtt          /tmp/<项目名>/
```

### 渲染命令

```bash
cd <hyperframes-cli-path>
node node_modules/hyperframes/dist/cli.js render \
  /tmp/<项目名> \
  -o "<输出目录>/<YYYYMMDD>_<关键词>_v1.mp4" \
  --fps 30 \
  --quality high \
  --resolution 1080p
```

### 渲染参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--fps` | 30 | 帧率，可选 24/30/60 |
| `--quality` | standard | 可选 draft/standard/high |
| `--resolution` | 1080p | 可选 1080p/4k/portrait/square |
| `--crf` | — | 质量参数，值越小质量越高 |
| `--workers` | auto | 并行渲染进程数 |

### Lint 检查（渲染前推荐）

```bash
hyperframes lint /tmp/<项目名>
```
- `✗` = 错误（必须修复）
- `⚠` = 警告（可忽略，渲染仍会继续）

---

## 文件命名规范

> 📁 **存放位置**：详见顶部「📁 文件存放约定」章节。简言之：**用户产物存放在执行命令时的当前工作目录**，不是 skill 目录。

```
<YYYYMMDD>_<内容关键词>_v<版本>.md       ← 口播稿
<YYYYMMDD>_<内容关键词>_v<版本>.mp3      ← TTS 音频
<YYYYMMDD>_<内容关键词>_v<版本>.vtt      ← WebVTT 字幕
<YYYYMMDD>_<内容关键词>_v<版本>.srt      ← SRT 字幕
<YYYYMMDD>_<内容关键词>_v<版本>.segments.json ← JSON 时间戳
<YYYYMMDD>_<内容关键词>_v<版本>_hf.html  ← HyperFrames 配方
<YYYYMMDD>_<内容关键词>_v<版本>.mp4       ← 最终视频
```

```
<YYYYMMDD>_<内容关键词>_v<版本>.md       ← 口播稿
<YYYYMMDD>_<内容关键词>_v<版本>.mp3      ← TTS 音频
<YYYYMMDD>_<内容关键词>_v<版本>.vtt      ← WebVTT 字幕
<YYYYMMDD>_<内容关键词>_v<版本>.srt      ← SRT 字幕
<YYYYMMDD>_<内容关键词>_v<版本>.segments.json ← JSON 时间戳
<YYYYMMDD>_<内容关键词>_v<版本>_hf.html  ← HyperFrames 配方
<YYYYMMDD>_<内容关键词>_v<版本>.mp4       ← 最终视频
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `YYYYMMDD` | 生成日期 | `20260614` |
| `内容关键词` | 英文或拼音 ≤20字 | `skills-intro` |
| `vN` | 版本，每次修订 +1 | `v1` / `v2` |

---

## 目录结构

> ⚠️ **注意区分**：下面是 **skill 自身**的目录结构（源码），**不是用户产物的存放位置**。用户产物存放在「📁 文件存放约定」里指定的当前工作目录。

```
multi-agent-tts-html/
├── SKILL.md                      ← 主入口（本文）
├── README.md                     ← 快速开始指南
├── LICENSE                       ← MIT 许可证
├── requirements.txt              ← Python 依赖锁定
├── grading.json                  ← 多维审核评分报告
├── .env.example                  ← 环境变量模板
├── references/
│   ├── script-writer.md         ← 口播脚本写手指南（反 AI 味）
│   ├── content-mapping-template.md ← 内容映射表模板（防虚构）
│   ├── failure_case_log.md      ← 错误案例日志（自我迭代）
│   ├── self-review-template.md  ← 自我复盘模板
│   └── test_pool.md             ← 测试用例池（回归测试）
└── scripts/
    ├── md2mp3.py                ← MD → MP3 一键转换
    ├── tts-gen.py               ← 通用 TTS 生成器（自动 Edge TTS 兜底）
    ├── tts-with-subs.py         ← TTS + 字幕一键生成（SRT/VTT/JSON）
    └── SubsGen.py                ← 字幕生成模块（切句/时间戳/格式）
```

---

## 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 字幕只有第一句 | JS 轮询 audio.currentTime 在 HyperFrames 截图模式失效 | 用 timed div 方案（每句独立 div + class="clip"） |
| 页面全部重叠 | `position: absolute` + `opacity` 切换没配 `visibility` | 加 `visibility: hidden` 到非当前页 |
| TTS rate limit | MiniMax RPM 配额用尽 | 自动降级 Edge TTS |
| HyperFrames 渲染失败 | 缺少 `data-composition-id` 或 `class="clip"` | lint 检查修复 |
| 字幕换行 | `white-space: nowrap` 缺失 | CSS 加 `white-space: nowrap` |
| 音频与字幕不同步 | ffprobe 未归一化 | 提供 `audio_path` 参数触发 ffprobe 归一化 |

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| **1.2.1** | 2026-06-14 | **F-002 复现修复**：删除 F-008 加的 `.clip[data-start="0"]` 兜底规则（与 `.clip.active` 同特异性导致 page-1 永远不隐藏），依赖 JS 在 DOMContentLoaded 立即 `applyState()` 给第一页加 `.active`；给 `.hf-root` 加 `overflow: hidden` 防装饰元素溢出 |
| **1.5.4** | 2026-06-19 | **🔧 SubsGen.py 关键修复（体检发现）**：①加 helper `_cn_count(s) = len(re.findall(r'[一-鿿]', s))` 统一中文字数②Step 2/3/4/5 全部 `len()` 阈值判断改用 `_cn_count()`③加 Step 3.5 短段回合并（循环到全合规）④加 Step 6 末段吸附⑤回归测试：wx-agent-ai 案例 27/39 违规（69%）→ 0/21 合规（100%） |
| **1.5.3** | 2026-06-19 | **🎯 字幕按自然句断句（第一原则）**：5 步切句规则改写为「按自然句优先」原则：①自然句边界（。！？）神圣不可破 ②次级标点（,;:、——）只在单自然句 > 22 字时作为内部拆分点 ③明确「自然句完整优先于字数硬约束」——短自然句可继续向后合并 ④新增「边界优先级」表（自然句 >>> 次级 >>> 兜底）⑤新增硬规则「绝不允许跨自然句切句」 |
| **1.3.0** | 2026-06-14 | **GATE 1 强制阻断机制上线**：`tts-with-subs.py` 和 `md2mp3.py` 必须显式传 `--gate1-approved` 才能调 TTS，否则 exit(1)。把硬约束 #1 从文档约束升级为技术约束 |
| **1.5.2** | 2026-06-19 | **📏 字幕字数硬约束 ≥10 字**：①新增硬约束 #6「每段字幕中文字符数 ≥ 10 字」②Phase 0.3 新增「📏 字幕字数硬约束」章节，含 min_chars=10/ideal=18/max=22 参数表 + 「为什么是 10 字」原理 + 5 步切句规则 + 验证脚本③`SubsGen.py` `generate_subtitles_for_text` 默认 min_chars 6→10、max_chars 18→22；CLI `--min-chars` 默认 6→10 |
| **1.5.1** | 2026-06-19 | **🎨 单一浅色风格 + 标准模板**：`templates/light-style-wx-agent-ai.html` 沉淀为唯一标准模板（lint 0 errors 全过版）。①删除「4 页版式参考（harness-intro 案例）」旧模板（cover-magazine/three-pillars/terminal/manuscript）②删除「浅色 vs 深色风格对比表」③删除「完整 HTML 头部」内嵌模板，改为指向 `templates/light-style-wx-agent-ai.html` 文件④删除 `examples/harness-intro/` 深色风格示例目录⑤8 页版式表改为标准化（与模板文件 1:1 对应，含 CSS 类名）⑥字体规范简化为统一 `sans-serif` 兜底 |
| **1.5.0** | 2026-06-19 | **🎨 视觉风格规范 + 首页封面 + 禁用第一人称**：①新增「🎨 视觉风格规范」章节，固化浅色风格色板（米白 #FAFAF7 / 微信绿 #07C160 / 字体 sans-serif）、首页封面模板（148px 900 字重 + kicker 角标 + 页码 + 渐变背景）、8 页版式参考、浅色 vs 深色风格对照、完整 HTML 模板（lint 全过版）②硬约束新增 #5「禁用第一人称」③反 AI 味禁用词表加第一人称条④10 项自检加第一人称核查项⑤10 种钩子模板示例去"我"⑥description 加浅色风格 / 封面 / 禁用第一人称触发词 |
| **1.4.0** | 2026-06-14 | **🎬 字幕样式规范固化**：Phase 3 新增「字幕样式规范」章节，强制 42px / 21px 60px padding / 三层 text-shadow / bottom 118px / 禁用背景容器。所有 harness-intro 系列视频必须使用此规范 |
| **1.1.2** | 2026-06-14 | **HTML 黑屏 bug 修复**：①CSS 默认显示第一页（`data-start="0"`）②JS 改为 DOMContentLoaded 立即启动循环（不依赖 audio.play）③加播放按钮兜底（防浏览器 autoplay 拦截）|
| **1.1.1** | 2026-06-14 | **文档可发现性修复**：①SKILL.md 顶部新增「📁 文件存放约定」章节，明确用户产物存放在「当前工作目录」而非 skill 目录或 examples/ 子目录②目录结构章节加 ⚠️ 提示区分 skill 源码 vs 用户产物 |
| **1.1.0** | 2026-06-14 | **审核驱动优化**：①新增排除词（只要字幕/只要 TTS/只要 HTML）②SubsGen.py 修复全角空格被吞掉的 bug③新增 `failure_case_log.md`/`self-review-template.md`/`test_pool.md` 三大自我迭代文件④新增 `requirements.txt` 锁定依赖⑤生成 `grading.json` 审核评分 |
| **1.0.0** | 2026-06-14 | 初始版本：整合 multi-agent-mmx-tts + HyperFrames 渲染，一条流水线从口播稿到 MP4 |
