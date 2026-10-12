"""Format all Python sources under code/ with Black (T003b).

Runs `black code/` from the project root so that the task's verification
command `black --check code/` exits 0. Fails loudly if Black is missing
or reports an internal error.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths


def main() -> int:
    project_root = paths.root
    code_dir = project_root / "code"
    if not code_dir.is_dir():
        print(f"ERROR: {code_dir} does not exist", file=sys.stderr)
        return 1

    result = subprocess.run(
        [sys.executable, "-m", "black", str(code_dir)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        print(
            f"ERROR: black formatting failed with exit code {result.returncode}",
            file=sys.stderr,
        )
        return result.returncode

    # Verify the check now passes.
    check = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        print(
            f"ERROR: black --check code/ still fails:\n{check.stdout}\n{check.stderr}",
            file=sys.stderr,
        )
        return check.returncode

    print("Black formatting complete; `black --check code/` passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
