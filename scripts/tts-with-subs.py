#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts-with-subs.py - 带字幕功能的 MiniMax TTS 生成器

用法:
    # 单条 + 字幕
    python tts-with-subs.py "你好世界" --output hello --srt --vtt

    # 批量 + 字幕
    python tts-with-subs.py --batch texts.txt --output-dir ./out/

    # MD → MP3 + SRT + VTT
    python tts-with-subs.py script.md --md --output video

输出:
    <name>.mp3       - 音频
    <name>.srt       - SRT 字幕(可选)
    <name>.vtt       - WebVTT 字幕(可选)
    <name>.segments.json - JSON 时间戳(可选)

特性:
    - 单次 TTS 调用(省 RPM 配额)
    - 用 ffprobe 探测真实音频时长
    - 自动切分字幕句 + 时间戳归一化
    - SRT / VTT / JSON 三种格式
"""

import argparse
import os
import re
import sys
import importlib.util
from pathlib import Path
from typing import Optional

# 动态导入同目录下的 tts-gen.py(文件名带连字符,不能直接 import)
_spec = importlib.util.spec_from_file_location(
    "tts_gen", Path(__file__).resolve().parent / "tts-gen.py"
)
_tts_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tts_gen)

# 导入字幕生成模块
_spec2 = importlib.util.spec_from_file_location(
    "SubsGen", Path(__file__).resolve().parent / "SubsGen.py"
)
_subs = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_subs)


# ============== Markdown 解析 ==============

def parse_markdown_to_text(md_path: str) -> str:
    """简化版 MD 解析: 提取正文,去除 frontmatter/标题/代码块/链接标记"""
    text = Path(md_path).read_text(encoding="utf-8")
    # 去除 frontmatter
    text = re.sub(r"^---.*?---\s*\n", "", text, count=1, flags=re.DOTALL)
    # 去除代码块
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # 去除行内代码
    text = re.sub(r"`[^`]+`", "", text)
    # 去除标题
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    # 去除链接标记,保留文本
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # 去除加粗/斜体标记
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # 多空行合并
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 合并换行为空格(口播稿不需换行)
    text = re.sub(r"\s*\n\s*", " ", text)
    return text.strip()


# ============== TTS 调用(委托给 tts-gen) ==============

def call_tts(text: str, voice_id: str, api_key: str,
             speed: float, volume: float, fmt: str = "mp3",
             bitrate: int = 128000) -> bytes:
    return _tts_gen.call_tts_once(text, voice_id, api_key, speed, volume, fmt, bitrate)


# ============== 主流程 ==============

def process_text(
    text: str,
    voice_name: str,
    api_key: str,
    output_path: str,
    speed: float = 1.0,
    volume: float = 1.5,
    fmt: str = "mp3",
    bitrate: int = 128000,
    emit_srt: bool = False,
    emit_vtt: bool = False,
    emit_json: bool = False,
    min_chars: int = 6,
    max_chars: int = 18,
) -> dict:
    """单条: 生成音频 + 字幕"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    voice_id = _tts_gen.VOICE_PRESETS.get(voice_name, voice_name)

    print(f"[TTS] 生成音频: {output_path.name}")
    audio_data = call_tts(text, voice_id, api_key, speed, volume, fmt, bitrate)
    output_path.write_bytes(audio_data)
    print(f"      完成: {len(audio_data)/1024:.1f} KB")

    result = {"audio": str(output_path), "subs": {}}
    if not (emit_srt or emit_vtt or emit_json):
        return result

    # 生成字幕(归一化到真实音频时长)
    print(f"[SUB] 生成字幕...")
    sub = _subs.generate_subtitles_for_text(
        text,
        audio_path=str(output_path),
        min_chars=min_chars,
        max_chars=max_chars,
    )
    print(f"      句数: {len(sub['sentences'])}")
    if sub["audio_duration"]:
        print(f"      音频时长: {sub['audio_duration']:.2f}s (已归一化)")

    base = output_path.with_suffix("")  # 去掉 .mp3
    formats = []
    if emit_srt: formats.append("srt")
    if emit_vtt: formats.append("vtt")
    if emit_json: formats.append("json")

    written = _subs.save_subtitles(
        base.parent,
        base.name,
        srt=sub["srt"] if emit_srt else None,
        vtt=sub["vtt"] if emit_vtt else None,
        json_data=sub["json"] if emit_json else None,
    )
    for fmt, p in written.items():
        print(f"      {fmt.upper()}: {p}")
        result["subs"][fmt] = p

    return result


def main():
    # 先加载 .env
    _tts_gen.load_env_file()

    parser = argparse.ArgumentParser(
        description="带字幕功能的 MiniMax TTS 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单条 + SRT + VTT
  python tts-with-subs.py "你好世界" --output hello --srt --vtt

  # 批量生成
  python tts-with-subs.py --batch texts.txt --output-dir ./out/ --srt

  # MD 文件 → MP3 + 字幕
  python tts-with-subs.py script.md --md --output video --srt --vtt

  # 已有音频,只生成字幕
  python tts-with-subs.py script.md --md --audio-only audio.mp3 \\
    --output video --srt --vtt
        """,
    )
    parser.add_argument("text", nargs="?", help="要转换的文本(单条模式)")
    parser.add_argument("--batch", help="批量模式: 每行一条的文本文件")
    parser.add_argument("--md", action="store_true", help="输入是 Markdown 文件")
    parser.add_argument("--audio-only", help="仅基于已有音频生成字幕(配合 --srt/--vtt)")

    parser.add_argument("--voice", "-v", default="国语男声", help="音色")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="语速 0.5-2.0")
    parser.add_argument("--volume", default=1.5, help="音量 0.0-2.0")
    parser.add_argument("--format", "-f", default="mp3",
                        choices=["mp3", "wav", "pcm"], help="音频格式")
    parser.add_argument("--bitrate", type=int, default=128000, help="比特率")

    parser.add_argument("--output", "-o", default=None, help="输出文件路径(单条)")
    parser.add_argument("--output-dir", default="./output", help="输出目录(批量)")

    parser.add_argument("--srt", action="store_true", help="输出 SRT 字幕")
    parser.add_argument("--vtt", action="store_true", help="输出 WebVTT 字幕")
    parser.add_argument("--json", dest="emit_json", action="store_true",
                        help="输出 JSON 时间戳")
    parser.add_argument("--all-subs", action="store_true",
                        help="输出 SRT + VTT + JSON(等价于 --srt --vtt --json)")
    parser.add_argument("--min-chars", type=int, default=6, help="字幕句最短字符数")
    parser.add_argument("--max-chars", type=int, default=18, help="字幕句最长字符数")

    parser.add_argument("--api-key", default=None, help="API Key(默认从 .env / 环境变量)")

    # ⛔ GATE 1 强制阻断:必须显式声明已通过人工审核
    parser.add_argument("--gate1-approved", action="store_true",
                        help="[GATE 1] 显式声明已通过口播稿人工审核(必填)。"
                             "未加此 flag 脚本会拒绝运行。详见 SKILL.md「🛑 GATE 1 技术阻断机制」。")

    args = parser.parse_args()

    if args.all_subs:
        args.srt = args.vtt = args.emit_json = True

    # ⛔ 强制阻断:未审核禁止 TTS
    if not args.gate1_approved:
        print("=" * 70)
        print("[GATE1 BLOCKED] 未通过人工审核,禁止调用 TTS API")
        print("=" * 70)
        print()
        print("  按 SKILL.md「GATE 1」清单完成 10 项自检 + 人工确认 A 通过。")
        print()
        print("  然后重新跑命令,在末尾显式加 --gate1-approved:")
        print("    python scripts/tts-with-subs.py <口播稿.md> --md \\")
        print("      --output <项目名> --all-subs --gate1-approved")
        print()
        print("  跳过审核的代价:浪费 API 配额 + 返工成本 >> 审核成本。")
        print("=" * 70)
        sys.exit(1)

    # 解析 API Key
    api_key = args.api_key or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("[ERR] 未设置 API Key,请通过 .env / 环境变量 / --api-key 提供")
        sys.exit(1)

    # 模式 1: 仅生成字幕(已有音频)
    if args.audio_only:
        if not (args.srt or args.vtt or args.emit_json):
            print("[ERR] --audio-only 模式必须配合 --srt / --vtt / --json")
            sys.exit(1)
        text = parse_markdown_to_text(args.text) if args.md else args.text
        if not text:
            print("[ERR] 需要提供文本(--md 或 text 参数)")
            sys.exit(1)
        sub = _subs.generate_subtitles_for_text(
            text, audio_path=args.audio_only,
            min_chars=args.min_chars, max_chars=args.max_chars,
        )
        base = Path(args.output or args.audio_only).with_suffix("")
        base.parent.mkdir(parents=True, exist_ok=True)
        written = _subs.save_subtitles(
            base.parent, base.name,
            srt=sub["srt"] if args.srt else None,
            vtt=sub["vtt"] if args.vtt else None,
            json_data=sub["json"] if args.emit_json else None,
        )
        print(f"[OK] 已基于 {args.audio_only} 生成字幕")
        for fmt, p in written.items():
            print(f"     {fmt.upper()}: {p}")
        return

    # 模式 2: 批量
    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"[ERR] 批量文件不存在: {batch_path}")
            sys.exit(1)
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        lines = [l.strip() for l in batch_path.read_text(encoding="utf-8").split("\n") if l.strip()]
        print(f"[BATCH] 共 {len(lines)} 条")
        for i, line in enumerate(lines, 1):
            print(f"\n--- [{i}/{len(lines)}] ---")
            try:
                out_file = out_dir / f"audio_{i:03d}"
                process_text(
                    line, args.voice, api_key, str(out_file) + ".mp3",
                    args.speed, args.volume, args.format, args.bitrate,
                    args.srt, args.vtt, args.emit_json,
                    args.min_chars, args.max_chars,
                )
            except Exception as e:
                print(f"[ERR] 第 {i} 条失败: {e}")
        return

    # 模式 3: 单条 / MD
    if not args.text:
        parser.print_help()
        sys.exit(1)

    text = parse_markdown_to_text(args.text) if args.md else args.text
    if not text:
        print("[ERR] 文本为空")
        sys.exit(1)

    if args.output:
        out_path = args.output
        if not out_path.endswith("." + args.format):
            out_path += "." + args.format
    else:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"audio_{ts}.{args.format}"

    process_text(
        text, args.voice, api_key, out_path,
        args.speed, args.volume, args.format, args.bitrate,
        args.srt, args.vtt, args.emit_json,
        args.min_chars, args.max_chars,
    )


if __name__ == "__main__":
    main()
