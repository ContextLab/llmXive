"""
Recovery and Reset Script for PROJ-006-agriculture-optimization.

Logic:
1. Verify existence of `research.md` (required prerequisite).
2. Scan `data/`, `src/`, and `tests/` for critical artifacts defined in tasks.md.
3. If critical source files (e.g., T015-T035 implementations) are missing,
   automatically unmark (reset) all dependent tasks in `tasks.md` to `[ ]`.
4. Exit 0 if reset is complete or no reset needed; Exit 1 if research.md is missing.
"""
import os
import sys
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project root (assuming script is in projects/PROJ-006-agriculture-optimization/scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
TASKS_FILE = PROJECT_ROOT / "tasks.md"
RESEARCH_FILE = PROJECT_ROOT / "research.md"

# Critical artifacts that indicate T015-T035 are implemented
# Based on tasks.md descriptions for User Story 1, 2, 3
CRITICAL_SOURCE_FILES = [
    "src/data/collectors/survey_collector.py",
    "src/data/collectors/remote_sensing_collector.py",
    "src/data/processing/spatial_join.py",
    "src/data/processing/feature_engineering.py",
    "src/data/processing/final_assembly.py",
    "src/analysis/run_regression.py",
    "src/analysis/sensitivity_check.py",
    "src/services/report_generator.py",
    "src/cli/run_pipeline.py",
    "src/cli/validate.py",
]

# Critical data artifacts that should exist if pipeline ran successfully
CRITICAL_DATA_ARTIFACTS = [
    "data/processed/analysis_dataset.csv",
    "data/logs/linkage_validation.json",
]

# Task range to reset
TASK_RANGE_START = 15
TASK_RANGE_END = 35

def check_research_document() -> bool:
    """Verify research.md exists. Exit 1 if missing."""
    if not RESEARCH_FILE.exists():
        logger.error(f"CRITICAL: {RESEARCH_FILE} is missing. Cannot proceed.")
        return False
    logger.info(f"Found {RESEARCH_FILE}")
    return True

def check_artifacts() -> dict:
    """Check for existence of critical source and data files."""
    missing_sources = []
    missing_data = []

    for rel_path in CRITICAL_SOURCE_FILES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing_sources.append(rel_path)

    for rel_path in CRITICAL_DATA_ARTIFACTS:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing_data.append(rel_path)

    return {
        "missing_sources": missing_sources,
        "missing_data": missing_data
    }

def reset_tasks_in_tasks_md(missing_sources: list) -> bool:
    """
    Reset tasks T015-T035 to [ ] if critical source files are missing.
    Returns True if tasks were modified, False otherwise.
    """
    if not missing_sources:
        logger.info("All critical source files found. No reset needed.")
        return False

    logger.warning(f"Missing critical source files: {missing_sources}")
    logger.info(f"Resetting tasks T{TASK_RANGE_START:03d}-T{TASK_RANGE_END:03d} in {TASKS_FILE}")

    if not TASKS_FILE.exists():
        logger.error(f"Cannot reset: {TASKS_FILE} not found.")
        return False

    try:
        content = TASKS_FILE.read_text()
        lines = content.splitlines()
        modified = False
        new_lines = []

        # Regex to match task lines in the range T015 to T035
        # Matches: - [X] T015 ... or - [ ] T015 ...
        pattern = re.compile(r'^(\s*- \[.)\s(T01[5-9]|T02[0-9]|T03[0-5])\s')

        for line in lines:
            match = pattern.match(line)
            if match:
                # Found a task in the range
                prefix = match.group(1)
                task_id = match.group(2)
                if prefix == "[X]":
                    # Reset to [ ]
                    new_line = line.replace("[X]", "[ ]", 1)
                    new_lines.append(new_line)
                    logger.debug(f"Reset {task_id} to [ ]")
                    modified = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if modified:
            TASKS_FILE.write_text("\n".join(new_lines))
            logger.info(f"Successfully reset tasks in {TASKS_FILE}")
        else:
            logger.info("No tasks in range T015-T035 were marked [X].")

        return modified

    except Exception as e:
        logger.error(f"Failed to reset tasks: {e}")
        return False

def main():
    logger.info("Starting Recovery & Reset (T000)...")

    # 1. Verify research.md
    if not check_research_document():
        sys.exit(1)

    # 2. Check artifacts
    status = check_artifacts()
    missing_sources = status["missing_sources"]
    missing_data = status["missing_data"]

    # 3. Reset tasks if source files are missing
    if missing_sources:
        reset_tasks_in_tasks_md(missing_sources)
    else:
        logger.info("Critical source files present. Skipping task reset.")

    # 4. Report status
    if missing_data:
        logger.warning(f"Missing data artifacts (pipeline may need re-run): {missing_data}")
    else:
        logger.info("All critical data artifacts present.")

    logger.info("Recovery & Reset complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()