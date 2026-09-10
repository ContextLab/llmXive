"""
Script to verify and enforce source file relocation (T113).
Moves any .py files or subdirectories (baselines, models, evaluation, data, services, utils)
from code/ root to code/src/ and generates a verification report.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    project_root = Path(__file__).parent.parent
    code_root = project_root / "code"
    src_dir = code_root / "src"
    report_path = project_root / "code" / "src_structure_report.md"

    # Ensure src directory exists
    src_dir.mkdir(parents=True, exist_ok=True)

    # Directories to move if found at root
    target_dirs = ["baselines", "models", "evaluation", "data", "services", "utils"]
    issues_found = []
    actions_taken = []

    # 1. Move .py files from code/ root to code/src/
    py_files = list(code_root.glob("*.py"))
    if py_files:
        issues_found.append(f"Found {len(py_files)} .py files at code/ root level.")
        for f in py_files:
            dest = src_dir / f.name
            shutil.move(str(f), str(dest))
            actions_taken.append(f"Moved {f.name} -> src/{f.name}")

    # 2. Move specific subdirectories from code/ root to code/src/
    for dir_name in target_dirs:
        dir_path = code_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            issues_found.append(f"Found directory '{dir_name}' at code/ root level.")
            dest = src_dir / dir_name
            # If dest exists, merge; otherwise move
            if dest.exists():
                # Merge contents
                for item in dir_path.iterdir():
                    shutil.move(str(item), str(dest / item.name))
                dir_path.rmdir()
                actions_taken.append(f"Merged contents of {dir_name}/ into src/{dir_name}/")
            else:
                shutil.move(str(dir_path), str(dest))
                actions_taken.append(f"Moved {dir_name}/ -> src/{dir_name}/")

    # 3. Verification: Run find commands
    find_py_cmd = ["find", str(code_root), "-maxdepth", "1", "-name", "*.py", "-type", "f"]
    find_dir_cmd = ["find", str(code_root), "-maxdepth", "1", "-type", "d", "-name", "baselines", "-o", "-name", "models", "-o", "-name", "evaluation", "-o", "-name", "data", "-o", "-name", "services", "-o", "-name", "utils"]

    py_output = subprocess.run(find_py_cmd, capture_output=True, text=True).stdout.strip()
    # Note: The second command logic in shell is complex, simpler to check existence in Python
    remaining_dirs = [d for d in target_dirs if (code_root / d).exists()]

    report_lines = [
        "# Source Relocation Verification Report (T113)",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Actions Taken",
    ]
    if actions_taken:
        for action in actions_taken:
            report_lines.append(f"- {action}")
    else:
        report_lines.append("- No files or directories required moving.")

    report_lines.extend([
        "",
        "## Verification Results",
        "",
        "### Python Files at Root",
        f"Command: `find code/ -maxdepth 1 -name '*.py' -type f`",
        f"Output: `{py_output if py_output else '(empty)'}`",
        f"Status: {'PASSED' if not py_output else 'FAILED'}",
        "",
        "### Subdirectories at Root",
        f"Remaining target dirs: {remaining_dirs if remaining_dirs else '(none)'}",
        f"Status: {'PASSED' if not remaining_dirs else 'FAILED'}",
        "",
        "## Summary",
    ])

    if not py_output and not remaining_dirs:
        report_lines.append("Constraint satisfied: No .py files or target subdirectories at code/ root level.")
    else:
        report_lines.append("Constraint VIOLATED: Files or directories remain at root level.")

    # Write report
    report_path.write_text("\n".join(report_lines))
    print(f"Report written to {report_path}")
    
    if py_output or remaining_dirs:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()