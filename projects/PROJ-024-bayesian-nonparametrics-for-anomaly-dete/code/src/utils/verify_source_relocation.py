"""
T108 Implementation: Source Relocation Verification.

This script verifies that no .py files exist at the code/ root level.
It moves any found files to code/src/ and generates a verification report.
"""
import os
import sys
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

def main():
    project_root = Path(__file__).parent.parent.parent
    code_root = project_root / "code"
    src_dir = code_root / "src"
    report_path = code_root / "src_structure_report.md"

    # Ensure src directory exists
    src_dir.mkdir(parents=True, exist_ok=True)

    # Find .py files at code/ root
    py_files = list(code_root.glob("*.py"))
    py_dirs = [d for d in code_root.iterdir() if d.is_dir() and d.name not in ['src', 'tests', 'scripts', '__pycache__']]

    moved_files = []
    moved_dirs = []
    errors = []

    # Move .py files
    for f in py_files:
        try:
            dest = src_dir / f.name
            shutil.move(str(f), str(dest))
            moved_files.append(f.name)
        except Exception as e:
            errors.append(f"Failed to move {f.name}: {str(e)}")

    # Move subdirectories (baselines, models, etc.) if they exist at root
    # Note: The task specifically mentions .py files, but we check for dirs too
    # based on the context of T113 which handles dirs.
    # For T108, we focus on .py files as per the task description.
    
    # Verification: Run the find command
    find_cmd = ["find", str(code_root), "-maxdepth", "1", "-name", "*.py", "-type", "f"]
    try:
        result = subprocess.run(find_cmd, capture_output=True, text=True, check=True)
        remaining_files = [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError as e:
        remaining_files = []
        errors.append(f"Find command failed: {e}")

    # Generate Report
    report_lines = [
        "# Source Relocation Verification Report (T108)",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Verification Command",
        f"`find code/ -maxdepth 1 -name '*.py' -type f`",
        "",
        "## Result",
    ]

    if remaining_files:
        report_lines.append("FAILED: The following files remain at code/ root:")
        for f in remaining_files:
            report_lines.append(f"- {f}")
        report_lines.append("")
        report_lines.append("## Action Taken")
        if moved_files:
            report_lines.append(f"Moved {len(moved_files)} files to code/src/:")
            for f in moved_files:
                report_lines.append(f"- {f}")
        else:
            report_lines.append("No files were moved (none found or all moved previously).")
    else:
        report_lines.append("PASSED: No .py files found at code/ root level.")
        report_lines.append("")
        if moved_files:
            report_lines.append("## Files Moved")
            for f in moved_files:
                report_lines.append(f"- {f}")
            report_lines.append("")
            report_lines.append("## Verification Status")
            report_lines.append("Constraint satisfied: `output.strip() == \"\"`")

    report_content = "\n".join(report_lines)
    
    # Write report
    with open(report_path, 'w') as f:
        f.write(report_content)

    print(report_content)

    if remaining_files:
        print(f"\nERROR: Verification failed. {len(remaining_files)} files remain.")
        sys.exit(1)
    else:
        print("\nSUCCESS: Source relocation verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
