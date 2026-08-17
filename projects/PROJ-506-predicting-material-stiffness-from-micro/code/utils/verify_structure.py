import sys
from pathlib import Path
from typing import List, Tuple

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

def main():
    """
    Main entry point to verify structure.
    """
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