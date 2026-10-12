# Raw Data Directory

This directory stores the original, unmodified poll data files downloaded from verified sources.

- **Location**: `data/raw/`
- **Purpose**: Preserve the exact raw CSVs (or other formats) as they are retrieved.
- **Integrity**: Each file should be checksummed immediately after download; see `src.utils.state.record_hash`.
- **Do not edit**: Raw files must never be altered in place. All processing should read from here and write results to `data/processed/`.
