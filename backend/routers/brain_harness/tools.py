# tools.py
import json
from runtime import FakeRuntime
from trust import is_dangerous_shell, is_forbidden_path, wrap_tool_result

runtime = FakeRuntime()

# ──────────────────────────────────────────────────────────────
# OpenAI / Groq tool schemas
# ──────────────────────────────────────────────────────────────
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell",
            "description": "Run a shell command inside the workspace. Returns stdout + stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path of the file to read"
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (or overwrite) a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path of the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "The full content to write into the file"
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Call this when the task is complete. Provide a short summary of what was done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A short summary of what was accomplished"
                    }
                },
                "required": ["summary"],
            },
        },
    },
]


# ──────────────────────────────────────────────────────────────
# Local implementations with trust guards
# ──────────────────────────────────────────────────────────────
def run_tool(name: str, args: dict) -> str:
    """Execute a tool by name and return a string result (already wrapped)."""

    if name == "shell":
        command = args.get("command", "")
        reason = is_dangerous_shell(command)
        if reason:
            return wrap_tool_result(name, reason)
        raw = runtime.exec(command)
        return wrap_tool_result(name, raw)

    elif name == "read_file":
        path = args.get("path", "")
        reason = is_forbidden_path(path)
        if reason:
            return wrap_tool_result(name, reason)
        raw = runtime.read_file(path)
        return wrap_tool_result(name, raw)

    elif name == "write_file":
        path = args.get("path", "")
        reason = is_forbidden_path(path)
        if reason:
            return wrap_tool_result(name, reason)
        content = args.get("content", "")
        raw = runtime.write_file(path, content)
        return wrap_tool_result(name, raw)

    elif name == "finish":
        summary = args.get("summary", "")
        return wrap_tool_result(name, f"FINISHED: {summary}")

    else:
        return wrap_tool_result(name, f"Error: unknown tool '{name}'")