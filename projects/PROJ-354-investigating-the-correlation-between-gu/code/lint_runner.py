import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory (parent of the code/ directory)."""
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def ensure_linting_configs(project_root: Path) -> bool:
    """
    Ensure .ruff.toml and pyproject.toml (with black config) exist.
    Returns True if configs are present or created successfully.
    """
    ruff_config = project_root / ".ruff.toml"
    pyproject_config = project_root / "pyproject.toml"

    if not ruff_config.exists():
        logger.info(f"Creating missing .ruff.toml at {ruff_config}")
        ruff_content = """[lint]
select = ["E", "F", "W", "I"]
ignore = []

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
        ruff_config.write_text(ruff_content)
        logger.info("Created .ruff.toml with E, F, W, I rules.")

    if not pyproject_config.exists():
        logger.info(f"Creating missing pyproject.toml at {pyproject_config}")
        pyproject_content = """[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
"""
        pyproject_config.write_text(pyproject_content)
        logger.info("Created pyproject.toml with [tool.black] section.")
    else:
        # Check if black section exists
        content = pyproject_config.read_text()
        if "[tool.black]" not in content:
            logger.warning("pyproject.toml exists but lacks [tool.black] section. Appending.")
            with open(pyproject_config, "a") as f:
                f.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py310']\n")
        else:
            logger.info("pyproject.toml already contains [tool.black].")

    return True

def run_black(project_root: Path) -> Tuple[bool, str, str]:
    """
    Run black formatter on the codebase.
    Returns (success, stdout, stderr).
    """
    logger.info("Running Black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(project_root / "code")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # Black returns 0 if no changes needed, 1 if changes needed
        # We treat "no changes needed" as success for the check, but if changes are needed,
        # we might want to format them. The task says "Run black... to ensure compliance".
        # Let's actually run formatting if needed to ensure compliance.
        if result.returncode != 0:
            logger.info("Code needs formatting. Running black to fix...")
            format_result = subprocess.run(
                [sys.executable, "-m", "black", str(project_root / "code")],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if format_result.returncode != 0:
                logger.error(f"Black formatting failed: {format_result.stderr}")
                return False, format_result.stdout, format_result.stderr
            logger.info("Black formatting completed successfully.")
            return True, "Formatted successfully", ""
        else:
            logger.info("Black check passed (no changes needed).")
            return True, "No changes needed", ""
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False, "", str(e)

def run_ruff(project_root: Path) -> Tuple[bool, str, str]:
    """
    Run ruff linter on the codebase.
    Returns (success, stdout, stderr).
    """
    logger.info("Running Ruff linter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(project_root / "code")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode != 0:
            logger.warning("Ruff found issues. Attempting to fix automatically...")
            fix_result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--fix", str(project_root / "code")],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if fix_result.returncode != 0:
                logger.error(f"Ruff fix failed. Remaining issues:\n{fix_result.stdout}")
                return False, fix_result.stdout, fix_result.stderr
            logger.info("Ruff automatic fixes applied successfully.")
            return True, "Fixed automatically", ""
        else:
            logger.info("Ruff check passed (no issues found).")
            return True, "No issues found", ""
    except Exception as e:
        logger.error(f"Error running ruff: {e}")
        return False, "", str(e)

def generate_compliance_report(project_root: Path, black_success: bool, ruff_success: bool) -> str:
    """
    Generate a JSON compliance report.
    """
    report = {
        "task_id": "T041",
        "description": "Run black and ruff on all code to ensure formatting and linting compliance.",
        "status": "completed" if (black_success and ruff_success) else "failed",
        "details": {
            "black": {
                "success": black_success,
                "message": "Black formatting completed" if black_success else "Black formatting failed"
            },
            "ruff": {
                "success": ruff_success,
                "message": "Ruff linting completed" if ruff_success else "Ruff linting failed"
            }
        },
        "timestamp": str(Path.now()) if hasattr(Path, 'now') else "2023-10-27T10:00:00"
    }
    # Fallback for timestamp if Path.now doesn't exist in older python versions
    from datetime import datetime
    report["timestamp"] = datetime.now().isoformat()

    report_path = project_root / "results" / "validation" / "linting_compliance_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Compliance report saved to {report_path}")
    return str(report_path)

def main():
    """
    Main entry point for the lint runner.
    Ensures configs exist, runs black and ruff, and generates a report.
    """
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Ensure configs
    if not ensure_linting_configs(project_root):
        logger.error("Failed to ensure linting configurations.")
        sys.exit(1)

    # Run Black
    black_success, _, _ = run_black(project_root)

    # Run Ruff
    ruff_success, _, _ = run_ruff(project_root)

    # Generate Report
    report_path = generate_compliance_report(project_root, black_success, ruff_success)

    if black_success and ruff_success:
        logger.info("All linting checks passed.")
        sys.exit(0)
    else:
        logger.error("Linting checks failed. See report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()