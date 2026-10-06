# trust.py
"""
Trust & guardrails layer.
Wraps untrusted content and blocks dangerous tool calls.
"""

import re

# ──────────────────────────────────────────────────────────────
# 1. Wrappers – clearly mark untrusted content
# ──────────────────────────────────────────────────────────────

def wrap_user_request(text: str) -> str:
    return f"<user_request>\n{text}\n</user_request>"


def wrap_tool_result(tool_name: str, content: str) -> str:
    return f"<tool_result name=\"{tool_name}\">\n{content}\n</tool_result>"


def wrap_session_context(text: str) -> str:
    return f"<session_context>\n{text}\n</session_context>"


def wrap_recalled_memory(text: str) -> str:
    return f"<recalled_memory>\n{text}\n</recalled_memory>"


def wrap_repo_listing(text: str) -> str:
    return f"<repo_listing>\n{text}\n</repo_listing>"


# ──────────────────────────────────────────────────────────────
# 2. Shell refuse rules
# ──────────────────────────────────────────────────────────────

# Patterns that look like secret exfiltration or dangerous commands
DANGEROUS_SHELL_PATTERNS = [
    r"echo\s+\$\w*API_KEY",
    r"echo\s+\$\w*SECRET",
    r"echo\s+\$\w*TOKEN",
    r"printenv",
    r"env\s*\|",
    r"curl\s+.*\$\w+",
    r"wget\s+.*\$\w+",
    r"cat\s+.*\.env",
    r"type\s+.*\.env",          # Windows
    r"Get-Content\s+.*\.env",   # PowerShell
    r"rm\s+-rf\s+/",
    r"del\s+/s\s+/q\s+C:\\",
]


def is_dangerous_shell(command: str) -> str | None:
    """
    Return a reason string if the command should be refused,
    otherwise return None.
    """
    lowered = command.lower().strip()
    for pattern in DANGEROUS_SHELL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return f"Refused: command matches dangerous pattern → {pattern}"
    return None


# ──────────────────────────────────────────────────────────────
# 3. Path guards
# ──────────────────────────────────────────────────────────────

FORBIDDEN_PATH_PARTS = [
    "..",
    "node_modules",
    ".next",
    ".git/objects",
    "venv",
    ".venv",
    "__pycache__",
]


def is_forbidden_path(path: str) -> str | None:
    """
    Return a reason if the path is not allowed.
    """
    normalized = path.replace("\\", "/").lower()
    for part in FORBIDDEN_PATH_PARTS:
        if part in normalized:
            return f"Refused: path contains forbidden part '{part}'"
    return None


# ──────────────────────────────────────────────────────────────
# 4. Memory filter (for later save_memory tool)
# ──────────────────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"disregard\s+(previous|all)\s+instructions",
    r"you\s+are\s+now",
    r"system\s+prompt",
    r"new\s+instructions",
]


def is_injection_attempt(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in INJECTION_PATTERNS)