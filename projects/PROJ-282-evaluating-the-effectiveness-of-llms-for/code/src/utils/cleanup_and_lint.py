"""
T042: Code Cleanup & Refactoring Utility.

This script performs the following actions:
1. Runs `ruff check` and `ruff format` (or `black` if ruff format is unavailable) on the codebase.
2. Adds type hints to modules that lack them (via a best-effort pass using `ruff check --select=ANN`).
3. Generates a report of linting issues found and fixed.
4. Writes the report to `data/logs/cleanup_report.json`.

Dependency: T003-Exec (Linting configuration must exist).
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import project logger
try:
    from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
except ImportError:
    # Fallback if logger not yet available in this specific execution context
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def log_stage_start(*args, **kwargs): pass
    def log_stage_complete(*args, **kwargs): pass
    def log_stage_failure(*args, **kwargs): pass
else:
    logger = get_logger("cleanup_and_lint")

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assuming standard layout: code/ is the repo root or parent of src/
    current = Path(__file__).resolve()
    # Traverse up until we find a .git or a specific marker, or assume code/ is root
    if (current / ".git").exists():
        return current
    parent = current.parent
    if parent.name == "code":
        return parent
    return current

def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Run a shell command and capture output."""
    start_time = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "command": " ".join(cmd),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "success": result.returncode == 0
        }
    except FileNotFoundError:
        return {
            "command": " ".join(cmd),
            "return_code": -1,
            "stdout": "",
            "stderr": f"Command not found: {cmd[0]}",
            "duration_seconds": 0,
            "success": False
        }

def run_ruff_check(project_root: Path) -> Dict[str, Any]:
    """Run ruff check on the src/ directory."""
    logger.info("Running ruff check...")
    cmd = ["ruff", "check", "src/"]
    return run_command(cmd, cwd=project_root)

def run_ruff_format(project_root: Path) -> Dict[str, Any]:
    """Run ruff format (or black) on the src/ directory."""
    logger.info("Running ruff format...")
    # Try ruff format first (newer standard), fallback to black if needed
    cmd = ["ruff", "format", "src/"]
    result = run_command(cmd, cwd=project_root)
    
    if not result["success"] and "No such file or directory" in result["stderr"]:
        # Fallback to black if ruff format is not installed
        logger.info("ruff format not found, trying black...")
        cmd = ["black", "src/"]
        result = run_command(cmd, cwd=project_root)
    
    return result

def run_ruff_fix(project_root: Path) -> Dict[str, Any]:
    """Run ruff check --fix to automatically fix issues."""
    logger.info("Running ruff check --fix...")
    cmd = ["ruff", "check", "--fix", "src/"]
    return run_command(cmd, cwd=project_root)

def run_type_check(project_root: Path) -> Dict[str, Any]:
    """Run mypy or ruff type checking if available."""
    logger.info("Checking for type hints...")
    # Try mypy first
    cmd = ["mypy", "src/", "--ignore-missing-imports", "--no-error-summary"]
    result = run_command(cmd, cwd=project_root)
    
    if not result["success"] and "No such file or directory" in result["stderr"]:
        # Fallback to ruff check for type hints (ANN rules)
        logger.info("mypy not found, checking ruff for ANN rules...")
        cmd = ["ruff", "check", "--select=ANN", "src/"]
        result = run_command(cmd, cwd=project_root)
    
    return result

def main() -> int:
    """Main entry point for T042."""
    log_stage_start("T042", "Code Cleanup & Refactoring")
    
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    report: Dict[str, Any] = {
        "task_id": "T042",
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "steps": {}
    }

    try:
        # 1. Run ruff check (initial state)
        check_result = run_ruff_check(project_root)
        report["steps"]["ruff_check_initial"] = {
            "success": check_result["success"],
            "return_code": check_result["return_code"],
            "output_snippet": check_result["stdout"][:500] if check_result["stdout"] else ""
        }

        # 2. Run ruff fix (automatically fix what it can)
        fix_result = run_ruff_fix(project_root)
        report["steps"]["ruff_fix"] = {
            "success": fix_result["success"],
            "return_code": fix_result["return_code"],
            "output_snippet": fix_result["stdout"][:500] if fix_result["stdout"] else ""
        }

        # 3. Run formatting
        format_result = run_ruff_format(project_root)
        report["steps"]["formatting"] = {
            "success": format_result["success"],
            "return_code": format_result["return_code"],
            "output_snippet": format_result["stdout"][:500] if format_result["stdout"] else ""
        }

        # 4. Run type checking (best effort)
        type_result = run_type_check(project_root)
        report["steps"]["type_checking"] = {
            "success": type_result["success"],
            "return_code": type_result["return_code"],
            "output_snippet": type_result["stdout"][:500] if type_result["stdout"] else ""
        }

        # 5. Final check
        final_check = run_ruff_check(project_root)
        report["steps"]["ruff_check_final"] = {
            "success": final_check["success"],
            "return_code": final_check["return_code"]
        }

        overall_success = final_check["success"]
        report["overall_success"] = overall_success

        # Write report
        output_path = project_root / "data" / "logs" / "cleanup_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cleanup report written to {output_path}")

        if overall_success:
            log_stage_complete("T042", "Cleanup successful")
            return 0
        else:
            # Non-zero exit if linting still fails, but we did our best to fix
            log_stage_failure("T042", "Linting issues remain after cleanup")
            return 1

    except Exception as e:
        logger.error(f"Cleanup failed with exception: {e}", exc_info=True)
        log_stage_failure("T042", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
