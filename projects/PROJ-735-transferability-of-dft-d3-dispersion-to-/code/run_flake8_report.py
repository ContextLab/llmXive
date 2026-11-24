"""
Run flake8 on the project and write a detailed report (including exit code)
to ``code/lint_report.txt``.
"""

import subprocess
from pathlib import Path

def main() -> None:
    # Run flake8 on both ``code`` and ``tests`` directories
    cmd = ["flake8", "code", "tests"]
    result = subprocess.run(
        cmd, capture_output=True, text=True
    )
    exit_code = result.returncode
    output = result.stdout + result.stderr

    report_path = Path("code/lint_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w") as f:
        f.write(f"Exit code: {exit_code}\\n")
        f.write(output)

if __name__ == "__main__":
    main()
