import os
import sys
from pathlib import Path

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")

def main() -> None:
    """Main entry point to ensure required data directories exist."""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Define directories to create
    directories = [
        "data/raw",
        "data/processed",
        "data/processed/plots"
    ]

    for dir_path in directories:
        ensure_dir(dir_path)
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Placeholder to ensure directory is tracked by git\n")
            logging.info(f"Created .gitkeep in: {dir_path}")
        else:
            logging.info(f".gitkeep already exists in: {dir_path}")

    logging.info("Directory setup complete.")

if __name__ == "__main__":
    main()