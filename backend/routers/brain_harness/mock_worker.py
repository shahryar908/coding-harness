# mock_worker.py
"""
Tiny stand-in for the real execution worker.
Run it with:  uvicorn mock_worker:app --port 8100
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
from runtime import FakeRuntime

app = FastAPI()
runtime = FakeRuntime()


class ToolRequest(BaseModel):
    tool: str
    args: dict[str, Any]


@app.post("/api/v1/tasks/{task_id}/tools")
def run_tool(task_id: str, body: ToolRequest):
    name = body.tool
    args = body.args

    if name == "shell":
        result = runtime.exec(args.get("command", ""))
    elif name == "read_file":
        result = runtime.read_file(args.get("path", ""))
    elif name == "write_file":
        result = runtime.write_file(args.get("path", ""), args.get("content", ""))
    elif name == "finish":
        result = f"FINISHED: {args.get('summary', '')}"
    else:
        result = f"Error: unknown tool '{name}'"

    return {"result": result}