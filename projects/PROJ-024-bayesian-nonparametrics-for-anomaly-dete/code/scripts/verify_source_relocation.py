"""
T108: Source Relocation Verification Script.

This script verifies that no .py files or subdirectories exist at the code/ root level.
It moves any remaining files to code/src/ subdirectories and generates a report.
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    project_root = Path(__file__).parent.parent.parent
    code_root = project_root / "code"
    src_root = code_root / "src"
    report_path = code_root / "src_structure_report.md"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Code root: {code_root}")
    logger.info(f"Src root: {src_root}")

    # Ensure src_root exists
    if not src_root.exists():
        logger.warning(f"Creating missing src directory: {src_root}")
        src_root.mkdir(parents=True, exist_ok=True)

    # Define target subdirectories based on existing structure
    subdirectories = [
        "models", "baselines", "data", "evaluation", 
        "services", "utils", "simulation", "scripts"
    ]
    
    for subdir in subdirectories:
        target_dir = src_root / subdir
        if not target_dir.exists():
            logger.info(f"Creating target subdirectory: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

    # Find all .py files at code/ root (maxdepth 1)
    py_files = list(code_root.glob("*.py"))
    py_dirs = [d for d in code_root.glob("*") if d.is_dir() and d.name not in ['src', '__pycache__', 'tests', 'scripts'] and not d.name.startswith('.')]

    moved_files = []
    moved_dirs = []
    errors = []

    # Move .py files
    for py_file in py_files:
        if py_file.name == "verify_source_relocation.py":
            # Skip this script itself
            continue
        
        logger.info(f"Moving file: {py_file.name}")
        try:
            # Determine target directory based on file name patterns
            target_subdir = None
            if "model" in py_file.name.lower():
                target_subdir = "models"
            elif "baseline" in py_file.name.lower():
                target_subdir = "baselines"
            elif "data" in py_file.name.lower():
                target_subdir = "data"
            elif "eval" in py_file.name.lower():
                target_subdir = "evaluation"
            elif "service" in py_file.name.lower():
                target_subdir = "services"
            elif "util" in py_file.name.lower():
                target_subdir = "utils"
            elif "sim" in py_file.name.lower():
                target_subdir = "simulation"
            else:
                # Default to scripts or utils
                target_subdir = "utils"
            
            target_path = src_root / target_subdir / py_file.name
            shutil.move(str(py_file), str(target_path))
            moved_files.append(f"{py_file.name} -> {target_subdir}/{py_file.name}")
            logger.info(f"Successfully moved {py_file.name} to {target_subdir}")
        except Exception as e:
            error_msg = f"Failed to move {py_file.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    # Move directories
    for py_dir in py_dirs:
        logger.info(f"Moving directory: {py_dir.name}")
        try:
            target_path = src_root / py_dir.name
            if target_path.exists():
                # Merge if target exists
                for item in py_dir.iterdir():
                    shutil.move(str(item), str(target_path / item.name))
                py_dir.rmdir()
            else:
                shutil.move(str(py_dir), str(target_path))
            moved_dirs.append(f"{py_dir.name} -> src/{py_dir.name}")
            logger.info(f"Successfully moved {py_dir.name}")
        except Exception as e:
            error_msg = f"Failed to move {py_dir.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    # Verification step: Run find command equivalent
    remaining_files = list(code_root.glob("*.py"))
    # Filter out self
    remaining_files = [f for f in remaining_files if f.name != "verify_source_relocation.py"]
    
    remaining_dirs = [d for d in code_root.glob("*") if d.is_dir() and d.name not in ['src', '__pycache__', 'tests', 'scripts'] and not d.name.startswith('.')]

    # Generate report
    report_lines = [
        "# Source Relocation Verification Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- Files moved: {len(moved_files)}",
        f"- Directories moved: {len(moved_dirs)}",
        f"- Remaining .py files at root: {len(remaining_files)}",
        f"- Remaining subdirectories at root: {len(remaining_dirs)}",
        "",
        "## Moved Files",
    ]
    
    for item in moved_files:
        report_lines.append(f"- {item}")
    
    report_lines.extend(["", "## Moved Directories"])
    for item in moved_dirs:
        report_lines.append(f"- {item}")
    
    if errors:
        report_lines.extend(["", "## Errors", ""])
        for err in errors:
            report_lines.append(f"- {err}")
    
    if remaining_files:
        report_lines.extend(["", "## Remaining Files (FAILED)", ""])
        for f in remaining_files:
            report_lines.append(f"- {f.name}")
    else:
        report_lines.extend(["", "## Verification Result", "✅ PASSED: No .py files remain at code/ root level"])
    
    if remaining_dirs:
        report_lines.extend(["", "## Remaining Directories (FAILED)", ""])
        for d in remaining_dirs:
            report_lines.append(f"- {d.name}")
    else:
        report_lines.append("✅ PASSED: No unexpected subdirectories remain at code/ root level")

    # Write report
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report saved to: {report_path}")

    # Assert constraint: output must be empty
    if remaining_files or remaining_dirs:
        logger.error("VERIFICATION FAILED: Items remain at root level")
        sys.exit(1)
    else:
        logger.info("VERIFICATION PASSED: Code structure compliant")
        sys.exit(0)

if __name__ == "__main__":
    main()
