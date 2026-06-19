# Self-Review Template — multi-agent-tts-html

> **目的**：当技能出现失败或异常时，按此模板做根因分析 + 改进建议，确保每次错误都转化为技能升级。

---

## 🎯 触发条件（满足任一即触发自复盘）

1. **新错误录入** — 任何 phase 出现未在 `failure_case_log.md` 的失败
2. **同一错误复发** — F-XXX 标记的错误再次出现
3. **用户主动反馈** — 用户报告"这个技能有问题"
4. **版本发布前** — 每次 minor/major 版本升级前

---

## 📋 复盘流程（5 步）

### Step 1：现象复现

- **错误 ID**：F-XXX
- **Phase**：Phase X.Y
- **触发词**：（用户输入原文）
- **完整复现命令**：（最小可复现命令链）
- **期望输出**：
- **实际输出**：（错误截图 / 日志 / 文件）

### Step 2：根因分析（5 Why）

逐层追问，至少 3 层：

1. **Why 1**：（最直接的原因）
2. **Why 2**：（Why 1 的根因）
3. **Why 3**：（Why 2 的根因）
4. **Why 4**：（如需要）
5. **Why 5**：（如需要）

> 例：
> - W1: 字幕只有第一句 → JS 轮询 `audio.currentTime` 没触发
> - W2: 没触发 → HyperFrames 截图模式不更新 `currentTime`
> - W3: 不更新 → 截图是离屏渲染，没有真实音频播放
> - W4: 离屏渲染 → 用户用 Puppeteer/Playwright headless 模式
> - W5: 根本方案 → 不用 JS 轮询，改用 CSS timed div（每句独立 `data-start/data-duration`）

### Step 3：影响范围

| 维度 | 评估 |
|------|------|
| 受影响 Phase | Phase 0.3 / Phase 3 / Phase 4 |
| 受影响文件 | tts-with-subs.py / SubsGen.py / SKILL.md |
| 受影响用户 | 全部 HyperFrames 用户 |
| 数据损失 | 无 / 有（描述） |

### Step 4：改进建议（具体可操作）

| # | 改进项 | 优先级 | 负责人 | 验收标准 |
|---|--------|--------|--------|----------|
| 1 | （修复代码）| P0 | — | 通过 X 测试 |
| 2 | （加回归测试）| P0 | — | RE-XXX 跑通 |
| 3 | （更新文档）| P1 | — | SKILL.md 同步 |

### Step 5：闭环

1. ☐ 修复代码 → commit
2. ☐ 在 `failure_case_log.md` 把 F-XXX 从 🔴 移到 ✅
3. ☐ 在 `test_pool.md` 增加 RE-XXX 回归用例
4. ☐ 更新 SKILL.md / README.md（如有文档变更）
5. ☐ 下一个版本发布前跑一遍 `test_pool.md` 全量回归

---

## 🎨 视觉风格自检清单（v1.5.0 新增）

### 浅色风格自检（默认必过）

- [ ] 底色用 `#FAFAF7` 或渐变白 `#FFFFFF→#F0F4F1`，**不是纯黑**？
- [ ] 文字主色 `#1A1A1A`（深灰黑），**不是纯黑 #000**？
- [ ] 品牌主色 `#07C160`（微信绿）作为强调？
- [ ] 卡片用白底 + 浅阴影，**不是深色卡片**？
- [ ] `font-family: sans-serif`（避免 hyperframes 不识别的 PingFang SC）？
- [ ] lint `font_family_without_font_face` 0 errors？

### 首页封面自检（强制）

- [ ] 主标题字号 ≥ 120px（推荐 148px）？
- [ ] 主标题字重 = 900（黑体）？
- [ ] 主标题加 `text-shadow: 0 4px 24px rgba(7,193,96,0.08)` 品牌色微光？
- [ ] kicker 36px 600 #07C160 letter-spacing 8px？
- [ ] 左上角标 28px 700 #888（14px 绿点 + 大写英文）？
- [ ] 右下页码 24px 600 #999（"01 / 08" 格式）？
- [ ] 背景用 `linear-gradient(135deg, #FFFFFF 0%, #F0F4F1 100%)` 渐变？

### 第一人称自检（硬约束 #5）

- [ ] 全文"我"出现次数 = 0？
- [ ] 禁用 "我跟你说 / 我跟你讲 / 我有个朋友 / 反正我 / 我直说"？
- [ ] 用 "说白了 / 其实 / 告诉你 / 想象一下 / 嗯 / 知道吧" 替代？

### lint 全过自检（渲染前必跑）

```bash
hyperframes lint <project>
# 期望：0 errors（warnings 可忽略：studio_missing_editable_id 是非阻塞）
```

- [ ] `missing_timeline_registry` 已注册 `window.__timelines`？
- [ ] `media_missing_id` audio 已有 `id="voiceover"`？
- [ ] `overlapping_clips_same_track` page slide duration 减 0.05s？
- [ ] `font_family_without_font_face` 字体用 sans-serif 兜底？

### 📏 字幕字数自检（v1.5.2 硬约束 #6）

- [ ] 解析 `*.segments.json` 所有 cues，正则 `[一-鿿]` 统计中文字符数 = 0 条 < 10 字？
- [ ] 末句允许 ≥ 5 字（容忍短收尾）？
- [ ] `SubsGen.py` 中 `min_chars: int = 10`（不是 6）？
- [ ] CLI `--min-chars` 默认值 = 10？

### 🎯 按自然句断句自检（v1.5.3 第一原则）

- [ ] 解析 `*.segments.json`，验证单条 cue 内容**不跨越 2 个以上** `。！？` 边界？
- [ ] grep SKILL.md，验证包含"按自然句断句"+"自然句边界神圣不可破"？
- [ ] 单自然句 > 22 字时（次级标点拆分），拆分后的两段都 ≥ 10 字？
- [ ] 短自然句（< 10 字）应被合并到下一自然句而非独立成句？

### 🔧 SubsGen.py 中文字数自检（v1.5.4 关键修复）

- [ ] grep `SubsGen.py` 验证所有 min/ideal/max 阈值判断都改用 `_cn_count()`（不能用 `len()`）
- [ ] Step 3.5 短段回合并存在（循环 while changed）
- [ ] Step 6 末段吸附存在
- [ ] 单元测试：wx-agent-ai 口播稿切完 100% ≥ 10 中文字

---

## 🔗 关联

- 失败案例日志：`references/failure_case_log.md`
- 回归测试：`references/test_pool.md`
- 审核报告：`grading.json`