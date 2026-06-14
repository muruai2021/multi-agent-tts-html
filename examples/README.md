# 示例项目（Examples）

> **不要把产物放在这里！** 用户产物应放在你执行命令时的**当前工作目录**（详见 [SKILL.md 📁 文件存放约定](../SKILL.md#-文件存放约定先看这条再开工)）。
>
> `examples/` 目录是**只读的演示样本**，展示本 Skill 端到端流水线跑出来的真实产物。

---

## 📂 现有示例

| 示例 | 主题 | 时长 | 文件 | 状态 |
|------|------|------|------|------|
| **[harness-intro/](harness-intro/)** | 关于 harness 的技术介绍（Claude Code 视角）| 34.19s | 9 件 | ✅ v1（首条流水线）|

---

## 🆕 添加新示例

1. 在 `examples/<你的项目名>/` 目录里放 8 类产物（命名规范见下）
2. 加 `examples/<你的项目名>/README.md` 说明：主题 / 关键设计 / 复现命令
3. 在本文件表格里登记一行
4. PR 提交

### 命名规范

```
examples/<项目名>/
├── README.md                          ← 本目录的项目说明
├── <YYYYMMDD>_<关键词>_v1.md          ← 口播稿
├── <YYYYMMDD>_<关键词>_v1.mp3         ← TTS 音频
├── <YYYYMMDD>_<关键词>_v1.srt         ← SRT 字幕
├── <YYYYMMDD>_<关键词>_v1.vtt         ← WebVTT 字幕
├── <YYYYMMDD>_<关键词>_v1.segments.json ← JSON 时间戳
├── <YYYYMMDD>_<关键词>_v1_hf.html     ← HyperFrames HTML
├── <YYYYMMDD>_<关键词>_v1_mapping.md  ← GATE 2 内容映射表
├── <YYYYMMDD>_<关键词>_v1.mp4        ← 🎬 最终视频
└── 过程.md                            ← 生成过程记录
```

### 不需要放的东西

- ❌ `.env` / API Key
- ❌ 临时调试文件
- ❌ `/tmp/harness-intro/` 等中间产物