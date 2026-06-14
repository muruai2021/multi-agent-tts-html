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

## 🔗 关联

- 失败案例日志：`references/failure_case_log.md`
- 回归测试：`references/test_pool.md`
- 审核报告：`grading.json`