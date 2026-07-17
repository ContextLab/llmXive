"""
Validation script for quickstart.md documentation.
Validates that quickstart.md exists, contains required sections,
and that referenced files/directories actually exist.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Import logging utilities from sibling module
from utils_logging import (
    get_project_root,
    ensure_log_directory,
    setup_logger,
    get_pipeline_logger,
    log_info,
    log_warning,
    log_error,
    log_abort
)


def check_file_exists(file_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a specific file exists."""
    if file_path.exists():
        return True, f"✓ {description} exists at {file_path}"
    return False, f"✗ {description} missing at {file_path}"


def check_dir_exists(dir_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a specific directory exists."""
    if dir_path.exists() and dir_path.is_dir():
        return True, f"✓ {description} exists at {dir_path}"
    return False, f"✗ {description} missing at {dir_path}"


def check_r_installed() -> Tuple[bool, str]:
    """Check if R is installed and accessible."""
    try:
        result = subprocess.run(
            ["R", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return True, f"✓ R is installed: {version_line}"
        return False, "✗ R installation check failed"
    except FileNotFoundError:
        return False, "✗ R not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "✗ R version check timed out"


def check_renv_initialized(project_root: Path) -> Tuple[bool, str]:
    """Check if renv is initialized (renv.lock exists)."""
    lockfile = project_root / "renv.lock"
    if lockfile.exists():
        return True, f"✓ renv initialized (renv.lock found)"
    return False, "✗ renv not initialized (renv.lock missing)"


def check_logging_infrastructure(project_root: Path) -> Tuple[bool, str]:
    """Check if logging infrastructure is in place."""
    log_dir = project_root / "logs"
    if log_dir.exists() and log_dir.is_dir():
        return True, f"✓ Logging directory exists at {log_dir}"
    return False, f"✗ Logging directory missing at {log_dir}"


def validate_quickstart_content(project_root: Path) -> List[Tuple[bool, str]]:
    """
    Validate the content of quickstart.md.
    Checks for required sections and referenced paths.
    """
    quickstart_path = project_root / "quickstart.md"
    results = []

    # Check file existence
    exists, msg = check_file_exists(quickstart_path, "quickstart.md")
    results.append((exists, msg))
    if not exists:
        return results

    # Read and parse content
    try:
        content = quickstart_path.read_text(encoding='utf-8')
    except Exception as e:
        results.append((False, f"✗ Failed to read quickstart.md: {e}"))
        return results

    # Required sections to check
    required_sections = [
        "Setup",
        "Data Requirements",
        "Run Commands",
        "Data Source Note"
    ]

    for section in required_sections:
        if section.lower() in content.lower():
            results.append((True, f"✓ Section '{section}' found in quickstart.md"))
        else:
            results.append((False, f"✗ Required section '{section}' missing in quickstart.md"))

    # Check for referenced critical files
    critical_files = [
        ("code/01_ingest.R", "Ingest script"),
        ("code/02_classify.R", "Classification script"),
        ("code/03_analysis.R", "Analysis script"),
        ("code/04_report.Rmd", "Report template"),
        ("data/raw/", "Raw data directory"),
        ("data/processed/", "Processed data directory"),
        ("data/derived/", "Derived data directory")
    ]

    for rel_path, desc in critical_files:
        full_path = project_root / rel_path
        if rel_path.endswith('/'):
            exists, msg = check_dir_exists(full_path, desc)
        else:
            exists, msg = check_file_exists(full_path, desc)
        results.append((exists, msg))

    # Check for data source warning
    if "user-provided" in content.lower() or "real data" in content.lower():
        results.append((True, "✓ Data source warning/note found"))
    else:
        results.append((False, "✗ Missing data source warning (should mention user-provided real data)"))

    return results


def run_quickstart_validation(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Run all validation checks and return summary.
    Returns (success, list of all messages).
    """
    messages = []
    all_passed = True

    # 1. Check R installation
    passed, msg = check_r_installed()
    messages.append(msg)
    if not passed:
        all_passed = False

    # 2. Check renv initialization
    passed, msg = check_renv_initialized(project_root)
    messages.append(msg)
    if not passed:
        all_passed = False

    # 3. Check logging infrastructure
    passed, msg = check_logging_infrastructure(project_root)
    messages.append(msg)
    if not passed:
        all_passed = False

    # 4. Validate quickstart.md content
    content_results = validate_quickstart_content(project_root)
    messages.extend([msg for _, msg in content_results])
    if not all(result[0] for result in content_results):
        all_passed = False

    return all_passed, messages


def main():
    """Main entry point for quickstart validation."""
    project_root = get_project_root()
    log_info("Starting quickstart.md validation...")

    success, messages = run_quickstart_validation(project_root)

    for msg in messages:
        if msg.startswith("✓"):
            log_info(msg)
        elif msg.startswith("✗"):
            log_warning(msg)

    if success:
        log_info("Quickstart validation PASSED.")
        sys.exit(0)
    else:
        log_error("Quickstart validation FAILED. See warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
