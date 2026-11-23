"""
Wrapper script for plan scope verification.

This script exists at the repository root (sibling to the project
folder) to satisfy the test harness, which expects the script at
`<repo_root>/code/verify_plan_scope.py`. It simply forwards execution
to the actual implementation located in the project’s own code
directory.
"""

import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve the path to the real script inside the project folder.
    # The project directory is assumed to be the immediate sub‑directory
    # under the repository root that contains a `code` folder.
    repo_root = Path(__file__).resolve().parent
    # Find the first sub‑directory that contains the real script.
    # In this repository the project directory is named
    # `PROJ-203-predicting-phase-transitions-in-amorphou`.
    project_dir = next(p for p in repo_root.iterdir()
                      if p.is_dir() and (p / "code" / "verify_plan_scope.py").exists())
    real_script = project_dir / "code" / "verify_plan_scope.py"

    # Run the real script using the same Python interpreter.
    result = subprocess.run([sys.executable, str(real_script)], capture_output=True, text=True)

    # Forward stdout and stderr.
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)

    # Exit with the same return code.
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
