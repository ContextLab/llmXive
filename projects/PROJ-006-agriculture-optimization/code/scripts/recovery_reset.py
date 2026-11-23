"""
Recovery and Reset Script for PROJ-006-agriculture-optimization.

This script scans the project structure for critical missing artifacts.
If critical source files are missing, it automatically unmarks (resets)
all dependent tasks (T015-T035) in tasks.md to '[ ]'.
It also verifies the existence of research.md.

Exit Codes:
  0: Reset complete, research.md exists, and dependencies are satisfied.
  1: research.md is missing (critical failure).
  2: Critical source files missing but reset logic executed successfully.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = PROJECT_ROOT / "tasks.md"
RESEARCH_FILE = PROJECT_ROOT / "research.md"
CRITICAL_SOURCE_FILES = [
    "src/data/collectors/survey_collector.py",
    "src/data/collectors/remote_sensing_collector.py",
    "src/data/processing/spatial_join.py",
    "src/data/processing/feature_engineering.py",
    "src/analysis/run_regression.py",
    "src/analysis/sensitivity_check.py",
    "src/cli/run_pipeline.py",
    "src/cli/validate.py",
    "src/services/report_generator.py",
]
CRITICAL_DATA_ARTIFACTS = [
    "data/processed/analysis_dataset.csv",
    "data/logs/linkage_validation.json",
]
TASK_RANGE_START = 15
TASK_RANGE_END = 35
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "recovery_reset.log"

def ensure_log_dir():
    """Ensure the log directory exists."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_message(message: str, level: str = "INFO"):
    """Log a message to the console and the log file."""
    ensure_log_dir()
    timestamp = "2026-04-30T00:00:00Z"  # Placeholder for deterministic logging if needed
    log_line = f"[{timestamp}] [{level}] {message}\n"
    print(log_line.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def check_research_md() -> bool:
    """Check if research.md exists."""
    if RESEARCH_FILE.exists():
        log_message(f"Found research.md at {RESEARCH_FILE}", "INFO")
        return True
    else:
        log_message(f"CRITICAL: research.md is missing at {RESEARCH_FILE}", "ERROR")
        return False

def scan_missing_artifacts() -> Tuple[List[str], List[str]]:
    """
    Scan for missing critical source files and data artifacts.
    Returns (missing_sources, missing_data).
    """
    missing_sources = []
    missing_data = []

    # Check source files
    for rel_path in CRITICAL_SOURCE_FILES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing_sources.append(rel_path)
            log_message(f"Missing source file: {rel_path}", "WARNING")

    # Check data artifacts
    for rel_path in CRITICAL_DATA_ARTIFACTS:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing_data.append(rel_path)
            log_message(f"Missing data artifact: {rel_path}", "WARNING")

    return missing_sources, missing_data

def scan_tests_directory() -> bool:
    """Verify that the tests/ directory exists and contains files."""
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        log_message(f"Tests directory missing: {tests_dir}", "WARNING")
        return False
    
    files = list(tests_dir.rglob("*.py"))
    if not files:
        log_message(f"Tests directory exists but contains no .py files", "WARNING")
        return False
    
    log_message(f"Found {len(files)} test files in {tests_dir}", "INFO")
    return True

def reset_tasks_in_md(missing_count: int) -> int:
    """
    Reset tasks T015-T035 in tasks.md to '[ ]' if any critical files are missing.
    Returns the number of tasks reset.
    """
    if missing_count == 0:
        log_message("No critical files missing. Skipping task reset.", "INFO")
        return 0

    if not TASKS_FILE.exists():
        log_message(f"tasks.md not found at {TASKS_FILE}", "ERROR")
        return 0

    log_message(f"Critical files missing. Resetting tasks T{TASK_RANGE_START:03d}-T{TASK_RANGE_END:03d}...", "INFO")
    
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to match task lines like "- [X] T015 ..." or "- [x] T015 ..."
    # We only want to reset tasks in the range T015 to T035
    pattern = r"(- \[([xX])\] )T(0?)(\d{2,})( )(.*)"
    
    def replace_match(match):
        prefix = match.group(1) # "- [X] "
        is_checked = match.group(2)
        padding = match.group(3) # Usually empty or '0'
        task_num = int(match.group(4))
        suffix = match.group(5) + match.group(6) # " " + description
        
        # Check if task number is in range [15, 35]
        if TASK_RANGE_START <= task_num <= TASK_RANGE_END:
            return f"- [ ] T{task_num:03d}{suffix}"
        else:
            return match.group(0)

    new_content, count = re.subn(pattern, replace_match, content)

    if count > 0:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        log_message(f"Reset {count} tasks in tasks.md.", "INFO")
    else:
        log_message("No tasks in range T015-T035 were found to reset.", "WARNING")

    return count

def main():
    """Main entry point for the recovery reset script."""
    log_message("Starting Recovery & Reset Process...", "INFO")
    
    # 1. Check research.md
    if not check_research_md():
        log_message("Aborting: research.md is missing.", "ERROR")
        sys.exit(1)

    # 2. Scan for missing artifacts
    missing_sources, missing_data = scan_missing_artifacts()
    total_missing = len(missing_sources) + len(missing_data)

    # 3. Scan tests directory
    scan_tests_directory()

    # 4. Reset tasks if necessary
    if total_missing > 0:
        reset_tasks_in_md(total_missing)
        log_message(f"Recovery complete. Found {total_missing} missing artifacts. Tasks reset.", "INFO")
        # Exit 2 to indicate artifacts were missing but reset was successful
        sys.exit(2)
    else:
        log_message("Recovery complete. All critical artifacts present.", "INFO")
        sys.exit(0)

if __name__ == "__main__":
    main()