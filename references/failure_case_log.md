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