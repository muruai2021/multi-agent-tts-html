#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SubsGen.py - 字幕生成工具(模块)
提供:
  - 文本切分为字幕句
  - 时间戳估算(基于字数+停顿符)
  - SRT / WebVTT / JSON 格式输出
  - 归一化到真实音频时长(可选,需 ffprobe)

无外部依赖,仅使用标准库 + 可选 subprocess(ffprobe)
"""
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# ============== 文本切分 ==============

def _cn_count(s: str) -> int:
    """中文字符数（v1.5.4 修复：与 SKILL.md 文档一致，不含标点空白）"""
    return len(re.findall(r'[一-鿿]', s))


def split_to_caption_sentences(
    text: str,
    min_chars: int = 10,
    ideal_chars: int = 18,
    max_chars: int = 26,
) -> List[str]:
    """
    把口播文本切分为字幕句(v3 - 按自然句优先 + 中文字数硬约束).

    设计原则（v1.5.4 重构）:
      1. 按自然句（。！？）切分（边界神圣不可破）
      2. 短句(< min_chars)与下一自然句合并，直到 ≥ min_chars
      3. 单自然句 > ideal_chars → 在其内部按次级标点切
      4. 单自然句 > max_chars → 兜底在最近次级标点硬拆
      5. 绝不允许 < min_chars 字（除非全文末句）
      6. 计数单位：中文字符数（_cn_count），不含标点/空白/ASCII

    修复历史:
      v1.0.0 - 初版
      v1.0.1 - 保留全角空格(　) 修复段落节奏
      v1.5.2 - min_chars 默认 6→10
      v1.5.3 - 「按自然句断句」作为第一原则
      v1.5.4 - 关键修复：min/ideal/max 阈值改用 _cn_count() 中文字数（之前用 len() 含标点导致 9 字自然句被认作 11 字符通过硬约束）
    """
    # 仅合并半角空白(空格/Tab/换行),保留全角空格(　)和段落换行节奏
    text = re.sub(r'[ \t\r\n]+', ' ', text).strip()
    if not text:
        return []

    # 1. 主切分: 。！？  (保留标点) — 自然句边界
    primary = re.split(r'([。！？!?])', text)
    sentences = []
    for i in range(0, len(primary) - 1, 2):
        s = (primary[i] + (primary[i+1] if i+1 < len(primary) else "")).strip()
        if s:
            sentences.append(s)
    if len(primary) % 2 == 1 and primary[-1].strip():
        sentences.append(primary[-1].strip())

    # 2. 短句合并（自然句完整优先）— 用中文字数判断
    merged = []
    buffer = ""
    for s in sentences:
        if not buffer:
            buffer = s
        elif _cn_count(buffer) < min_chars:
            # 累积到 min_chars，不等到 ideal_chars——避免 s 被丢弃
            buffer += s
            if _cn_count(buffer) >= min_chars:
                merged.append(buffer)
                buffer = ""
        else:
            merged.append(buffer)
            buffer = s
    if buffer:
        merged.append(buffer)

    # 3. 单自然句 > ideal_chars → 在自然句内部按次级标点切（不跨自然句）
    result = []
    for s in merged:
        if _cn_count(s) <= ideal_chars:
            result.append(s)
            continue

        # 找所有次级标点位置（在字符之后的位置）
        sub_breaks = []
        for m in re.finditer(r'[,;:、——，；：]+', s):
            sub_breaks.append(m.end())  # 标点之后的位置

        if not sub_breaks:
            # 没有次级标点：若 ≤ max_chars 保留整段；否则兜底在 max_chars 附近切
            if _cn_count(s) <= max_chars:
                result.append(s)
            else:
                best = -1
                for i, ch in enumerate(s):
                    if ch in ',;:。！？、——，；：' and abs(i - max_chars) < abs(best - max_chars):
                        best = i + 1
                if best > 0 and best < len(s):
                    result.append(s[:best].strip())
                    rest = s[best:].strip()
                    if rest:
                        result.append(rest)
                else:
                    result.append(s)  # 无可切点，保留整段（max_chars 超限罕见）
            continue

        # 按次级标点切分，每段目标 ideal_chars~max_chars（中文字数）
        cur = ""
        for i, ch in enumerate(s):
            cur += ch
            if ch in ',;:。！？、——，；：':
                # 在标点后切（cur 已包含该标点）
                if _cn_count(cur) >= min_chars:
                    result.append(cur.strip())
                    cur = ""
        if cur.strip():
            result.append(cur.strip())

    # 3.5 短段回合并（v1.5.4）：前段 < min_chars → 把当前段也吸进来（或前段 ≥ min_chars + 当前段 < min_chars → 当前段吸到前段）
    # 简化版：循环合并所有 < min_chars 的相邻对
    if result:
        changed = True
        while changed:
            changed = False
            merged_back = []
            for s in result:
                if merged_back and _cn_count(s) < min_chars:
                    # 当前段 < min_chars → 吸到上一段
                    merged_back[-1] = (merged_back[-1] + s).strip()
                    changed = True
                else:
                    merged_back.append(s)
            result = merged_back

    # 4. 最后处理: 拆过长的（兜底，中文字数判断）
    final = []
    for s in result:
        s = s.strip()
        if not s:
            continue
        if _cn_count(s) > max_chars:
            # 仍过长，找最近标点切（不硬切）
            best = -1
            for i, ch in enumerate(s):
                if ch in ',;:。！？、——，；：.' and abs(i - max_chars) < abs(best - max_chars):
                    best = i + 1
            # 兜底：若 best 落到末尾/无效，退而求其次找任一可切点（保证两段都 >= min_chars）
            if not (0 < best < len(s)):
                fallback = -1
                for i, ch in enumerate(s):
                    if ch in ',;:。！？、——，；：.' and 0 < i < len(s) - 1:
                        if _cn_count(s[:i+1].strip()) >= min_chars and _cn_count(s[i+1:].strip()) >= min_chars:
                            fallback = i + 1
                            break  # 取第一个能切的就行
                best = fallback
            if 0 < best < len(s):
                final.append(s[:best].strip())
                rest = s[best:].strip()
                if rest:
                    final.append(rest)
            else:
                final.append(s)
        else:
            final.append(s)

    # 5. 合并微短句（中文字数 < 5 视为微短句）
    cleaned = []
    for s in final:
        if cleaned and _cn_count(s) < 5 and _cn_count(cleaned[-1]) < ideal_chars + 4:
            cleaned[-1] = (cleaned[-1] + s).strip()
        else:
            cleaned.append(s)

    # 6. 末段吸附（v1.5.4 新增）：最后 1 句 < 10 字 → 吸附到倒数第 2 句
    if len(cleaned) >= 2 and _cn_count(cleaned[-1]) < min_chars:
        last = cleaned.pop()
        cleaned[-1] = (cleaned[-1] + last).strip()

    return [s for s in cleaned if _cn_count(s) >= 1]


# ============== 时间戳估算 ==============

def estimate_durations(
    sentences: List[str],
    base_speed: float = 4.0,
    pause_overhead: float = 0.3,
) -> List[float]:
    """
    估算每句朗读时长(秒).
      - base_speed 字/秒(中文朗读,默认 4.0，与 SKILL.md 模板 B 一致：240 字/分)
      - 停顿符加成: ... +0.5s, —— +0.3s, ,;: +0.15s
    """
    durations = []
    for s in sentences:
        chinese_chars = len(re.findall(r'[一-鿿]', s))
        duration = chinese_chars / base_speed
        duration += s.count('...') * 0.5
        duration += s.count('——') * 0.3
        duration += (s.count(',') + s.count(';') + s.count(':')) * 0.15
        # 句末标点加 0.2s 自然停顿
        if re.search(r'[。！？.!?]$', s):
            duration += 0.2
        durations.append(max(duration, 0.3))  # 至少 0.3s
    return durations


def assign_timestamps(
    sentences: List[str],
    audio_duration: Optional[float] = None,
) -> List[Dict]:
    """
    为每句生成开始/结束时间.
    若提供 audio_duration,按比例归一化.
    """
    raw_durations = estimate_durations(sentences)
    total_raw = sum(raw_durations)

    if audio_duration and total_raw > 0:
        scale = audio_duration / total_raw
        durations = [d * scale for d in raw_durations]
    else:
        durations = raw_durations

    timestamps = []
    cursor = 0.0
    for sent, dur in zip(sentences, durations):
        timestamps.append({
            "start": round(cursor, 3),
            "end": round(cursor + dur, 3),
            "duration": round(dur, 3),
            "text": sent,
        })
        cursor += dur

    return timestamps


# ============== 真实音频时长探测 ==============

def probe_audio_duration(audio_path: str) -> Optional[float]:
    """用 ffprobe 探测音频时长(秒),失败返回 None"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


# ============== 字幕格式生成 ==============

def _format_srt_time(seconds: float) -> str:
    """SRT 时间格式: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(seconds: float) -> str:
    """VTT 时间格式: HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def to_srt(timestamps: List[Dict]) -> str:
    """生成 SRT 格式字幕"""
    lines = []
    for i, ts in enumerate(timestamps, 1):
        lines.append(str(i))
        lines.append(f"{_format_srt_time(ts['start'])} --> {_format_srt_time(ts['end'])}")
        lines.append(ts["text"])
        lines.append("")  # 空行分隔
    return "\n".join(lines)


def to_vtt(timestamps: List[Dict]) -> str:
    """生成 WebVTT 格式字幕"""
    lines = ["WEBVTT", ""]
    for i, ts in enumerate(timestamps, 1):
        lines.append(str(i))
        lines.append(f"{_format_vtt_time(ts['start'])} --> {_format_vtt_time(ts['end'])}")
        lines.append(ts["text"])
        lines.append("")
    return "\n".join(lines)


def to_json(timestamps: List[Dict], meta: Optional[Dict] = None) -> str:
    """生成 JSON 时间戳(用于自定义集成)"""
    out = {
        "version": 1,
        "format": ["srt", "vtt", "json"][2],
        "count": len(timestamps),
        "timestamps": timestamps,
    }
    if meta:
        out["meta"] = meta
    return json.dumps(out, ensure_ascii=False, indent=2)


# ============== 一键生成 ==============

def generate_subtitles_for_text(
    text: str,
    audio_path: Optional[str] = None,
    min_chars: int = 10,
    max_chars: int = 22,
) -> Dict:
    """
    给定口播文本,自动:
      1. 切分为字幕句
      2. 用 ffprobe 探测真实音频时长(若提供 audio_path)
      3. 生成时间戳
      4. 返回所有格式
    """
    sentences = split_to_caption_sentences(text, min_chars=min_chars, max_chars=max_chars)
    audio_duration = probe_audio_duration(audio_path) if audio_path else None
    timestamps = assign_timestamps(sentences, audio_duration=audio_duration)
    return {
        "sentences": sentences,
        "timestamps": timestamps,
        "audio_duration": audio_duration,
        "srt": to_srt(timestamps),
        "vtt": to_vtt(timestamps),
        "json": to_json(timestamps, meta={"audio_duration": audio_duration}),
    }


def save_subtitles(
    out_dir: str,
    base_name: str,
    srt: Optional[str] = None,
    vtt: Optional[str] = None,
    json_data: Optional[str] = None,
) -> Dict[str, str]:
    """保存字幕文件到 out_dir/base_name.{srt,vtt,json},返回写入的文件路径字典"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = {}
    if srt is not None:
        p = out / f"{base_name}.srt"
        p.write_text(srt, encoding="utf-8")
        written["srt"] = str(p)
    if vtt is not None:
        p = out / f"{base_name}.vtt"
        p.write_text(vtt, encoding="utf-8")
        written["vtt"] = str(p)
    if json_data is not None:
        p = out / f"{base_name}.segments.json"
        p.write_text(json_data, encoding="utf-8")
        written["json"] = str(p)
    return written


# ============== CLI ==============

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="字幕生成器(可独立调用,或作为模块导入)"
    )
    parser.add_argument("text", nargs="?", help="要生成字幕的文本")
    parser.add_argument("--audio", "-a", help="音频文件路径(用 ffprobe 探测真实时长)")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    parser.add_argument("--base-name", default="subtitles", help="输出文件基础名")
    parser.add_argument("--min-chars", type=int, default=10, help="字幕句最短字符数（v1.5.2 硬约束 ≥10）")
    parser.add_argument("--max-chars", type=int, default=18, help="字幕句最长字符数")
    parser.add_argument("--format", "-f", default="all",
                        choices=["srt", "vtt", "json", "all"],
                        help="输出格式")
    args = parser.parse_args()

    if not args.text and not args.audio:
        # 试从 stdin 读取
        import sys
        if not sys.stdin.isatty():
            args.text = sys.stdin.read().strip()

    if not args.text:
        parser.print_help()
        return

    result = generate_subtitles_for_text(
        args.text,
        audio_path=args.audio,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )

    formats = ["srt", "vtt", "json"] if args.format == "all" else [args.format]
    kwargs = {}
    if "srt" in formats: kwargs["srt"] = result["srt"]
    if "vtt" in formats: kwargs["vtt"] = result["vtt"]
    if "json" in formats: kwargs["json_data"] = result["json"]

    written = save_subtitles(args.output_dir, args.base_name, **kwargs)

    print(f"[OK] 字幕生成完成")
    print(f"     句数: {len(result['sentences'])}")
    if result["audio_duration"]:
        print(f"     音频时长: {result['audio_duration']:.2f}s (归一化)")
    for fmt, path in written.items():
        print(f"     {fmt.upper()}: {path}")


if __name__ == "__main__":
    main()
