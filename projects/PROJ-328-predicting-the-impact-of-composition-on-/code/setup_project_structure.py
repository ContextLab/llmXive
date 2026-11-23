import os
import sys
import logging
from pathlib import Path

def setup_directories(root_path: Path) -> None:
    """
    Create the required directory structure for the project.
    This function is idempotent (safe to run multiple times).
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
    ]

    for dir_path in directories:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists in Python package directories
        if dir_path.startswith("code/") or dir_path.startswith("tests/"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

def verify_directory_structure(root_path: Path) -> bool:
    """
    Verify that all required directories exist.
    Returns True if all directories exist, False otherwise.
    """
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
    ]

    all_exist = True
    for dir_path in required_dirs:
        full_path = root_path / dir_path
        if not full_path.exists():
            logging.error(f"Missing required directory: {full_path}")
            all_exist = False
        elif not full_path.is_dir():
            logging.error(f"Path exists but is not a directory: {full_path}")
            all_exist = False

    return all_exist

def main():
    """
    Main entry point for directory setup and verification.
    """
    # Determine project root (assume script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # First, setup directories if they don't exist
    logger.info(f"Setting up directories at: {project_root}")
    setup_directories(project_root)

    # Then verify the structure
    logger.info("Verifying directory structure...")
    if verify_directory_structure(project_root):
        logger.info("✅ All required directories exist.")

        # Print the directory tree for verification (simulating ls -R)
        logger.info("\nDirectory structure verification (simulating 'ls -R'):")
        print("\n--- data/ ---")
        for item in sorted((project_root / "data").rglob("*")):
            if item.is_dir():
                print(f"{item.relative_to(project_root)}/")
            else:
                print(f"  {item.relative_to(project_root)}")

        print("\n--- code/ ---")
        for item in sorted((project_root / "code").rglob("*")):
            if item.is_dir():
                print(f"{item.relative_to(project_root)}/")
            else:
                print(f"  {item.relative_to(project_root)}")

        print("\n--- tests/ ---")
        for item in sorted((project_root / "tests").rglob("*")):
            if item.is_dir():
                print(f"{item.relative_to(project_root)}/")
            else:
                print(f"  {item.relative_to(project_root)}")

        return 0
    else:
        logger.error("❌ Directory structure verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())