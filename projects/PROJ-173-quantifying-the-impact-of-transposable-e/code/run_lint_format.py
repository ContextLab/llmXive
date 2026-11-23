"""
Run Black and Ruff linting/formatting checks on the project source code.

The script writes a combined report to the results folder:
data/results/lint_format_report.txt
"""
import subprocess
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _run_command(command):
    """Run a shell command, capture stdout and stderr, return output string."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.stdout
    except Exception as e:
        log.error(f"Failed to run {' '.join(command)}: {e}")
        return f"Error executing command: {e}\n"

def main():
    # Destination for the report
    report_path = paths.results("lint_format_report.txt")
    # Ensure the results directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    sections = []

    # 1. Run Black in check mode
    black_cmd = ["python", "-m", "black", "--check", "--diff", "code"]
    sections.append("=== Black (check mode) ===\n")
    sections.append(_run_command(black_cmd) + "\n")

    # 2. Run Ruff (lint)
    ruff_cmd = ["python", "-m", "ruff", "check", "code"]
    sections.append("=== Ruff (lint) ===\n")
    sections.append(_run_command(ruff_cmd) + "\n")

    # 3. Run pre-commit hooks (if installed)
    precommit_cmd = ["pre-commit", "run", "--all-files"]
    sections.append("=== Pre-commit Hooks ===\n")
    sections.append(_run_command(precommit_cmd) + "\n")

    # Write combined report
    report_content = "\n".join(sections)
    report_path.write_text(report_content, encoding="utf-8")
    log.info(f"Lint/format report written to {report_path}")

if __name__ == "__main__":
    main()
