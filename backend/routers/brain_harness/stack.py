# stack.py
"""
Stack-specific guidance that is injected into the system prompt.
Helps the model avoid cross-stack mistakes.
"""

STACK_HINTS = {
    "fastapi": """
You are working on a FastAPI (Python) project.
- Main entry point is usually main.py or app/main.py
- Use SQLModel / SQLAlchemy for database models
- Prefer Pydantic models for request/response schemas
- Do NOT create Next.js files (page.tsx, layout.tsx, etc.)
- Do NOT assume a frontend framework unless the user asks for it
""".strip(),

    "nextjs": """
You are working on a Next.js (React) project.
- App Router is preferred (app/ directory)
- page.tsx and layout.tsx are the main files
- Use TypeScript
- Do NOT create Python files (main.py, requirements.txt) unless explicitly asked
""".strip(),

    "node": """
You are working on a plain Node.js project.
- Entry point is usually index.js or src/index.js
- Prefer TypeScript when possible
- package.json is the source of truth for dependencies
""".strip(),

    "go": """
You are working on a Go project.
- Main package is usually in main.go or cmd/
- Use go.mod for dependencies
- Do NOT create Python or JavaScript frontend files unless asked
""".strip(),

    "generic": """
No specific stack detected.
Be careful not to assume a framework.
Only create files that match the languages and tools already present in the workspace.
""".strip(),
}


def get_stack_hint(stack: str = "generic") -> str:
    """Return the guidance text for the given stack."""
    return STACK_HINTS.get(stack.lower(), STACK_HINTS["generic"])





