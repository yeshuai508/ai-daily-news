"""Generate podcast-style audio from daily digest using Podcastfy + Edge TTS."""

import os
import re
import shutil
import subprocess

from dotenv import load_dotenv

load_dotenv()

from podcastfy.client import generate_podcast

CONVERSATION_CONFIG = {
    "word_count": 800,
    "output_language": "Chinese",
    "conversation_style": ["engaging", "informative", "concise"],
    "roles_person1": "主播",
    "roles_person2": "评论员",
    "creativity": 0.4,
    "text_to_speech": {
        "model": "edge",
        "default_voices": {
            "question": "zh-CN-YunxiNeural",
            "answer": "zh-CN-XiaoxiaoNeural",
        },
    },
}


def generate_podcast_audio(digest_md, date_str):
    """Generate a podcast MP3 from digest markdown. Returns output file path."""
    cleaned = _clean_for_tts(digest_md)

    # Set up LiteLLM env for OpenAI-compatible endpoint
    llm_api_key = os.getenv("LLM_API_KEY", "")
    llm_base_url = os.getenv("LLM_BASE_URL", "")
    llm_model = os.getenv("LLM_MODEL", "moonshot-v1-32k")

    # LiteLLM needs OPENAI_API_BASE for custom endpoints
    if llm_base_url:
        os.environ["OPENAI_API_BASE"] = llm_base_url
    if llm_api_key:
        os.environ["PODCAST_LLM_KEY"] = llm_api_key

    output_file = generate_podcast(
        text=cleaned,
        tts_model="edge",
        conversation_config=CONVERSATION_CONFIG,
        llm_model_name=f"openai/{llm_model}",
        api_key_label="PODCAST_LLM_KEY",
    )

    os.makedirs("data", exist_ok=True)
    dest = f"data/audio-{date_str}.mp3"
    shutil.move(output_file, dest)

    # Compress if over 2MB (WeChat voice material limit)
    if os.path.getsize(dest) > 2 * 1024 * 1024:
        dest = _compress_audio(dest)

    return dest


def _clean_for_tts(markdown_text):
    """Strip markdown formatting, links, and emoji for cleaner TTS input."""
    text = markdown_text
    # Remove links but keep link text
    text = re.sub(r'\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    # Remove markdown headings markers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove emoji (common Unicode ranges)
    text = re.sub(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF'
        r'\U0000FE00-\U0000FE0F\U0000200D]+',
        '', text
    )
    # Remove list markers
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _compress_audio(audio_path, max_size_mb=2):
    """Compress MP3 with ffmpeg to fit under size limit."""
    compressed = audio_path.replace('.mp3', '_compressed.mp3')
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", audio_path,
            "-b:a", "48k", "-ar", "24000", "-ac", "1",
            compressed,
        ],
        check=True,
        capture_output=True,
    )
    os.replace(compressed, audio_path)
    return audio_path
