"""
Well-known declarations for Durga.

Serves agents.txt, agents.json, ai.txt, ai.json under RFC 8615 /.well-known/.
Durga is the first reference implementation that declares itself per the
agents.txt and ai.txt standards (https://github.com/kaylacar/agents-txt,
https://github.com/kaylacar/ai-txt).

Behavior:
  * If DURGA_AGENTS_TXT_PATH / DURGA_AI_TXT_PATH point at a readable file,
    that file's contents are served verbatim.
  * Otherwise the bundled defaults at src/khoj/static/well-known/ are served,
    with Generated-At injected for the .txt variants.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import Response

logger = logging.getLogger(__name__)

well_known_router = APIRouter()

_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
    "well-known",
)

_TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"
_JSON_CONTENT_TYPE = "application/json; charset=utf-8"


def _now_iso() -> str:
    # ISO 8601 in UTC with millisecond precision; matches spec examples.
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _read_override(env_var: str) -> Optional[str]:
    path = os.environ.get(env_var)
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        logger.warning("Could not read %s override at %s: %s", env_var, path, exc)
        return None


def _read_default(filename: str) -> str:
    path = os.path.join(_STATIC_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        logger.error("Default well-known asset missing: %s (%s)", path, exc)
        # Fall back to a minimal but spec-valid stub so the route still answers.
        return "# agents.txt\nSpec-Version: 1.0\n"


def _inject_generated_at_text(body: str) -> str:
    """Insert or refresh the Generated-At header in a text declaration."""
    stamp = _now_iso()
    lines = body.splitlines()
    out = []
    seen_spec_version = False
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("generated-at:"):
            out.append(f"Generated-At: {stamp}")
            replaced = True
            continue
        out.append(line)
        if not seen_spec_version and stripped.lower().startswith("spec-version:"):
            seen_spec_version = True
            if not replaced:
                out.append(f"Generated-At: {stamp}")
                replaced = True
    text = "\n".join(out)
    if not body.endswith("\n"):
        text += "\n"
    elif not text.endswith("\n"):
        text += "\n"
    return text


def _inject_generated_at_json(body: str) -> str:
    """Insert or refresh generatedAt on a JSON declaration. Best-effort."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body
    if isinstance(data, dict):
        data["generatedAt"] = _now_iso()
    return json.dumps(data, indent=2) + "\n"


def _serve_text(env_var: str, default_filename: str) -> Response:
    body = _read_override(env_var)
    if body is None:
        body = _read_default(default_filename)
    body = _inject_generated_at_text(body)
    return Response(content=body, media_type=_TEXT_CONTENT_TYPE)


def _serve_json(env_var: str, default_filename: str) -> Response:
    body = _read_override(env_var)
    if body is None:
        body = _read_default(default_filename)
    body = _inject_generated_at_json(body)
    return Response(content=body, media_type=_JSON_CONTENT_TYPE)


@well_known_router.get("/agents.txt", include_in_schema=False)
async def agents_txt() -> Response:
    return _serve_text("DURGA_AGENTS_TXT_PATH", "agents.txt")


@well_known_router.get("/agents.json", include_in_schema=False)
async def agents_json() -> Response:
    return _serve_json("DURGA_AGENTS_TXT_PATH", "agents.json")


@well_known_router.get("/ai.txt", include_in_schema=False)
async def ai_txt() -> Response:
    return _serve_text("DURGA_AI_TXT_PATH", "ai.txt")


@well_known_router.get("/ai.json", include_in_schema=False)
async def ai_json() -> Response:
    return _serve_json("DURGA_AI_TXT_PATH", "ai.json")
