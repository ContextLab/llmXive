#!/usr/bin/env python3
"""
create_project_skeleton.py

Creates the required project directory skeleton for
PROJ-756-assessing-dataset-imbalance-effects-on-m with placeholder
files (__init__.py, .gitkeep, run.sh).

Execution of this script satisfies task T001.
"""
import sys
from pathlib import Path

def main() -> None:
    """
    Build the directory layout and placeholder files.
    """
    # Base project directory
    base_dir = Path("projects/PROJ-756-assessing-dataset-imbalance-effects-on-m")
    subdirs = [
        "data",
        "code",
        "tests",
        "artifacts",
        "results",
        "state",
        "logs",
    ]

    # Create base directory
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py to make the directory a Python package
    (base_dir / "__init__.py").write_text("", encoding="utf-8")

    # Create a minimal run.sh script
    run_sh_content = (
        "#!/usr/bin/env bash\\n"
        "# Placeholder run script for the project\\n"
        "set -e\\n"
        "echo \"Run script placeholder\"\\n"
    )
    run_sh_path = base_dir / "run.sh"
    run_sh_path.write_text(run_sh_content, encoding="utf-8")
    # Make it executable
    run_sh_path.chmod(0o755)

    # Create subdirectories and a .gitkeep in each
    for sub in subdirs:
        sub_path = base_dir / sub
        sub_path.mkdir(parents=True, exist_ok=True)
        # .gitkeep ensures the folder is tracked even if empty
        (sub_path / ".gitkeep").write_text("", encoding="utf-8")

    print(f"Project skeleton created at {base_dir}", file=sys.stderr)

if __name__ == "__main__":
    main()