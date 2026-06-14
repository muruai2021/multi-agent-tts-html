---
voice: 国语男声
speed: 1.0
volume: 1.5
insert_pauses: true
pause_ms: 600
---

# Harness 是什么？(不读出)

你以为 AI 是直接跟你聊的？

中间其实隔着一个东西——harness。

说白了...harness 就是一个中间层。

你按回车发消息...harness 先接到，决定要不要调工具、读文件、跑命令。

举个真实例子。

settings.json 里配权限——PreToolUse 钩子先跑、PostToolUse 再扫一遍日志，最后才轮到模型回话。

这中间任何一步拦住...对话就停了。

所以 90% 的"AI 抽风"...根因都在 harness 配置上。

下次出问题别光骂 AI，先翻 harness。