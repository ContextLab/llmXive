"""T001b: Validate the linting/formatting configuration.

1. Parses code/pyproject.toml and asserts the deterministic settings
   required by the task (line-length = 88, target-version py310 for
   both ruff and black).
2. Ensures ruff and black are available (installing them per the task
   prerequisite if missing).
3. Runs `ruff check code/` and `black --check code/` and reports the
   results.
"""
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = Path(__file__).resolve().parent / "pyproject.toml"
CODE_DIR = Path(__file__).resolve().parent


def validate_config() -> None:
    with open(PYPROJECT, "rb") as f:
        config = tomllib.load(f)

    ruff = config["tool"]["ruff"]
    black = config["tool"]["black"]

    assert ruff["line-length"] == 88, "ruff line-length must be 88"
    assert ruff["target-version"] == "py310", "ruff target-version must be py310"
    assert black["line-length"] == 88, "black line-length must be 88"
    assert black["target-version"] == ["py310"], "black target-version must be py310"
    print("[OK] pyproject.toml: line-length=88 and target-version=py310 for ruff and black.")


def ensure_tool(tool: str) -> str:
    path = shutil.which(tool)
    if path:
        return path
    print(f"{tool} not found; installing per T001b prerequisite...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", tool],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Failed to install {tool}.")
    path = shutil.which(tool)
    if path is None:
        # Fall back to module invocation via the current interpreter.
        return None
    return path


def run_check(cmd: list) -> bool:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def main() -> int:
    validate_config()

    ensure_tool("ruff")
    ensure_tool("black")

    ruff_ok = run_check(["ruff", "check", "code/"])
    if not ruff_ok:
        # Retry via python -m in case PATH resolution differs.
        ruff_ok = run_check([sys.executable, "-m", "ruff", "check", "code/"])

    black_ok = run_check(["black", "--check", "code/"])
    if not black_ok:
        black_ok = run_check([sys.executable, "-m", "black", "--check", "code/"])

    if ruff_ok and black_ok:
        print("T001b PASSED: linting and formatting configuration validated.")
        return 0
    print("T001b: lint/format check reported issues (see above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())