"""
Template Engine safety filter.

Validates rendered output for dangerous shell patterns before
returning scripts to the client. This is a hard safety gate –
no script passes without this validation.
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import re
import subprocess
from typing import Any

import bashlex
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider

logger = logging.getLogger(__name__)

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"rm\s+-[rRf]{1,3}\s+/", "Recursive delete of filesystem path"),
    (r"rm\s+-[rRf]{1,3}\s+\$HOME", "Recursive delete of home directory"),
    (r"rm\s+-[rRf]{1,3}\s+~", "Recursive delete of home directory (tilde)"),
    (r"mkfs\.", "Filesystem format command"),
    (r"format\s+[A-Za-z]:", "Windows drive format command"),
    (r":\(\){\s*\|[^\)]*\s*};.*&*", "Fork bomb pattern"),
    (r"dd\s+if=", "Raw disk write command"),
    (r">\s*/dev/sd[a-z]", "Direct disk write"),
    (r"shutdown\s+(/[s/r|-h|-r)", "System shutdown/reboot"),
    (r"DROP\s+DATABASE", "SQL database destruction"),
    (r"DROP\s+TABLE", "SQL table destruction"),
    (r"TRUNCATE\s+TABLE", "SQL table truncation"),
    (
        r"curl\s+.*?\|\s*(?:ba)?sh",
        "Curl-pipe-to-shell (untrusted exec)",
    ),
    (
        r"wget\s+(?:-[^\s|;&]+?\s+)*?https?://(?!(?:micro\.mamba\.pm|astral\.sh)/)\S+\s*\|\s*(?:ba)?sh",
        "Wget-pipe-to-shell (untrusted exec)",
    ),
    (
        r"wget\s+[^;\|&]*?(-O\s+\S+).*(?:&&|;|\||[\r\n])\s*(?:ba)?sh\s+\1",
        "Wget download-and-execute pattern (sequential/chained)",
    ),
    (
        r"wget\s+[^;\|&]*?(-O\s+(\S+)).*(?:&&|;|\||[\r\n])\s*(?:ba)?sh\s+\2",
        "Wget download-and-execute pattern (explicit target)",
    ),
    (
        r"curl\s+[^;\|&]*?(-o|--output)\s+(\S+).*(?:&&|;|\||[\r\n])\s*(?:ba)?sh\s+\2",
        "Curl download-and-execute pattern",
    ),
    (
        r"curl\s+[^;\|&]*?(-O|--remote-name)\s+.*(?:&&|;|\||[\r\n])\s*(?:ba)?sh\s+",
        "Curl remote-name download-and-execute pattern",
    ),
    (
        r"curl\s+[^;\|&]*?>\s*(\S+).*(?:&&|;|\||[\r\n])\s*(?:ba)?sh\s+\1",
        "Curl redirect download-and-execute pattern",
    ),
    (
        r"(?:iex|Invoke-Expression)\s*\|\s*(?:\?s*(?:iwr|Invoke-WebRequest|Invoke-RestMethod|irm|curl|wget)\s+(?!https?://astral\.sh/)\S+.*"
        r"|Invoke-Expression\s+.*?(?:iex|Invoke-Expression)",
        "PowerShell malicious download cradle",
    ),
    (
        r"(?:iwr|Invoke-WebRequest|Invoke-RestMethod|irm|curl|wget)\s+(?!https?://astral\.sh/)\S+.*\s*\|\s*(?:iex|Invoke-Expression)",
        "PowerShell piped download cradle",
    ),
    (
        r"(?:iex|Invoke-Expression)\s*\|\s*(?:\?s*(?:\(?\:New-Object\)\s+Net\.WebClient\)?)\.(?:DownloadString|DownloadFile))\s*\(",
        "PowerShell .Net WebClient download cradle",
    ),
    (r"eval\s+\$\(", "Eval of subshell output"),
    (r"base64\s+--decode\s*\|\s*. *sh", "Base64 decode pipe to shell"),
]

_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE | re.DOTALL), desc)
    for pattern, desc in FORBIDDEN_PATTERNS
]


class AISafetyVerdict(BaseModel):
    is_safe: bool
    reason: str


class SafetyViolationError(Exception):
    """Raised when rendered template output contains a forbidden pattern."""

    def __init__(self, pattern: str, description: str, context: str = "") -> None:
        self.pattern = pattern
        self.description = description
        self.context = context
        super().__init__(
            f"Safety violation detected: {description} (pattern: {pattern!r})"
        )


def _validate_bash_ast(content: str, template_name: str = "") -> None:
    """Parse and validate shell scripts using bashlex AST parsing."""
    try:
        nodes = bashlex.parse(content)
    except Exception as e:
        logger.warning(
            f"Bash AST parsing skipped for {template_name} due to parser error/limitation: {str(e)}"
        )
        return

    violations = []