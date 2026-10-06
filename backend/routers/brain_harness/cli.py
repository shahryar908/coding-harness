# cli.py
import argparse

from loop import run_agent
from runtime_chooser import choose_stack_runtime
from sandbox_intent import plan_brain_execution


def main():
    parser = argparse.ArgumentParser(description="Brain-style coding agent")
    parser.add_argument("prompt", nargs="+", help="The task for the agent")
    parser.add_argument(
        "--stack",
        default=None,
        choices=["fastapi", "nextjs", "node", "go", "rust", "python", "generic"],
        help="Force a stack (skips auto detection)",
    )
    parser.add_argument(
        "--worker",
        default=None,
        help="Execution worker URL (e.g. http://localhost:8100)",
    )
    args = parser.parse_args()

    prompt = " ".join(args.prompt)
    print(f"User prompt: {prompt}\n")

    # ──────────────────────────────────────────────
    # 1. Pre-flight: does this even need a sandbox?
    # ──────────────────────────────────────────────
    plan = plan_brain_execution(prompt)
    print(f"[router] needsSandbox = {plan['needsSandbox']}")
    print(f"[router] reasoning    = {plan['reasoning']}")

    if not plan["needsSandbox"]:
        # Direct reply – no agent loop, no tools, no cost
        reply = plan.get("directReply") or "Hello! How can I help you today?"
        print(f"\n[direct reply]\n{reply}")
        return

    # ──────────────────────────────────────────────
    # 2. Choose stack (unless user forced one)
    # ──────────────────────────────────────────────
    stack = args.stack or choose_stack_runtime(prompt)
    print(f"[chooser] selected stack = {stack}\n")

    # ──────────────────────────────────────────────
    # 3. Run the full agent
    # ──────────────────────────────────────────────
    run_agent(
        user_prompt=prompt,
        stack=stack,
        execution_worker_url=args.worker,
    )


if __name__ == "__main__":
    main()