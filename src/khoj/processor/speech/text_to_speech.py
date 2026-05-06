"""
Text-to-speech for Durga.

Provider precedence:
1. ElevenLabs — if ELEVEN_LABS_API_KEY is set (preserves upstream behavior, premium).
2. Edge TTS — free Microsoft neural voices, no API key. Default for Durga.

Returns an object with `.iter_content(chunk_size=N)` so the existing
`StreamingResponse(...)` call site in `routers/api_chat.py` works unchanged.
"""

import asyncio
import logging
import os
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)

# ElevenLabs (kept as optional premium provider)
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", None)
ELEVEN_DEFAULT_VOICE_ID = "RPEIZnKMqlQiZyZd1Dae"
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Edge TTS — free Microsoft neural voices.
# Catalog: https://github.com/rany2/edge-tts (run `edge-tts --list-voices`).
EDGE_TTS_DEFAULT_VOICE = os.getenv("DURGA_TTS_VOICE", "en-US-AriaNeural")

markdown_renderer = MarkdownIt()


class TextToSpeechError(Exception):
    """Exception raised when text-to-speech generation fails."""


class _BytesStream:
    """Mimics requests.Response.iter_content for in-memory audio bytes."""

    def __init__(self, audio_bytes: bytes):
        self._buffer = BytesIO(audio_bytes)
        self.ok = True
        self.status_code = 200

    def iter_content(self, chunk_size: int = 1024):
        while True:
            chunk = self._buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk


def is_eleven_labs_enabled() -> bool:
    return ELEVEN_LABS_API_KEY is not None


def is_edge_tts_enabled() -> bool:
    try:
        import edge_tts  # noqa: F401

        return True
    except ImportError:
        return False


def is_text_to_speech_enabled() -> bool:
    return is_eleven_labs_enabled() or is_edge_tts_enabled()


def _markdown_to_plain(md_text: str) -> str:
    html = markdown_renderer.render(md_text)
    return "".join(BeautifulSoup(html, features="lxml").findAll(text=True))


def _looks_like_edge_voice(voice_id: str | None) -> bool:
    """Edge voice names look like 'en-US-AriaNeural'. ElevenLabs IDs are alphanumeric."""
    return bool(voice_id) and "-" in voice_id and "Neural" in voice_id


async def _edge_tts_async(text: str, voice: str) -> bytes:
    import edge_tts

    chunks: list[bytes] = []
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def _generate_edge_tts(text: str, voice: str) -> _BytesStream:
    """Run edge-tts synthesis. Safe to call from sync or async contexts."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Called from inside an async stack (FastAPI). Run on a separate thread loop.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                audio = ex.submit(asyncio.run, _edge_tts_async(text, voice)).result()
        else:
            audio = loop.run_until_complete(_edge_tts_async(text, voice))
    except RuntimeError:
        # No current loop.
        audio = asyncio.run(_edge_tts_async(text, voice))
    return _BytesStream(audio)


def _generate_eleven_labs(text: str, voice_id: str):
    tts_url = f"{ELEVEN_API_URL}/{voice_id}/stream"
    headers = {"Accept": "application/json", "xi-api-key": ELEVEN_LABS_API_KEY}
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    if response.ok:
        return response
    raise TextToSpeechError(f"ElevenLabs TTS failed: {response.text}")


def generate_text_to_speech(
    text_to_speak: str,
    voice_id: str | None = None,
):
    """
    Generate audio for the given text. Returns a streaming-compatible object
    with `.iter_content(chunk_size=N)`. Picks the provider based on what's
    configured: ElevenLabs if its API key is set, else Edge TTS.

    `voice_id` semantics: an Edge voice name like `en-US-AriaNeural` routes
    Edge TTS regardless of the default. ElevenLabs voice IDs route ElevenLabs.
    """
    text = _markdown_to_plain(text_to_speak)

    # Explicit per-request routing via voice_id shape.
    if _looks_like_edge_voice(voice_id):
        if not is_edge_tts_enabled():
            raise TextToSpeechError(
                "Edge TTS voice requested but `edge-tts` package is not installed."
            )
        return _generate_edge_tts(text, voice_id)

    # No edge override: prefer ElevenLabs if configured, else Edge TTS as default.
    if is_eleven_labs_enabled():
        return _generate_eleven_labs(text, voice_id or ELEVEN_DEFAULT_VOICE_ID)

    if is_edge_tts_enabled():
        return _generate_edge_tts(text, EDGE_TTS_DEFAULT_VOICE)

    raise TextToSpeechError(
        "No TTS provider available. Install `edge-tts` (free) or set ELEVEN_LABS_API_KEY."
    )
