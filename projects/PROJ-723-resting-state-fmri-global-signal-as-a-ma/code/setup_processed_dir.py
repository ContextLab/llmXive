"""T001c: Create the data/processed/ directory at the project root.

This is a scaffolding step for the analysis pipeline. All derived,
cleaned datasets (e.g. cleaned_data.csv, residuals.csv) are written
into data/processed/ by later tasks.
"""

from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def main() -> Path:
    processed_dir = paths.data("processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Keep a marker so the directory survives in version control.
    keep = processed_dir / ".gitkeep"
    if not keep.exists():
        keep.write_text("")
    log.info("Ensured directory exists: %s", processed_dir)
    print(f"Created/verified: {processed_dir}")
    return processed_dir


if __name__ == "__main__":
    main()