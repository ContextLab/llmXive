"""
Script to create the test directory skeletons required for T003.
This ensures `tests/unit/`, `tests/contract/`, and `tests/integration/` exist.
"""
import os
from pathlib import Path

def main():
    # Determine project root relative to this script location (code/)
    # Assuming this script is in code/, project root is parent of code/
    # However, per project structure, we are creating dirs relative to the project root
    # The task says: "Create `tests/unit/`, `tests/contract/`, `tests/integration/` directory skeletons"
    # Usually these are at the root of the repo or project.
    # Based on T001a, the project is PROJ-867... and we are inside it.
    # The standard convention is `tests/` at the root of the project.
    
    # Let's assume we are running from the project root or the script knows the root.
    # Since we are in `code/`, we go up one level to find the project root.
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    test_base = project_root / "tests"
    
    dirs_to_create = [
        test_base / "unit",
        test_base / "contract",
        test_base / "integration"
    ]
    
    created = []
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d.relative_to(project_root)))
        # Create a placeholder __init__.py to ensure they are treated as packages
        (d / "__init__.py").touch()
    
    print(f"Created test directories relative to {project_root}:")
    for d in created:
        print(f"  - {d}")

if __name__ == "__main__":
    main()
