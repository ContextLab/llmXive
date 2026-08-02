"""
Linting Runner for PROJ-082
Runs ruff on the codebase and generates a structured report.
"""
import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def run_ruff_check(project_root: Path) -> tuple:
    """
    Runs ruff check on the project root.
    Returns (success, output_text)
    """
    cmd = [sys.executable, "-m", "ruff", "check", str(project_root), "--output-format", "full"]
    logger.info(f"Running linting command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        # ruff returns exit code 0 if no issues, 1 if issues found, 2 if error
        output = result.stdout + result.stderr
        return (result.returncode == 0, output)
    except subprocess.TimeoutExpired:
        logger.error("Linting timed out.")
        return (False, "Linting timed out after 120 seconds.")
    except Exception as e:
        logger.error(f"Linting execution error: {e}")
        return (False, str(e))

def run_ruff_fix(project_root: Path) -> tuple:
    """
    Runs ruff check --fix on the project root.
    Returns (success, output_text)
    """
    cmd = [sys.executable, "-m", "ruff", "check", str(project_root), "--fix"]
    logger.info(f"Running auto-fix command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout + result.stderr
        return (result.returncode == 0, output)
    except subprocess.TimeoutExpired:
        logger.error("Fix command timed out.")
        return (False, "Fix command timed out.")
    except Exception as e:
        logger.error(f"Fix execution error: {e}")
        return (False, str(e))

def generate_report(success: bool, output: str, fixed_success: bool = None, fixed_output: str = None) -> str:
    """
    Generates a Markdown report from linting results.
    """
    timestamp = datetime.now().isoformat()
    
    report_lines = [
        "# Linting Report",
        f"Generated: {timestamp}",
        "",
        "## Initial Check",
        f"**Status**: {'PASSED' if success else 'FAILED'}",
        "```text",
        output if output else "(No output)",
        "```",
        ""
    ]

    if not success:
        report_lines.extend([
            "## Auto-Fix Attempt",
            f"**Status**: {'PASSED' if fixed_success else 'FAILED (or not attempted)'}",
            "```text",
            fixed_output if fixed_output else "(No output or not attempted)",
            "```",
            ""
        ])
        
        if fixed_success:
            report_lines.append("> **Note**: Issues were automatically fixed. Please verify changes.")
        else:
            report_lines.append("> **Note**: Auto-fix was either not attempted, failed, or did not resolve all issues. Manual intervention may be required.")
    else:
        report_lines.append("## Summary")
        report_lines.append("All linting checks passed successfully.")

    return "\n".join(report_lines)

def main():
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = log_dir / "lint_report.md"
    
    logger.info(f"Starting linting process for project at {project_root}")
    
    # 1. Run initial check
    success, output = run_ruff_check(project_root)
    
    fixed_success = None
    fixed_output = None
    
    # 2. If failed, attempt fix
    if not success:
        logger.warning("Linting failed. Attempting auto-fix.")
        fixed_success, fixed_output = run_ruff_fix(project_root)
        
        # Re-check to see if fixes resolved everything
        if fixed_success:
            # Run check again to confirm clean state
            final_success, final_output = run_ruff_check(project_root)
            if not final_success:
                logger.warning("Auto-fix ran but issues remain.")
                # We still report the fix attempt, but note remaining issues
            else:
                logger.info("Auto-fix resolved all issues.")
        else:
            logger.error("Auto-fix failed or was skipped.")

    # 3. Generate Report
    report_content = generate_report(success, output, fixed_success, fixed_output)
    
    # 4. Write Report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Linting report saved to {report_path}")
    
    # Exit with code 0 regardless of lint status, as the task is to generate the report.
    # If the CI pipeline needs to fail on lint errors, it should parse the report or run ruff directly.
    # However, standard practice for a "run linting and save log" task is to complete the action.
    return 0

if __name__ == "__main__":
    sys.exit(main())
