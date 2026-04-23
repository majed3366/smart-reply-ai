from __future__ import annotations

import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
MEMORY_MESSAGE_LIMIT = int(os.environ.get("MEMORY_MESSAGE_LIMIT", "24"))
