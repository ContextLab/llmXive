"""
verify_plan.py

This script verifies that the project's plan.md file contains a line with a dataset
source URL. It is used as a guard step for the pipeline to ensure that a real data
source has been recorded before downstream tasks run.

If a URL line is missing, the script exits with a non‑zero status code and prints an
error message, causing the task to be considered failed.
"""

import re
import sys
from pathlib import Path

def _has_dataset_url(plan_path: Path) -> bool:
    """
    Scan the given plan.md file for a line that appears to contain a dataset URL.

    A line is considered a dataset URL line if it contains a substring matching
    a simple HTTP/HTTPS URL pattern (e.g., ``http://example.com`` or
    ``https://example.org``). The function returns ``True`` if at least one such
    line is found, otherwise ``False``.
    """
    url_pattern = re.compile(r"https?://\S+")
    try:
        with plan_path.open("r", encoding="utf-8") as f:
            for line in f:
                if url_pattern.search(line):
                    return True
    except FileNotFoundError:
        # If the plan file does not exist, we treat this as a failure.
        return False
    return False

def main() -> None:
    """
    Entry point for the verification script.

    The script expects ``plan.md`` to be located at the repository root. It checks
    for the presence of a dataset URL line and exits with status ``0`` if found,
    otherwise prints an error and exits with status ``1``.
    """
    project_root = Path(__file__).resolve().parents[1]  # repository root
    plan_md = project_root / "plan.md"

    if not plan_md.is_file():
        sys.stderr.write(f"Error: plan.md not found at expected location: {plan_md}\\n")
        sys.exit(1)

    if _has_dataset_url(plan_md):
        # Success – URL line present.
        sys.stdout.write("Dataset source URL found in plan.md.\\n")
        sys.exit(0)
    else:
        sys.stderr.write(
            "Error: No dataset source URL line detected in plan.md. "
            "Please add a line containing the dataset URL (e.g., "
            "'Dataset URL: https://...') and re‑run the pipeline.\\n"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()