import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(cmd, cwd=None):
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)

    report_path = os.path.join(results_dir, "lint_check_report.json")
    log_path = os.path.join(results_dir, "lint_check.log")

    print(f"Running lint/format check in {project_root}...")

    # Check black formatting
    black_cmd = "black --check --diff ."
    print(f"Executing: {black_cmd}")
    black_ok, black_out, black_err = run_command(black_cmd, cwd=project_root)

    # Check ruff linting
    ruff_cmd = "ruff check ."
    print(f"Executing: {ruff_cmd}")
    ruff_ok, ruff_out, ruff_err = run_command(ruff_cmd, cwd=project_root)

    overall_success = black_ok and ruff_ok

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_root": project_root,
        "tools": {
            "black": {
                "command": black_cmd,
                "success": black_ok,
                "stdout": black_out,
                "stderr": black_err
            },
            "ruff": {
                "command": ruff_cmd,
                "success": ruff_ok,
                "stdout": ruff_out,
                "stderr": ruff_err
            }
        },
        "overall_success": overall_success
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Black Check:\n{'SUCCESS' if black_ok else 'FAILED'}\n{black_out}\n{black_err}\n")
        f.write(f"Ruff Check:\n{'SUCCESS' if ruff_ok else 'FAILED'}\n{ruff_out}\n{ruff_err}\n")

    print(f"Report written to: {report_path}")
    print(f"Log written to: {log_path}")

    if not overall_success:
        print("Lint/Format check FAILED. See logs for details.")
        sys.exit(1)
    else:
        print("Lint/Format check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
