import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def ensure_directories():
    """
    Create all required top‑level directories for the project.

    Required directories:
        - code/
        - data/raw/
        - data/processed/
        - results/
        - tests/unit/
        - tests/contract/
    """
    dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.results(),
        paths.tests("unit"),
        paths.tests("contract"),
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            log.debug(f"Ensured directory exists: {d}")
        except Exception as e:
            log.error(f"Failed to create directory {d}: {e}")
            raise
