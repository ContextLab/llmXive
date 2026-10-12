"""
Script to create the required data storage hierarchy and README files.
This fulfills task T004 by ensuring that `data/raw/` and `data/processed/`
exist and contain a small README.md in each directory.
The platform owns the `state/` directory, so no files are written there.
"""

import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


RAW_README_CONTENT = """# Raw Data Directory

This directory stores the original, unmodified poll data files downloaded from verified sources.

- **Location**: `data/raw/`
- **Purpose**: Preserve the exact raw CSVs (or other formats) as they are retrieved.
- **Integrity**: Each file should be checksummed immediately after download; see `src.utils.state.record_hash`.
- **Do not edit**: Raw files must never be altered in place. All processing should read from here and write results to `data/processed/`.
"""

PROCESSED_README_CONTENT = """# Processed Data Directory

This directory holds all derived datasets produced by the pipeline.

- `poll_data_cleaned.csv` – Harmonized poll records with weekly bins and placeholder columns.
- `historical_weights.csv` – Pollster‑specific RMSE‑based weights.
- `frequentist_forecasts.csv` – Simple and weighted average forecasts.
- `bayesian_forecasts.csv` – Posterior mean forecasts with 95 % credible intervals.
- Additional evaluation files (metrics, meta‑analysis results, etc.).

Files in this folder are version‑controlled via SHA‑256 hashes recorded in
`state/projects/PROJ-206-statistical-analysis-of-publicly-availab.yaml`.
"""


def write_readme(path_obj, content):
    """Write the README file, creating parent directories as needed."""
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(content, encoding="utf-8")
    log.info(f"Wrote README to {path_obj}")


def main():
    """Create hierarchy and README files."""
    # Create raw data README
    raw_readme_path = paths.data("raw", "README.md")
    write_readme(raw_readme_path, RAW_README_CONTENT)

    # Create processed data README
    processed_readme_path = paths.data("processed", "README.md")
    write_readme(processed_readme_path, PROCESSED_README_CONTENT)

    log.info("Data hierarchy creation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
