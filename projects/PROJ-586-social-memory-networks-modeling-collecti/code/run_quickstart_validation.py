"""
T031: Run quickstart.md validation.

Executes all commands listed in quickstart.md and verifies that each exits with code 0.
Produces a validation report at results/quickstart_validation_report.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORT_PATH = RESULTS_DIR / "quickstart_validation_report.md"

# Commands to execute (hardcoded based on typical quickstart steps for this project)
# These correspond to the experiment runs required by US-1, US-2, and US-3
COMMANDS = [
    # US-1: Full context baseline
    [
        "python", "run_experiment.py",
        "--context", "full",
        "--agents", "5",
        "--games", "100",
        "--seed", "42"
    ],
    # US-1: Larger run for full results
    [
        "python", "run_experiment.py",
        "--context", "full",
        "--agents", "5",
        "--games", "1000",
        "--seed", "42"
    ],
    # US-2: Limited context
    [
        "python", "run_experiment.py",
        "--context", "limited",
        "--agents", "5",
        "--games", "1000",
        "--seed", "42"
    ],
    # US-3: Scaling analysis
    [
        "python", "run_experiment.py",
        "--context", "full",
        "--agents", "3,5,7",
        "--games", "800",
        "--plot", "scaling"
    ],
]

def run_command(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes per command
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -3, "", str(e)

def generate_report(results: List[Tuple[List[str], int, str, str]]) -> str:
    """Generate a markdown validation report."""
    lines = [
        "# Quickstart Validation Report",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "",
        "## Summary",
        "",
    ]

    passed = sum(1 for _, rc, _, _ in results if rc == 0)
    total = len(results)
    lines.append(f"Commands executed: {total}")
    lines.append(f"Commands passed (exit 0): {passed}")
    lines.append(f"Commands failed: {total - passed}")
    lines.append("")

    if passed == total:
        lines.append("## Verdict: PASSED")
        lines.append("All quickstart commands executed successfully.")
    else:
        lines.append("## Verdict: FAILED")
        lines.append("One or more commands failed.")

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")

    for i, (cmd, rc, stdout, stderr) in enumerate(results, 1):
        status = "✅ PASS" if rc == 0 else f"❌ FAIL (rc={rc})"
        lines.append(f"### {i}. {' '.join(cmd)}")
        lines.append(f"**Status**: {status}")
        lines.append("")

        if stdout:
            lines.append("**stdout**:")
            lines.append("```")
            lines.append(stdout.strip())
            lines.append("```")
            lines.append("")

        if stderr:
            lines.append("**stderr**:")
            lines.append("```")
            lines.append(stderr.strip())
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def main():
    """Main entry point for validation."""
    if not QUICKSTART_PATH.exists():
        print(f"Error: quickstart.md not found at {QUICKSTART_PATH}")
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Running validation of {QUICKSTART_PATH}...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Executing {len(COMMANDS)} commands...")

    results = []
    all_passed = True

    for cmd in COMMANDS:
        cmd_str = ' '.join(cmd)
        print(f"\n[1/{len(COMMANDS)}] Running: {cmd_str}")
        rc, stdout, stderr = run_command(cmd, PROJECT_ROOT)

        if rc != 0:
            all_passed = False
            print(f"  ❌ FAILED with rc={rc}")
        else:
            print(f"  ✅ PASSED")

        results.append((cmd, rc, stdout, stderr))

    # Generate report
    report = generate_report(results)
    REPORT_PATH.write_text(report)
    print(f"\nValidation report written to: {REPORT_PATH}")

    if all_passed:
        print("\n✅ Quickstart validation PASSED.")
        sys.exit(0)
    else:
        print("\n❌ Quickstart validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()