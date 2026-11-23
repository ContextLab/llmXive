import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project artifacts.
    This includes data/, models/, reports/, and logs/ at the root,
    and subdirectories under code/ if they don't exist.
    """
    # Define directories relative to project root
    root = Path(__file__).resolve().parent.parent
    directories = [
        root / "data",
        root / "models",
        root / "reports",
        root / "logs",
        root / "code" / "data",
        root / "code" / "features",
        root / "code" / "models",
        root / "code" / "analysis",
        root / "tests" / "unit",
        root / "tests" / "contract",
        root / "tests" / "integration",
    ]

    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        # Ensure .gitkeep exists to prevent empty directory removal
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    return created

def main():
    created_dirs = setup_directories()
    print(f"Created directories: {created_dirs}")

if __name__ == "__main__":
    main()