"""
Script to execute pytest and capture its full console output
into the processed data directory as required by task T010d.
"""

import subprocess
import sys
from pathlib import Path

# Import the project's path helper
try:
    from llmxive_toolkit import paths
except ImportError:
    # Fallback: construct paths relative to this file
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    def _data_path(*parts):
        return PROJECT_ROOT / "data" / Path(*parts)
    class _Paths:
        @staticmethod
        def data(*parts):
            return _data_path(*parts)
    paths = _Paths()

def main() -> int:
    """
    Run pytest on the entire test suite and write the captured output
    to ``data/processed/pytest_lint_log.txt``.
    Returns the subprocess exit code (0 on success).
    """
    # Ensure the output directory exists
    output_path = paths.data("processed", "pytest_lint_log.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Execute pytest, capturing stdout and stderr
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
        )
    except Exception as e:
        print(f"Failed to invoke pytest: {e}", file=sys.stderr)
        return 1

    # Write the full console output to the log file
    output_path.write_text(completed.stdout, encoding="utf-8")

    # Return the pytest exit code (0 means all tests passed)
    return completed.returncode

if __name__ == "__main__":
    sys.exit(main())