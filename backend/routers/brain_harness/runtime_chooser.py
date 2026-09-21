# runtime_chooser.py
"""
Choose the most appropriate runtime / stack for a user prompt.
"""

import json
import os
import re
from dotenv import load_dotenv
import openai

load_dotenv("../../.env")

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)

VALID_STACKS = {"nextjs", "node", "go", "rust", "python", "fastapi", "generic"}


def choose_stack_runtime(prompt: str) -> str:
    """
    Returns one of: nextjs | node | go | rust | python | fastapi | generic
    """
    # 1. Fast heuristic (no LLM call)
    heuristic = _heuristic_stack(prompt)
    if heuristic:
        return heuristic

    # 2. Ask the model
    system = """You are a stack classifier.
Given a user coding request, reply with ONLY one word from this list:
nextjs, node, go, rust, python, fastapi, generic

Rules:
- FastAPI / SQLModel / pydantic / bcrypt / jwt → fastapi
- Next.js / React / page.tsx / app router → nextjs
- Express / plain Node → node
- Go / golang → go
- Rust → rust
- General Python (not FastAPI) → python
- Unclear → generic
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=20,
        )
        text = response.choices[0].message.content.strip().lower()
        # Clean possible punctuation
        text = re.sub(r"[^a-z]", "", text)

        if text in VALID_STACKS:
            return text
        return "generic"
    except Exception:
        return "generic"


def _heuristic_stack(prompt: str) -> str | None:
    """Very cheap keyword matching before calling the LLM."""
    p = prompt.lower()

    if any(k in p for k in ["fastapi", "sqlmodel", "pydantic", "uvicorn"]):
        return "fastapi"
    if any(k in p for k in ["next.js", "nextjs", "page.tsx", "app router", "react"]):
        return "nextjs"
    if any(k in p for k in ["express", "node.js", "nodejs"]):
        return "node"
    if any(k in p for k in ["golang", " go ", "gin ", "fiber"]):
        return "go"
    if "rust" in p or "cargo" in p:
        return "rust"
    if "django" in p or "flask" in p:
        return "python"

    return None