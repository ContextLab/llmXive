"""
Linting Runner for llmXive Project.
Executes Ruff checks and fixes, generating a markdown report.
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def run_ruff_check() -> tuple:
    """
    Run ruff check on the code directory.
    Returns (success, stdout, stderr).
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir), "--output-format=full"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error("ruff not found. Please install it via 'pip install ruff'.")
        return False, "", "ruff not found"

def run_ruff_fix() -> tuple:
    """
    Run ruff check --fix on the code directory.
    Returns (success, stdout, stderr).
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir), "--fix", "--exit-zero"],
            capture_output=True,
            text=True,
            check=False
        )
        # Return True if the command ran successfully, regardless of issues found
        return True, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error("ruff not found.")
        return False, "", "ruff not found"

def generate_report(check_success: bool, check_stdout: str, check_stderr: str, 
                    fix_success: bool, fix_stdout: str, fix_stderr: str, 
                    output_path: Path) -> None:
    """
    Generate a markdown report of the linting results.
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    lines = [
        "# Linting Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Project Root:** {get_project_root()}",
        "",
        "## Summary",
        "",
        f"- **Initial Check Status:** {'Passed' if check_success else 'Failed'}",
        f"- **Fix Attempt Status:** {'Completed' if fix_success else 'Failed'}",
        "",
        "## Initial Check Output",
        "",
    ]
    
    if check_stdout:
        lines.append("```")
        lines.append(check_stdout)
        lines.append("```")
        lines.append("")
    
    if check_stderr and not check_stdout:
        lines.append("```")
        lines.append(check_stderr)
        lines.append("```")
        lines.append("")
        
    if not check_stdout and not check_stderr:
        lines.append("*No output from initial check.*")
        lines.append("")

    lines.append("## Fix Attempt Output")
    lines.append("")
    
    if fix_stdout:
        lines.append("```")
        lines.append(fix_stdout)
        lines.append("```")
        lines.append("")
        
    if fix_stderr and not fix_stdout:
        lines.append("```")
        lines.append(fix_stderr)
        lines.append("```")
        lines.append("")
        
    if not fix_stdout and not fix_stderr:
        lines.append("*No output from fix attempt.*")
        lines.append("")

    lines.append("---")
    lines.append("*End of Report*")
    
    content = "\n".join(lines)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Linting report saved to {output_path}")

def main():
    """Main entry point for linting runner."""
    project_root = get_project_root()
    report_path = project_root / "data" / "logs" / "lint_report.md"
    
    logger.info("Starting linting process...")
    
    # Run initial check
    check_success, check_stdout, check_stderr = run_ruff_check()
    
    if not check_success:
        logger.warning("Linting issues found. Attempting to fix...")
        # Run fix
        fix_success, fix_stdout, fix_stderr = run_ruff_fix()
        
        if not fix_success:
            logger.error("Fix attempt failed.")
    else:
        logger.info("No linting issues found.")
        fix_success, fix_stdout, fix_stderr = True, "No issues to fix.", ""
    
    # Generate report
    generate_report(
        check_success, check_stdout, check_stderr,
        fix_success, fix_stdout, fix_stderr,
        report_path
    )
    
    if not check_success:
        logger.warning("Linting completed with issues. Review the report at: " + str(report_path))
        # Do not exit with error code to allow pipeline to continue and log the issue
    else:
        logger.info("Linting completed successfully.")

if __name__ == "__main__":
    main()
