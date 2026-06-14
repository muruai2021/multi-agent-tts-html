# Test Pool — multi-agent-tts-html

> **目的**：覆盖核心功能的自动化测试 + 已修复 bug 的回归测试。每次发布前必跑全量。

---

## 🧪 测试类型说明

| 类型 | 范围 | 工具 |
|------|------|------|
| TC-SYNTAX | Python 语法 / Markdown 语法 / JSON 格式 | `python -m py_compile` / `json.tool` |
| TC-FUNC | 核心功能（MD→MP3 / 字幕切句 / 时间戳归一化）| `pytest` |
| TC-BOUND | 边界场景（空输入 / 超长 / 特殊字符 / 并发）| `pytest` |
| TC-SEC | 安全（路径穿越 / 注入 / 凭证泄露）| `pytest` + `bandit` |

---

## 📋 测试用例清单

### TC-SYNTAX — 语法验证

| ID | 用例 | 预期 | 状态 |
|----|------|------|------|
| TC-SYN-001 | `python -m py_compile scripts/md2mp3.py` | exit 0 | ✅ |
| TC-SYN-002 | `python -m py_compile scripts/tts-gen.py` | exit 0 | ✅ |
| TC-SYN-003 | `python -m py_compile scripts/tts-with-subs.py` | exit 0 | ✅ |
| TC-SYN-004 | `python -m py_compile scripts/SubsGen.py` | exit 0 | ✅ |
| TC-SYN-005 | `python -c "import json; json.load(open('grading.json'))"` | exit 0 | ✅ |

### TC-FUNC — 功能测试

| ID | 用例 | 预期 | 状态 |
|----|------|------|------|
| TC-FUNC-001 | `parse_markdown_to_text()` 去除 frontmatter/标题/代码块 | 剩余纯文本 | ⬜ |
| TC-FUNC-002 | `parse_frontmatter()` 解析 voice/speed/volume | dict 正确 | ⬜ |
| TC-FUNC-003 | `split_to_caption_sentences()` 按 。！？ 切句 | 句数正确 | ⬜ |
| TC-FUNC-004 | `split_to_caption_sentences()` 短句合并 | 合并后长度 ≥ min_chars | ⬜ |
| TC-FUNC-005 | `estimate_durations()` 计算中文字数 × 4 字/秒 | 时长在 ±20% | ⬜ |
| TC-FUNC-006 | `assign_timestamps()` 归一化到 audio_duration | sum(durations) == audio_duration | ⬜ |
| TC-FUNC-007 | `to_srt()` SRT 格式（HH:MM:SS,mmm）| 时间格式正确 | ⬜ |
| TC-FUNC-008 | `to_vtt()` VTT 格式（WEBVTT 头 + HH:MM:SS.mmm）| 头正确 | ⬜ |
| TC-FUNC-009 | `to_json()` 输出 JSON 时间戳 | 可被 json.loads 解析 | ⬜ |
| TC-FUNC-010 | `probe_audio_duration()` ffprobe 探测 | 返回 float 或 None | ⬜ |

### TC-BOUND — 边界测试

| ID | 用例 | 输入 | 预期 | 状态 |
|----|------|------|------|------|
| TC-BOUND-001 | 空文本 | `""` | 字幕空数组 | ⬜ |
| TC-BOUND-002 | 单字 | `"啊"` | 字幕空数组（< 4 字）| ⬜ |
| TC-BOUND-003 | 5000 字长文本 | 5000 中文字 | 切分为多段调用 TTS | ⬜ |
| TC-BOUND-004 | 超长单句（无标点 100 字）| "啊啊啊啊..." | 保留整段（或 max_chars 切）| ⬜ |
| TC-BOUND-005 | emoji + 中文 | "你好 🎉 世界" | 不崩溃 | ⬜ |
| TC-BOUND-006 | 全角标点 + 半角混合 | "Hello, 你好。" | 正确切句 | ⬜ |
| TC-BOUND-007 | frontmatter 缺失 | 无 `---` 块 | 用默认配置 | ⬜ |
| TC-BOUND-008 | 输出路径无权限 | `/root/output.mp3`（Win 无权限）| 友好错误 | ⬜ |
| TC-BOUND-009 | TTS API 超时 | mock 30s 延迟 | 降级到 Edge TTS | ⬜ |
| TC-BOUND-010 | ffprobe 不存在 | PATH 无 ffprobe | 字幕用估算时长 | ⬜ |
| TC-BOUND-011 | 并发调用（多进程）| 4 进程同时调 | 无文件冲突 | ⬜ |

### TC-SEC — 安全测试

| ID | 用例 | 输入 | 预期 | 状态 |
|----|------|------|------|------|
| TC-SEC-001 | 路径穿越 | `../../../etc/passwd` | 拒绝或转义 | ⬜ |
| TC-SEC-002 | API Key 硬编码扫描 | grep `password\|api_key.*=.*['"]\w{8,}` | 0 命中 | ⬜ |
| TC-SEC-003 | ffmpeg 注入 | 文件名含 `'; rm -rf /` | 不执行恶意命令 | ⬜ |
| TC-SEC-004 | MD 嵌入 JS | `script.md` 含 `<script>alert(1)</script>` | 清理后无脚本 | ⬜ |
| TC-SEC-005 | 环境变量优先级 | 系统已有 `MINIMAX_API_KEY` | 不被 .env 覆盖 | ⬜ |

### RE-XXX — 回归测试（已修复 bug 验证）

| ID | 来源 | 用例 | 状态 |
|----|------|------|------|
| RE-001 | F-001 | 字幕只有第一句 → 验证 timed div 方案 | ⬜ |
| RE-002 | F-002 | 页面重叠 → 验证 visibility:hidden | ⬜ |
| RE-003 | F-003 | TTS rate limit → 验证 Edge TTS 降级 | ⬜ |
| RE-004 | F-004 | 渲染失败 → 验证 lint 报错 | ⬜ |
| RE-005 | F-005 | 字幕换行 → 验证 white-space: nowrap | ⬜ |
| RE-006 | F-006 | 音字不同步 → 验证 ffprobe 归一化 | ⬜ |
| RE-007 | F-007 | 文档可发现性 → grep SKILL.md 验证「📁 文件存放约定」章节存在且包含「当前工作目录」关键词 | ⬜ |
| RE-008 | F-008 | 浏览器打开 HTML 不黑屏 → Playwright 打开后立即截图，验证第一页可见 + 4 个 slide 元素都存在 | ⬜ |
| RE-009 | F-009 | **F-002 复现防护** → Playwright 在 audio.currentTime=12s 时截图，验证只有 page-2 可见（page-1/3/4 visibility:hidden）。同时在 audio.currentTime=0s 截图，验证只有 page-1 可见 | ⬜ |
| RE-010 | F-010 | **GATE 1 强制阻断** → `tts-with-subs.py` 不加 `--gate1-approved` 应 exit(1)；加 flag 应正常跑通。加 `md2mp3.py` 同理 | ⬜ |
| RE-011 | F-011 | **字幕样式规范合规** → 解析 HTML，验证 `.sub-cue` 必须有 `font-size:42px`、`background:none`、`text-shadow` 3 层；`#sub-bar` 必须有 `bottom:118px`。不符合任意一项 = 不通过 | ⬜ |

---

## 🚀 运行命令

```bash
# 全部测试
cd E:\work\skills\multi-agent-tts-html
pytest tests/ -v

# 仅回归测试
pytest tests/ -v -k "RE-"

# 仅功能测试
pytest tests/ -v -k "TC-FUNC"

# 覆盖率
pytest tests/ --cov=scripts --cov-report=term-missing
```

## 📊 覆盖率目标

| 模块 | 当前 | 目标 |
|------|------|------|
| `tts-gen.py` | — | ≥ 80% |
| `tts-with-subs.py` | — | ≥ 80% |
| `SubsGen.py` | — | ≥ 80% |
| `md2mp3.py` | — | ≥ 70%（UI 逻辑）|
| **总体** | — | **≥ 80%** |

---

## 🔗 关联

- 失败日志：`references/failure_case_log.md`
- 复盘模板：`references/self-review-template.md`
- 审核报告：`grading.json`