from __future__ import annotations

import asyncio
from typing import Any

from anthropic import Anthropic

from core.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _extract_text(response: Any) -> str:
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _messages_create_sync(
    *,
    system: str,
    messages: list[dict[str, str]],
) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return _extract_text(response)


async def generate_sales_reply(
    *,
    system: str,
    messages: list[dict[str, str]],
) -> str:
    return await asyncio.to_thread(
        _messages_create_sync,
        system=system,
        messages=messages,
    )
