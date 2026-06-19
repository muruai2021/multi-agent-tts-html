# Failure Case Log — multi-agent-tts-html

> **目的**：记录技能运行过程中的所有失败案例，形成"错误 → 复盘 → 修复 → 回归测试"闭环。
>
> **维护规则**：
> - 每次运行出现错误（含已被 try/except 吞掉的），立即追加一条
> - 修复后将条目从 🔴区移到 ✅区，并在 `test_pool.md` 增加对应 RE-XXX 测试
> - 修复中放 🟡区，标明修复 PR/版本

---

## 🔴 未修复（已知问题）

| ID | 日期 | Phase | 触发词 | 错误现象 | 根因分析 | 优先级 |
|----|------|-------|--------|----------|----------|--------|
| — | — | — | — | （暂无） | — | — |

---

## 🟡 修复中

| ID | 日期 | Phase | 问题 | 修复方案 | 负责人 | 目标版本 |
|----|------|-------|------|----------|--------|----------|
| — | — | — | — | — | — | — |

---

## ✅ 已修复（种子数据，来自 SKILL.md 常见问题排查）

| ID | 日期 | Phase | 错误现象 | 根因 | 修复方案 | 修复版本 |
|----|------|-------|----------|------|----------|----------|
| F-001 | 2026-06-14 | Phase 4 | 字幕只有第一句 | JS 轮询 `audio.currentTime` 在 HyperFrames 截图模式失效 | 改用 timed div 方案（每句独立 div + `class="clip"`）| v1.0.0 |
| F-002 | 2026-06-14 | Phase 4 | 页面全部重叠 | `position: absolute` + `opacity` 切换没配 `visibility` | 加 `visibility: hidden` 到非当前页 | v1.0.0 |
| F-003 | 2026-06-14 | Phase 0.2 | TTS rate limit | MiniMax RPM 配额用尽 | 自动降级 Edge TTS（`tts-gen.py:141-149`）| v1.0.0 |
| F-004 | 2026-06-14 | Phase 4 | HyperFrames 渲染失败 | 缺少 `data-composition-id` 或 `class="clip"` | `hyperframes lint` 预检查 | v1.0.0 |
| F-005 | 2026-06-14 | Phase 0.3 | 字幕换行 | `white-space: nowrap` 缺失 | CSS 加 `white-space: nowrap` | v1.0.0 |
| F-006 | 2026-06-14 | Phase 0.3 | 音频与字幕不同步 | ffprobe 未归一化 | 提供 `audio_path` 参数触发 ffprobe 归一化 | v1.0.0 |
| F-007 | 2026-06-14 | Doc | AI 把用户产物存到 `examples/harness-intro/` 子目录 | SKILL.md「目录结构」章节是 skill 源码结构，但没醒目区分用户产物存放在「当前工作目录」（约定埋在 GATE 1/2 模板里）| SKILL.md 顶部新增「📁 文件存放约定」章节 + 目录结构章节加 ⚠️ 提示 | v1.1.1 |
| F-008 | 2026-06-14 | Phase 3 | 浏览器打开 HTML 全黑屏 | JS visibility 切换只在 `audio.play` 事件触发后启动，未播放时所有 `.clip` 元素 `visibility: hidden`；同时未考虑浏览器 autoplay 拦截 | ①CSS 加 `.clip[data-start="0"] { visibility: visible; }` 默认显示第一页 ②JS 改为 DOMContentLoaded 立即启动循环（不依赖 play） ③加播放按钮兜底 | v1.1.2 |
| F-009 | 2026-06-14 | Phase 3 | **F-002 复现**：4 页同时可见，重叠 | **回归 bug**：F-008 修复时加的兜底 `.clip[data-start="0"] { visibility: visible; }` 与 `.clip.active` 同 CSS 特异性（都是 0,0,2,0），但 `[data-start="0"]` 后定义胜出，导致 page-1 失去 `.active` 类后仍 visible，与 page-2/3/4 重叠 | ①删除 `[data-start="0"]` 兜底规则 ②依赖 JS 在 DOMContentLoaded 立即 applyState() 给 page-1 加 `.active`（这步已经做了）③给 `.hf-root` 加 `overflow: hidden` 防止装饰元素溢出 | v1.2.1 |
| F-010 | 2026-06-14 | Phase 0.1→0.2 | 用户希望强化硬约束 #1「口播稿必须经 GATE 1 人工审定」——当前只是文档约束，写完口播稿可直接调 TTS，浪费 API 配额 + 返工成本高 | 把硬约束 #1 从文档约束升级为技术约束：`tts-with-subs.py` 和 `md2mp3.py` 必须显式传 `--gate1-approved` 才能调 TTS，否则 `exit(1)`。脚本顶部打印醒目的 `GATE1 BLOCKED` 提示 | v1.3.0 |
| F-011 | 2026-06-14 | Phase 3 | 字幕样式每次都要重新调试（font-size / padding / background / 阴影），浪费迭代时间 | 经过 harness-intro v1 三轮调整确定最优值：42px / 21px 60px / 3 层 text-shadow / bottom 118px / 禁用背景容器。固化到 SKILL.md「🎬 字幕样式规范」章节作为强制标准 | v1.4.0 |
| F-012 | 2026-06-19 | Phase 0.1 | AI 写口播稿模板化带第一人称"我跟你说/我跟你讲/我有个朋友/反正我..."，虽然反 AI 味禁词表里没有，但用户明确要求"不要用第一人称" | ①硬约束表新增 #5「禁用第一人称」②反 AI 味禁用词表加第一人称条③10 项自检加"我 出现次数 = 0"核查④10 种钩子模板示例中 4 处去"我"（#2 #7 #9 #10）⑤GATE 1 审核申请里加第一人称 count | v1.5.0 |
| F-013 | 2026-06-19 | Phase 3 | `hyperframes lint` 报 16 个 `overlapping_clips_same_track` 错误：紧贴的 `data-start="X"` 与上一页 `data-start+duration=X` 浮点相等导致 0.001s 重叠 | 每页 duration = 下一 start - 当前 start - 0.05s（留 50ms gap），最后一页 = 总时长 - 当前 start - 0.05s。SKILL.md 字幕规范原本已写"duration 减 0.05s"，但只针对 sub-cue 没针对 page slide → 同步到 page 排版 | v1.5.0 |
| F-014 | 2026-06-19 | Phase 3 | `hyperframes lint` 报 `missing_timeline_registry: Missing window.__timelines registration` | 必须注册 `window.__timelines = window.__timelines || {}; const tl = gsap.timeline({ paused: true }); window.__timelines["composition-id"] = tl;` 且需 import `https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`。固化到 v1.5.0 完整 HTML 模板 | v1.5.0 |
| F-015 | 2026-06-19 | Phase 3 | `hyperframes lint` 报 `font_family_without_font_face: Font families used without @font-face declaration: pingfang sc, microsoft yahei` | hyperframes 渲染时不识别 PingFang SC/Microsoft YaHei → 改 `font-family: sans-serif` 兜底（Windows render 时实际用 Microsoft YaHei 系统字体） | v1.5.0 |
| F-016 | 2026-06-19 | Phase 3 | `hyperframes lint` 报 `media_missing_id: <audio> has data-start but no id attribute. The renderer requires id to discover media elements — this audio will be SILENT in renders` | 给 audio 加 `id="voiceover"`（任意唯一字符串即可）。v1.5.0 完整模板固定此 id | v1.5.0 |
| F-017 | 2026-06-19 | Phase 3 | 用户多次复述"首页文字加大加粗，兼顾封面效果"但 SKILL.md 没有封面规范，每次都要重新设计 | 固化「首页封面规范」：主标题 148px / weight 900 / max-width 1700px / text-shadow 品牌色微光 + kicker 36px 600 绿 + 副标 46px 500 + 左上角标 28px（14px 绿点 + 大写英文） + 右下页码 24px（"01 / 08"） + 渐变背景 `#FFFFFF→#F0F4F1`。详见 v1.5.0「🎨 视觉风格规范」 | v1.5.0 |
| F-018 | 2026-06-19 | Phase 3 | SKILL.md 含多套 HTML 模板（harness-intro 4 页版式 / 浅色 vs 深色对比 / 完整 HTML 头部内嵌），用户每次出片 AI 不知道用哪套 | ①`templates/light-style-wx-agent-ai.html` 沉淀为**唯一标准模板**（lint 0 errors）②删除 `examples/harness-intro/` 深色风格示例③删除「4 页版式参考」「浅色 vs 深色对比」「完整 HTML 头部」3 处冗余模板④8 页版式表改为与模板文件 1:1 对应（带 CSS 类名） | v1.5.1 |
| F-019 | 2026-06-19 | Phase 0.3 | 微信 Agent 案例 39 句字幕中 27 句 < 10 字（69% 太短）："嗯..."（5字）、"嗯... 想象一下"（5字）、"过去"（4字）... 观众眼睛跟不上画面切换 | ①硬约束表新增 #6「字幕 ≥ 10 字」②Phase 0.3 新增「📏 字幕字数硬约束」章节（参数表 + 原理 + 切句规则 + 验证脚本）③`SubsGen.py` `generate_subtitles_for_text` 默认 min_chars 6→10、max_chars 18→22；CLI `--min-chars` 默认 6→10 | v1.5.2 |
| F-020 | 2026-06-19 | Phase 0.3 | v1.5.2 的 5 步切句规则里 Step 3 "长句拆分"暗示次级标点可优先于自然句切句，实际可能拆散自然句（例如把"现在的玩法是做一个 App，大家来用"拆成"现在的玩法是做一个 App，"+ "大家来用"破坏语义完整性） | ①5 步切句规则改写为「按自然句优先」原则：自然句边界神圣不可破，次级标点只作为自然句内部超长时的拆分点②明确「自然句完整优先于字数硬约束」——短自然句可继续向后合并而非被切碎③新增「边界优先级」表④新增硬规则「绝不允许跨自然句切句」 | v1.5.3 |

---

## 📝 记录模板（新错误使用此模板）

```markdown
| F-XXX | YYYY-MM-DD | Phase X.Y | [触发词/输入示例] | [错误现象/截图/日志] | [根因分析] | P0/P1/P2 |
```

---

## 🔗 关联

- 自我复盘模板：`references/self-review-template.md`
- 回归测试用例：`references/test_pool.md`
- 审核报告：`grading.json`