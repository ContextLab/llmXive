import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories() -> List[Path]:
    """Create the required project directory structure."""
    base = Path.cwd()
    dirs = [
        base / "code" / "data_generation",
        base / "code" / "training",
        base / "code" / "evaluation",
        base / "code" / "utils",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "tests" / "unit",
        base / "tests" / "contract",
        base / "tests" / "integration",
        base / "specs" / "001-predict-stiffness-cnn" / "contracts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def create_init_files() -> List[Path]:
    """Create __init__.py files for all packages."""
    base = Path.cwd()
    init_paths = [
        base / "code" / "__init__.py",
        base / "code" / "data_generation" / "__init__.py",
        base / "code" / "training" / "__init__.py",
        base / "code" / "evaluation" / "__init__.py",
        base / "code" / "utils" / "__init__.py",
        base / "tests" / "__init__.py",
        base / "tests" / "unit" / "__init__.py",
        base / "tests" / "contract" / "__init__.py",
        base / "tests" / "integration" / "__init__.py",
    ]
    for p in init_paths:
        p.touch()
    return init_paths

def create_placeholder_files() -> List[Path]:
    """Create placeholder files as per task T006c."""
    base = Path.cwd()
    files = [
        base / "code" / "main.py",
        base / "code" / "data_generation" / "generate_microstructures.py",
        base / "code" / "data_generation" / "compute_stiffness.py",
        base / "code" / "training" / "model.py",
        base / "code" / "training" / "train.py",
        base / "code" / "evaluation" / "stats_utils.py",
        base / "code" / "evaluation" / "evaluate.py",
        base / "docs" / "constitution_amendment_proposal.md",
    ]
    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        if not f.exists():
            f.write_text("# Placeholder\n")
    return files

def verify_structure() -> Tuple[bool, str]:
    """Verify that all required directories and files exist."""
    base = Path.cwd()
    required_dirs = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts",
    ]
    missing_dirs = []
    for d in required_dirs:
        if not (base / d).is_dir():
            missing_dirs.append(d)

    required_files = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
        "code/main.py",
        "code/data_generation/generate_microstructures.py",
        "code/data_generation/compute_stiffness.py",
        "code/training/model.py",
        "code/training/train.py",
        "code/evaluation/stats_utils.py",
        "code/evaluation/evaluate.py",
        "docs/constitution_amendment_proposal.md",
    ]
    missing_files = []
    for f in required_files:
        if not (base / f).exists():
            missing_files.append(f)

    if missing_dirs or missing_files:
        msg = "Missing directories: " + ", ".join(missing_dirs) + "; " if missing_dirs else ""
        msg += "Missing files: " + ", ".join(missing_files)
        return False, msg
    return True, "All required directories and files verified."

def main() -> int:
    """Execute the project setup."""
    print("Creating project directories...")
    create_directories()
    print("Creating __init__.py files...")
    create_init_files()
    print("Creating placeholder files...")
    create_placeholder_files()
    print("Verifying structure...")
    success, msg = verify_structure()
    if success:
        print("SUCCESS: " + msg)
        return 0
    else:
        print("FAILURE: " + msg)
        return 1

if __name__ == "__main__":
    sys.exit(main())
