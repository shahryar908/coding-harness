# execute.py
"""
Tool execution layer.
Splits "what the tool is" from "where it actually runs".
"""

import httpx
from runtime import FakeRuntime
from tool_context import ToolContext
from trust import is_dangerous_shell, is_forbidden_path, wrap_tool_result

# Local fallback runtime (used when no worker is configured)
_local_runtime = FakeRuntime()


def execute_tool(ctx: ToolContext, name: str, args: dict) -> str:
    """
    Main entry point used by the harness loop.
    1. Validate / guard
    2. Delegate to the correct backend
    3. Always return a wrapped string
    """
    # ── 1. Guards (same as before) ──────────────────────────────
    if name == "shell":
        reason = is_dangerous_shell(args.get("command", ""))
        if reason:
            return wrap_tool_result(name, reason)

    if name in ("read_file", "write_file"):
        reason = is_forbidden_path(args.get("path", ""))
        if reason:
            return wrap_tool_result(name, reason)

    # ── 2. Choose backend ───────────────────────────────────────
    if ctx.use_worker:
        raw = _execute_via_worker(ctx, name, args)
    else:
        raw = _execute_local(ctx, name, args)

    return wrap_tool_result(name, raw)


# ──────────────────────────────────────────────────────────────
# Backend A – local (standalone / fake runtime)
# ──────────────────────────────────────────────────────────────
def _execute_local(ctx: ToolContext, name: str, args: dict) -> str:
    if name == "shell":
        return _local_runtime.exec(args["command"])
    elif name == "read_file":
        return _local_runtime.read_file(args["path"])
    elif name == "write_file":
        return _local_runtime.write_file(args["path"], args["content"])
    elif name == "finish":
        return f"FINISHED: {args.get('summary', '')}"
    else:
        return f"Error: unknown tool '{name}'"


# ──────────────────────────────────────────────────────────────
# Backend B – via execution worker (Brain mode)
# ──────────────────────────────────────────────────────────────
def _execute_via_worker(ctx: ToolContext, name: str, args: dict) -> str:
    """
    POST to the worker. The worker is the only process allowed
    to talk to the real runtime / VM.
    """
    url = f"{ctx.execution_worker_url.rstrip('/')}/api/v1/tasks/{ctx.task_id}/tools"

    payload = {
        "tool": name,
        "args": args,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Worker is expected to return {"result": "..."} 
            return data.get("result", str(data))
    except Exception as e:
        return f"Error talking to execution worker: {e}"