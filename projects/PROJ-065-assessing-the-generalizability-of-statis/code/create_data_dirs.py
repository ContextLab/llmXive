"""Create required data directories for the project.

This script ensures that the following directories exist:
- data/raw/
- data/processed/

It uses the llmxive_toolkit `paths` helper which creates the
parent directories automatically.
"""
import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """Create the raw and processed data directories."""
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    log.info("Ensured raw data directory exists at %s", raw_dir)
    log.info("Ensured processed data directory exists at %s", processed_dir)
    # Print a concise confirmation for the caller / CI logs
    print(f"Created data directories: {raw_dir}, {processed_dir}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Failed to create data directories: %s", e)
        sys.exit(1)
