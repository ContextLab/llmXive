"""
Run black in check mode over the entire codebase.

This script executes ``black --check`` on the ``code/`` directory,
captures the output, and writes a concise report to
``output/black_check_report.txt``. If any files are not properly
formatted, the script exits with a non‑zero status so that CI can
fail the task.

The implementation deliberately avoids any side effects other than
the report file, adhering to the project’s “run‑check‑only” policy.
"""
import subprocess
import sys
from pathlib import Path

def run_black_check() -> int:
    """
    Execute ``black --check`` on the ``code/`` directory.

    Returns
    -------
    int
        The exit code from the ``black`` command (0 if all files are
        correctly formatted, non‑zero otherwise).
    """
    # Ensure the output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "black_check_report.txt"

    # Run black in check mode; capture both stdout and stderr
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        # ``black`` is not installed – raise so the failure is loud
        raise RuntimeError("Black formatter is not installed.") from exc

    # Write the full output to the report file
    report_path.write_text(result.stdout)

    # Print a short message to the console for user feedback
    print(f"Black check completed with exit code {result.returncode}.")
    print(f"Report written to {report_path}")

    return result.returncode

def main() -> None:
    """
    Entry point for ``python code/run_black_check.py``.
    """
    exit_code = run_black_check()
    # Propagate the exit code to the shell
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
