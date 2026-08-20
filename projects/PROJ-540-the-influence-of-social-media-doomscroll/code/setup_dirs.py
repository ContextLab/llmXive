import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def create_directories() -> None:
    """Create the required directory structure."""
    dirs = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'specs'
    ]
    
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")

def main() -> None:
    """Main entry point."""
    create_directories()
    logger.info("Directory structure setup complete.")

if __name__ == "__main__":
    main()