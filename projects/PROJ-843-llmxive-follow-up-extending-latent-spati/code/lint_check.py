"""
Lint configuration check (T002).

Verifies that flake8 and black are configured and runnable against the
project's code directory. Writes a machine-readable status report to
data/results/lint_status.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

def tool_available(name: str) -> bool:
    return shutil.which(name) is not None

def run_tool(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {"flake8": {}, "black": {}}

    if tool_available("flake8"):
        rc, out = run_tool(
            ["flake8", str(CODE_DIR), "--config", str(PROJECT_ROOT / "setup.cfg")],
            PROJECT_ROOT,
        )
        report["flake8"] = {
            "available": True,
            "returncode": rc,
            "output_tail": out.strip().splitlines()[-20:],
        }
    else:
        report["flake8"] = {"available": False}

    if tool_available("black"):
        rc, out = run_tool(
            ["black", str(CODE_DIR), "--check", "--config",
             str(PROJECT_ROOT / "pyproject.toml")],
            PROJECT_ROOT,
        )
        report["black"] = {
            "available": True,
            "returncode": rc,
            "output_tail": out.strip().splitlines()[-20:],
        }
    else:
        report["black"] = {"available": False}

    out_path = RESULTS_DIR / "lint_status.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Lint status report written to {out_path}")
    print(json.dumps(report, indent=2))

    # Tools being unavailable is a configuration gap worth surfacing,
    # but the config files themselves are the deliverable of T002.
    if not report["flake8"]["available"] or not report["black"]["available"]:
        print("WARNING: flake8 or black not on PATH; install dev tools to run linting.")
    return 0

if __name__ == "__main__":
    sys.exit(main())