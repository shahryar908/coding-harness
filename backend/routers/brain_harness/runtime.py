from pathlib import Path
import subprocess


WORKSPACE=Path("./workspace/repo").resolve()




class FakeRuntime:
    def __init__(self, root: Path=WORKSPACE):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, path: Path) -> Path:
        p=(self.root/path).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError(f"Path escapes workspace: {path}")
        return p

    def list_dir(self,path:str=".")->str:
        p=self._safe(path)
        if not p.is_dir():
            return f"Error: {path} is not a directory"
        entries=[]
        for item in sorted(p.iterdir()):
            kind="dir" if item.is_dir() else "file"
            entries.append(f"{kind}: {item.relative_to(self.root)}")
        return "\n".join(entries) or "(empty)"

    def read_file(self,path:str)->str:
        p=self._safe(path)
        if not p.is_file():
            raise ValueError("file not exist or is not a file")
        return p.read_text(encoding="utf-8", errors="replace")


    def write_file(self,path:str,content:str)->str:
        p=self._safe(path)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content,encoding="utf-8")
        return f"Wrote {len(content)} bytes to {path}utf-8"
    def exec(self,command:str,timeout:int=30)->str:
        try:
            result=subprocess.run(
                command,
                cwd=self.root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,

            )
            out=result.stdout
            if result.stderr:
                out += "\nSTDERR:\n" + result.stderr
            if result.returncode != 0:
                out += f"\nExit code: {result.returncode}"
            return out or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: command timed out"
        except Exception as e:
            return f"Error: {e}"



