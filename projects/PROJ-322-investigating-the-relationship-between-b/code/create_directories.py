"""
Script to create the required project directory structure:
- code/
- data/raw/
- data/processed/
- data/results/
- tests/
This script is idempotent and can be run multiple times without error.
"""
import logging
from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

def ensure_directories():
    """
    Ensure that all required top‑level directories exist.
    """
    required_dirs = [
        paths.code(),                     # <project>/code
        paths.data("raw"),                # <project>/data/raw
        paths.data("processed"),          # <project>/data/processed
        paths.data("results"),            # <project>/data/results
        paths.tests()                     # <project>/tests
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory exists: {d}")

def main():
    """
    Entry point for the script when executed directly.
    """
    logging.basicConfig(level=logging.INFO)
    ensure_directories()
    log.info("All required directories are now present.")

if __name__ == "__main__":
    main()
