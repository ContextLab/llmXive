"""
Utility script for linting the codebase.

This script is intentionally lightweight for the purpose of this
repository. In a full project it could invoke tools such as
flake8, pylint, black, or mypy. Here it simply provides a callable
entry point that can be used by CI scripts.
"""

import sys
import subprocess

def main() -> None:
    """Run a basic lint check using flake8 if available."""
    try:
        subprocess.run([sys.executable, "-m", "flake8", "code/"], check=True)
    except FileNotFoundError:
        # flake8 is not installed; fall back to a no‑op.
        print("flake8 not installed; lint step skipped.")
    except subprocess.CalledProcessError as exc:
        # Linting errors are propagated to the caller.
        sys.exit(exc.returncode)

if __name__ == "__main__":
    main()
