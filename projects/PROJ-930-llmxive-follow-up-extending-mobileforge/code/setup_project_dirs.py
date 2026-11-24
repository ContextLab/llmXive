import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    """
    Creates the full directory tree required for the study as specified in T001.
    """
    # Define the required directory structure relative to project root
    # Based on T001 requirements:
    # code/{data/raw, data/processed, data/evaluation, models, utils, tests/unit, tests/integration}
    # data/
    # outputs/
    required_dirs = [
        "code/data/raw",
        "code/data/processed",
        "code/data/evaluation",
        "code/models",
        "code/utils",
        "code/tests/unit",
        "code/tests/integration",
        "data",
        "outputs",
    ]

    root = paths.root
    created_count = 0

    for dir_rel_path in required_dirs:
        target_path = root / dir_rel_path
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            log.info(f"Ensured directory exists: {dir_rel_path}")
            created_count += 1
        except Exception as e:
            log.error(f"Failed to create directory {dir_rel_path}: {e}")
            return 1

    log.info(f"Successfully ensured {created_count} directories exist.")
    return 0

if __name__ == "__main__":
    exit(main())