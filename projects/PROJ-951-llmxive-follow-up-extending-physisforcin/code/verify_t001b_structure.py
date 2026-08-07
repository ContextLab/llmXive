import os
from pathlib import Path

def print_tree(root: Path, prefix: str = ""):
    """Recursively prints the directory tree."""
    contents = sorted(root.iterdir())
    pointers = [None] * len(contents)
    for i, c in enumerate(contents):
        if i == len(contents) - 1:
            pointers[i] = "└── "
            extension = "    "
        else:
            pointers[i] = "├── "
            extension = "│   "
        
        print(f"{prefix}{pointers[i]}{c.name}")
        if c.is_dir():
            print_tree(c, prefix + extension)

def verify_t001b_structure(project_root: Path) -> bool:
    """
    Verifies that the required T001b directories exist:
    - src/
    - tests/
    - data/
    
    Returns True if all exist, False otherwise.
    """
    required_dirs = ["src", "tests", "data"]
    all_exist = True
    
    print(f"Verifying T001b structure at: {project_root}")
    print("-" * 40)
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"[OK] {dir_path} exists")
        else:
            print(f"[MISSING] {dir_path} does not exist")
            all_exist = False
    
    print("-" * 40)
    if all_exist:
        print("T001b Verification: PASSED")
    else:
        print("T001b Verification: FAILED")
    
    return all_exist

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        root = Path.cwd()
    
    verify_t001b_structure(root)
