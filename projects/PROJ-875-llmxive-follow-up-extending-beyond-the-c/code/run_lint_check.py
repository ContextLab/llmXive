import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(cmd: list) -> int:
    """
    Executes a shell command and returns the exit code.
    Prints output to stdout/stderr as the subprocess does.
    """
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return 1

def main():
    """
    Runs initial lint/format check on the codebase to verify tool configuration.
    Executes 'ruff check .' and 'black --check .' on the project root.
    Writes a summary report to results/lint_check_report.json.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(project_root, "results")
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    report_path = os.path.join(results_dir, "lint_check_report.json")
    
    print(f"Running lint/format checks in: {project_root}")
    
    checks = [
        ("ruff", ["ruff", "check", "."]),
        ("black", ["black", "--check", "."])
    ]
    
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_root": project_root,
        "checks": {}
    }
    
    all_passed = True
    
    for name, cmd in checks:
        print(f"\n--- Running {name} ---")
        return_code = run_command(cmd)
        
        results["checks"][name] = {
            "command": " ".join(cmd),
            "exit_code": return_code,
            "passed": return_code == 0
        }
        
        if return_code != 0:
            all_passed = False
            print(f"❌ {name} failed with exit code {return_code}")
        else:
            print(f"✅ {name} passed")
    
    # Write report
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n--- Summary ---")
    if all_passed:
        print("✅ All lint/format checks passed.")
        print(f"Report saved to: {report_path}")
        return 0
    else:
        print("❌ Some checks failed. Review output above and fix issues.")
        print(f"Report saved to: {report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())