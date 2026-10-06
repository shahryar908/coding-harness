# loop.py
import json
import os
import time
import uuid

import openai
from context import COMPACT_AFTER, build_system_prompt, compact_messages
from dotenv import load_dotenv
from execute import execute_tool
from tool_context import ToolContext
from tools import OPENAI_TOOLS
from trust import wrap_user_request

load_dotenv("../../.env")

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)

MAX_STEPS = 40
TIMEOUT_SEC = 600


def wrap_tool_result(tool_call_id: str, content: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def run_agent(
    user_prompt: str,
    stack: str = "fastapi",
    execution_worker_url: str | None = None,
):
    system_prompt = build_system_prompt(stack=stack)
    wrapped_prompt = wrap_user_request(user_prompt)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": wrapped_prompt},
    ]

    original_goal = user_prompt
    start = time.time()

    # Context for this run (standalone or worker mode)
    ctx = ToolContext(
        task_id=str(uuid.uuid4()),
        work_dir="./workspace/repo",
        execution_worker_url=execution_worker_url,
    )

    for step in range(1, MAX_STEPS + 1):
        if time.time() - start > TIMEOUT_SEC:
            print("\nTimeout reached. Stopping.")
            break

        if len(messages) >= COMPACT_AFTER:
            messages = compact_messages(messages, original_goal)

        print(f"\n=== Step {step} ===")

        # ── Call the model with recovery for hallucinated tools ──
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=OPENAI_TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            error_text = str(e)
            print(f"API error: {error_text[:300]}")

            if (
                "not in request.tools" in error_text.lower()
                or "tool call validation failed" in error_text.lower()
            ):
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You tried to call a tool that does not exist. "
                            "You may ONLY use these tools: shell, read_file, write_file, finish. "
                            "Never invent new tool names. "
                            "Please continue the task using only those tools. "
                            "When you are done, call the finish tool."
                        ),
                    }
                )
                continue
            else:
                raise

        # From here, response is guaranteed to exist
        msg = response.choices[0].message
        messages.append(msg)

        # No tool calls → model just replied with text
        if not msg.tool_calls:
            print("Model replied without tools:")
            print(msg.content)
            break

        finished = False
        known_tools = {"shell", "read_file", "write_file", "finish"}

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            print(f"→ calling {name}({args})")

            if name not in known_tools:
                result = (
                    f"Error: unknown tool '{name}'. "
                    f"Available tools: {', '.join(sorted(known_tools))}"
                )
                print(f"← {result}")
                messages.append(wrap_tool_result(tc.id, result))
                continue

            # Go through the execution layer (local or worker)
            result = execute_tool(ctx, name, args)

            preview = result if len(result) <= 400 else result[:400] + "..."
            print(f"← {preview}")

            messages.append(wrap_tool_result(tc.id, result))

            if name == "finish":
                finished = True

        if finished:
            print("\nAgent called finish. Stopping.")
            break
    else:
        print("\nMax steps reached.")

    return messages