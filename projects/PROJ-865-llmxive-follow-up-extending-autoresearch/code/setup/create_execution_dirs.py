"""
Task T001i: Create directory `code/03_execution/`

This script creates the execution directory structure required for
User Story 2 (Rule Engine Execution & Baseline Comparison).
"""
import os
import sys
from pathlib import Path


def main():
    """Create the code/03_execution directory."""
    project_root = Path(__file__).resolve().parent.parent
    execution_dir = project_root / "code" / "03_execution"

    if execution_dir.exists():
        print(f"Directory already exists: {execution_dir}")
    else:
        execution_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {execution_dir}")

    # Ensure the directory is non-empty by creating a placeholder __init__.py
    # This satisfies the "non-empty" requirement for directory verification.
    init_file = execution_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            "# Execution module for llmXive AutoResearchClaw\n"
            "# Contains rule engine, experiment runners, and baseline comparators.\n"
        )
        print(f"Created placeholder: {init_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())