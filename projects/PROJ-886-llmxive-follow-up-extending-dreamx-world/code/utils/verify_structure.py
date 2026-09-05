import os
import logging
from pathlib import Path
import subprocess

def main():
    """
    Verification script for T001.
    Runs `ls -R` on the project directory and checks for the existence
    of the 15 required directories.
    """
    project_root = Path("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world")
    
    required_dirs = [
        "data/raw",
        "data/derived",
        "data/derived/videos",
        "code",
        "code/models",
        "code/pipeline",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "logs",
        "docs",
        "config"
    ]

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 1

    # Run ls -R
    try:
        result = subprocess.run(
            ["ls", "-R", str(project_root)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run ls -R: {e}")
        print(e.stderr)
        return 1

    # Verify directories
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing_dirs.append(str(full_path))

    if missing_dirs:
        logger.error(f"Missing required directories: {missing_dirs}")
        return 1

    logger.info("All required directories verified successfully.")
    return 0

if __name__ == "__main__":
    exit(main())