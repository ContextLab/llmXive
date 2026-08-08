import os
import sys
from pathlib import Path

def create_artifacts_directory(base_path: Path) -> None:
    """
    Creates the artifacts directory.
    Expected: artifacts/
    """
    artifacts_path = base_path / "artifacts"
    artifacts_path.mkdir(parents=True, exist_ok=True)
    print(f"Created artifacts directory: {artifacts_path}")

def main() -> None:
    project_root = Path.cwd()
    project_id = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    base_path = project_root / "projects" / project_id
    create_artifacts_directory(base_path)

if __name__ == "__main__":
    main()
