# tool_context.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolContext:
    """
    Everything a tool needs to know about the current task / environment.
    """
    task_id: str
    work_dir: str
    runtime_base_url: Optional[str] = None      # direct fake-runtime or real runtime HTTP
    execution_worker_url: Optional[str] = None  # when set → Brain mode (go through worker)

    @property
    def use_worker(self) -> bool:
        """True when we must talk to the execution worker instead of local FS."""
        return bool(self.execution_worker_url)