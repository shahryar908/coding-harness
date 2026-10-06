# sandbox_intent.py
"""
Decide if a user prompt needs a real sandbox / coding agent
or can be answered with a simple direct reply.
"""

import json
import os

import openai
from dotenv import load_dotenv

load_dotenv("../../.env")

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)


def plan_brain_execution(prompt: str) -> dict:
    """
    Returns a small JSON plan:
    {
      "needsSandbox": bool,
      "directReply": str | null,
      "reasoning": str
    }
    """
    system = """You are a router. Decide if the user message requires a coding sandbox.

Reply with ONLY valid JSON in this exact shape:
{
  "needsSandbox": true or false,
  "directReply": "short friendly reply if needsSandbox is false, otherwise null",
  "reasoning": "one short sentence"
}

Rules:
- needsSandbox = false for greetings, thanks, simple questions that need no code or files
- needsSandbox = true for anything that involves writing code, creating files, fixing bugs, installing packages, etc.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()

        # Remove markdown fences if the model adds them
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()

        plan = json.loads(text)

        # Basic validation / defaults
        return {
            "needsSandbox": bool(plan.get("needsSandbox", True)),
            "directReply": plan.get("directReply"),
            "reasoning": plan.get("reasoning", ""),
        }
    except Exception as e:
        # Safe fallback: assume it needs a sandbox
        return {
            "needsSandbox": True,
            "directReply": None,
            "reasoning": f"Fallback because router failed: {e}",
        }