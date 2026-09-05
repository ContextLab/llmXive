import os
from pathlib import Path

def main():
    """Initialize project directory structure and configuration files."""
    project_root = Path(__file__).parent

    # Define directories
    directories = [
        "code/src/analysis",
        "code/src/data",
        "code/src/utils",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        "code/data",
        "code/analysis/results",
        "code/docs",
        "code/contracts",
    ]

    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if "src" in dir_path or "tests" in dir_path:
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("")

    # Create .gitkeep files for data directories
    data_dirs = ["code/data", "code/analysis/results"]
    for dir_path in data_dirs:
        gitkeep = project_root / dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    print("Project structure initialized successfully.")

if __name__ == "__main__":
    main()
