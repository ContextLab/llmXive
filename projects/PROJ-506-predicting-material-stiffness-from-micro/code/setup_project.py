import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories() -> Tuple[bool, List[str]]:
    """
    Create the required project directory structure.
    Returns (success, list of created paths).
    """
    base = Path(".")
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

    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
        else:
            created.append(str(d)) # Already exists, count as created for verification

    return True, created

def create_init_files() -> Tuple[bool, List[str]]:
    """
    Create __init__.py files for all Python packages.
    """
    base = Path(".")
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

    created = []
    for p in init_paths:
        if not p.exists():
            p.touch()
        created.append(str(p))
    return True, created

def create_placeholder_files() -> Tuple[bool, List[str]]:
    """
    Create placeholder files as specified in T006c.
    """
    base = Path(".")
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

    created = []
    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        if not f.exists():
            f.touch()
        created.append(str(f))
    return True, created

def print_tree_structure(root_path: Path) -> str:
    """
    Generate a string representation of the directory tree.
    """
    lines = []
    for path in sorted(root_path.rglob("*")):
        if path.is_file():
            lines.append(f"  {path}")
        else:
            lines.append(f"  {path}/")
    return "\n".join(lines)

def check_structure() -> Tuple[bool, str]:
    """
    Verify the expected directory structure exists.
    Returns (success, output_string).
    """
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

    base = Path(".")
    missing = []
    for d in required_dirs:
        if not (base / d).exists():
            missing.append(d)

    output = print_tree_structure(base)

    if missing:
        return False, f"Missing directories: {missing}\n{output}"
    return True, output

def main():
    """
    Main entry point to setup the project structure.
    """
    print("Creating directories...")
    success, paths = create_directories()
    if not success:
        print("Failed to create directories.")
        sys.exit(1)
    print(f"Created/Verified: {len(paths)} paths.")

    print("Creating __init__.py files...")
    success, paths = create_init_files()
    if not success:
        print("Failed to create init files.")
        sys.exit(1)
    print(f"Created/Verified: {len(paths)} init files.")

    print("Creating placeholder files...")
    success, paths = create_placeholder_files()
    if not success:
        print("Failed to create placeholder files.")
        sys.exit(1)
    print(f"Created/Verified: {len(paths)} placeholder files.")

    print("Verifying structure...")
    success, tree_output = check_structure()
    if not success:
        print("Structure verification FAILED.")
        print(tree_output)
        sys.exit(1)

    print("Structure verification PASSED.")
    print("\nDirectory Tree:")
    print(tree_output)
    sys.exit(0)

if __name__ == "__main__":
    main()
