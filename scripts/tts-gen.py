#!/usr/bin/env python3
"""
tts-gen.py - 通用 MiniMax TTS 生成器

用法:
    python tts-gen.py "要转换的文字" [选项]

示例:
    # 简单调用
    python tts-gen.py "你好世界" --output hello.mp3

    # 指定音色
    python tts-gen.py "今天天气真好" --voice 国语女声 --output test.mp3

    # 流式输出（边生成边播放）
    python tts-gen.py "实时语音播报" --stream

    # 批量生成（从文件，每行一条）
    python tts-gen.py --batch texts.txt --output-dir ./out/

特性:
    - 支持单条/批量生成
    - 支持流式响应
    - 支持音频元数据嵌入
    - 支持多种输出格式（mp3/wav/pcm）
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ 缺少 requests 库，请先运行: pip install requests")
    sys.exit(1)


# ============== .env 自动加载 ==============

def load_env_file(env_path=None) -> None:
    """从 .env 文件加载环境变量(不覆盖已有变量,无依赖实现)"""
    if env_path is None:
        # 脚本在 scripts/, .env 在 skill 根目录
        env_path = Path(__file__).resolve().parent.parent / ".env"

    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # 不覆盖系统已有的环境变量
        if key and key not in os.environ:
            os.environ[key] = value


API_ENDPOINT = "https://api.minimax.chat/v1/t2a_v2"
DEFAULT_VOICE = "moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85"
DEFAULT_MODEL = "speech-02-hd"

VOICE_PRESETS = {
    "国语男声": "moss_audio_ce44fc67-7ce3-11f0-8de5-96e35d26fb85",
    "国语女声": "moss_audio_aaa1346a-7ce7-11f0-8e61-2e6e3c7ee85d",
    "抒情男声": "Chinese (Mandarin)_Lyrical_Voice",
    "空乘女声": "Chinese (Mandarin)_HK_Flight_Attendant",
    "粤语女声": "Cantonese_GentleLady",
    "粤语播客": "Cantonese_podacast_host_1",
}

# Edge TTS fallback voices (当 MiniMax 配额用尽或未配置时使用)
EDGE_VOICE_PRESETS = {
    "国语男声": "zh-CN-YunjianNeural",    # 新闻播报腔，最接近 moss_audio
    "国语女声": "zh-CN-XiaoxiaoNeural",   # 青年女声
    "抒情男声": "zh-CN-YunxiNeural",       # 青年男声
    "空乘女声": "zh-CN-XiaoyouNeural",    # 故事讲述
    "粤语女声": "zh-CN-YuanyuNeural",     # 粤语
    "粤语播客": "zh-CN-YuanyuNeural",
}


def call_edge_tts(text: str, voice: str, rate: str = "+0%",
                  volume: str = "+0%", fmt: str = "mp3") -> bytes:
    """Edge TTS 兜底（需要 edge-tts 库: pip install edge-tts）"""
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError(
            "Edge TTS 未安装，请运行: pip install edge-tts\n"
            "或配置 MINIMAX_API_KEY 环境变量使用 MiniMax TTS"
        )

    OUTPUT_FILE = "edge_tts_output.mp3"

    async def _generate():
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(OUTPUT_FILE)

    import asyncio
    asyncio.run(_generate())
    return Path(OUTPUT_FILE).read_bytes()


def call_tts_once(text: str, voice_id: str, api_key: str,
                  speed: float, volume: float, fmt: str = "mp3",
                  bitrate: int = 128000) -> bytes:
    """单次 TTS 调用（优先级: MiniMax → Edge TTS 兜底）"""
    # 优先 MiniMax
    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": DEFAULT_MODEL,
                "text": text,
                "stream": False,
                "voice_setting": {
                    "voice_id": voice_id,
                    "speed": speed,
                    "volume": volume,
                    "pitch": 0
                },
                "audio_setting": {
                    "format": fmt,
                    "bitrate": bitrate
                }
            }
            response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            if result.get("data"):
                return bytes.fromhex(result["data"]["audio"])
        except Exception as e:
            # MiniMax 失败，尝试 Edge TTS 兜底
            print(f"⚠️  MiniMax TTS 失败 ({e})，切换 Edge TTS 兜底...")
            edge_voice = EDGE_VOICE_PRESETS.get(
                next((k for k, v in VOICE_PRESETS.items() if v == voice_id), "国语男声"),
                "zh-CN-YunjianNeural"
            )
            rate_str = f"{'+' if speed >= 1 else ''}{int((speed - 1) * 100)}%"
            return call_edge_tts(text, edge_voice, rate=rate_str, fmt=fmt)
    else:
        # 无 API Key，直接 Edge TTS
        edge_voice = EDGE_VOICE_PRESETS.get(
            next((k for k, v in VOICE_PRESETS.items() if v == voice_id), "国语男声"),
            "zh-CN-YunjianNeural"
        )
        return call_edge_tts(text, edge_voice, fmt=fmt)


def call_tts_stream(text: str, voice_id: str, api_key: str,
                    speed: float, volume: float, fmt: str = "mp3"):
    """流式 TTS 调用（生成器）；流式失败时降级为非流式 MiniMax 或 Edge TTS"""
    if not api_key:
        # 无 API Key，直接 Edge TTS（非流式）
        edge_voice = EDGE_VOICE_PRESETS.get(
            next((k for k, v in VOICE_PRESETS.items() if v == voice_id), "国语男声"),
            "zh-CN-YunjianNeural"
        )
        yield call_edge_tts(text, edge_voice, fmt=fmt)
        return

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        payload = {
            "model": DEFAULT_MODEL,
            "text": text,
            "stream": True,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "volume": volume,
                "pitch": 0
            },
            "audio_setting": {
                "format": fmt,
                "bitrate": 128000
            }
        }

        response = requests.post(API_ENDPOINT, headers=headers, json=payload,
                                stream=True, timeout=120)
        response.raise_for_status()

        buffer = b""
        for chunk in response.iter_content(chunk_size=4096):
            buffer += chunk
            while True:
                if b"\n\n" not in buffer:
                    break
                event, buffer = buffer.split(b"\n\n", 1)
                if event.startswith(b"data: "):
                    import json
                    try:
                        data = json.loads(event[6:].decode("utf-8"))
                        if data.get("data", {}).get("audio"):
                            yield bytes.fromhex(data["data"]["audio"])
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        # 流式失败，降级为 Edge TTS
        print(f"⚠️  MiniMax 流式 TTS 失败 ({e})，Edge TTS 兜底...")
        edge_voice = EDGE_VOICE_PRESETS.get(
            next((k for k, v in VOICE_PRESETS.items() if v == voice_id), "国语男声"),
            "zh-CN-YunjianNeural"
        )
        rate_str = f"{'+' if speed >= 1 else ''}{int((speed - 1) * 100)}%"
        yield call_edge_tts(text, edge_voice, rate=rate_str, fmt=fmt)


def main():
    # 先加载 .env(若存在)
    load_env_file()

    parser = argparse.ArgumentParser(
        description="通用 MiniMax TTS 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("text", nargs="?", help="要转换的文本")
    parser.add_argument("--voice", "-v", default="国语男声", help="音色名称或 ID")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="语速 0.5-2.0")
    parser.add_argument("--volume", default=1.5, help="音量 0.0-2.0")
    parser.add_argument("--format", "-f", default="mp3", choices=["mp3", "wav", "pcm"], help="音频格式")
    parser.add_argument("--bitrate", type=int, default=128000, help="比特率")
    parser.add_argument("--stream", action="store_true", help="流式响应")
    parser.add_argument("--batch", help="批量模式：读取文件，每行一条")
    parser.add_argument("--output-dir", default="./output", help="批量模式输出目录")
    parser.add_argument("--api-key", default=None, help="API Key（默认从环境变量读取）")

    args = parser.parse_args()

    # API Key
    api_key = args.api_key or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("❌ 未设置 API Key")
        print("   设置环境变量: export MINIMAX_API_KEY=your_key")
        print("   或使用 --api-key 参数")
        sys.exit(1)

    # 音色解析
    voice_id = VOICE_PRESETS.get(args.voice, args.voice)

    # 批量模式
    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"❌ 批量文件不存在: {batch_path}")
            sys.exit(1)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        lines = [l.strip() for l in batch_path.read_text(encoding="utf-8").split("\n") if l.strip()]
        print(f"📋 批量生成 {len(lines)} 条")
        print(f"📁 输出目录: {output_dir}")

        for i, line in enumerate(lines, 1):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"audio_{i:03d}_{timestamp}.{args.format}"
            print(f"🎙️  [{i}/{len(lines)}] {line[:30]}{'...' if len(line) > 30 else ''}")

            try:
                audio = call_tts_once(line, voice_id, api_key,
                                      args.speed, args.volume, args.format, args.bitrate)
                output_path.write_bytes(audio)
                print(f"   ✅ {output_path.name} ({len(audio)/1024:.1f} KB)")
            except Exception as e:
                print(f"   ❌ 失败: {e}")

        return

    # 单条模式
    if not args.text:
        parser.print_help()
        sys.exit(1)

    output_path = args.output or f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"

    print(f"🎤 音色: {args.voice}")
    print(f"📝 文本: {args.text[:50]}{'...' if len(args.text) > 50 else ''}")
    print(f"💾 输出: {output_path}")

    if args.stream:
        print("🌊 流式生成...")
        chunks = []
        total_size = 0
        for chunk in call_tts_stream(args.text, voice_id, api_key,
                                     args.speed, args.volume, args.format):
            chunks.append(chunk)
            total_size += len(chunk)
            print(f"   📦 已接收: {total_size/1024:.1f} KB", end="\r")
        print()

        with open(output_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
    else:
        audio = call_tts_once(args.text, voice_id, api_key,
                             args.speed, args.volume, args.format, args.bitrate)
        Path(output_path).write_bytes(audio)

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"✅ 完成: {output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
