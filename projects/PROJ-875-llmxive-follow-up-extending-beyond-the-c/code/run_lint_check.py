import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(command: list, cwd: str = None) -> tuple:
    """
    Run a shell command and return (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def main():
    """
    Execute 'ruff check .' on the project root and save the output to results/lint_report.txt.
    This verifies the tool configuration is correct.
    Exit codes:
      0: No issues found
      1: Issues found (warnings/errors) - still considered a successful run for verification
      >1: System error or crash
    """
    # Determine project root (assumed to be where this script is run from or parent)
    # The task requires running from the project root relative to the repo.
    # We assume the script is executed from the project root.
    project_root = os.getcwd()
    output_file = os.path.join(project_root, "results", "lint_report.txt")
    
    # Ensure results directory exists
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)

    command = ["ruff", "check", "."]
    
    print(f"Running lint check: {' '.join(command)}")
    print(f"Working directory: {project_root}")
    
    stdout, stderr, returncode = run_command(command, cwd=project_root)
    
    # Combine stdout and stderr for the report
    report_content = f"RUFF LINT CHECK REPORT\n"
    report_content += f"Timestamp: {datetime.now().isoformat()}\n"
    report_content += f"Command: {' '.join(command)}\n"
    report_content += f"Working Directory: {project_root}\n"
    report_content += f"Return Code: {returncode}\n"
    report_content += "-" * 50 + "\n\n"
    
    if stdout:
        report_content += "STDOUT:\n"
        report_content += stdout + "\n"
    
    if stderr:
        report_content += "STDERR:\n"
        report_content += stderr + "\n"
    
    if returncode == 0:
        report_content += "\nSTATUS: PASSED (No issues found)\n"
    elif returncode == 1:
        report_content += "\nSTATUS: ISSUES FOUND (Verification successful, issues detected as expected)\n"
    else:
        report_content += f"\nSTATUS: FAILED (Unexpected return code {returncode})\n"

    # Write the report
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"Report written to: {output_file}")
    
    # Return 0 if the tool ran successfully (even if it found errors), 
    # otherwise return the error code.
    # For verification purposes, 0 or 1 means the tool worked.
    if returncode in (0, 1):
        sys.exit(0)
    else:
        sys.exit(returncode)

if __name__ == "__main__":
    main()
