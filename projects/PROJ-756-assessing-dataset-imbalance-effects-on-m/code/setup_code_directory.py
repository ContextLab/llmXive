import os
import sys
from pathlib import Path

def create_code_directory(base_path: Path) -> None:
    """
    Creates the code directory.
    Expected: code/
    """
    code_path = base_path / "code"
    code_path.mkdir(parents=True, exist_ok=True)
    print(f"Created code directory: {code_path}")

def main() -> None:
    project_root = Path.cwd()
    project_id = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    base_path = project_root / "projects" / project_id
    create_code_directory(base_path)

if __name__ == "__main__":
    main()
