"""
Script to establish the standard project layout for the research pipeline.
It ensures that all required top‑level directories exist:
  - code/
  - data/raw/
  - data/processed/
  - state/
  - docs/
The script is idempotent and can be run safely multiple times.
"""
import logging
from llmxive_toolkit import paths, get_logger

# Set up a logger that writes to the standard output (no file needed here)
log = get_logger(__name__)  # optional: get_logger(__name__, log_file="logs/run.log")

def ensure_project_layout() -> None:
    """
    Create the essential directories for the project if they do not already exist.
    """
    # Define the directories we need
    required_dirs = [
        paths.code(),                     # <project>/code/
        paths.data("raw"),                # <project>/data/raw/
        paths.data("processed"),          # <project>/data/processed/
        paths.state(),                    # <project>/state/
        paths.docs()                      # <project>/docs/
    ]

    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"Ensured directory exists: {d}")

if __name__ == "__main__":
    ensure_project_layout()
