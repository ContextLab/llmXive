"""T016: Write harmonized dataset to data/processed/harmonized.parquet
and update checksums in the project state file.

Pipeline (User Story 1 final step):
1. Load synthetic noise and covariate data (chunked, memory-safe).
2. Clean traffic data (retain 0.0, exclude NaN rows).
3. Apply IQR outlier filter on decibel readings.
4. Aggregate noise metrics per day per grid cell.
5. Harmonize into a unified spatial grid (200m cells, WGS84).
6. Write data/processed/harmonized.parquet.
7. Update checksums via hygiene.compute_and_record_checksums().
"""

import logging
import sys
from pathlib import Path

# Ensure sibling modules in code/ are importable when run as a script.
_CODE_DIR = Path(__file__).resolve().parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums
from ingestion import load_synthetic_data_chunked, harmonize_spatial_data
from preprocessing import (
    clean_traffic_data,
    apply_iqr_filter,
    aggregate_daily_metrics,
)

logger = get_logger("harmonize_and_save")


def main():
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "harmonized.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading synthetic noise and covariate data (chunked)")
    noise_df, covariate_df = load_synthetic_data_chunked()
    logger.info(
        "Loaded noise_df with %d rows and covariate_df with %d rows",
        len(noise_df),
        len(covariate_df),
    )

    logger.info("Cleaning traffic data (retaining 0.0 values, excluding NaN)")
    covariate_df = clean_traffic_data(covariate_df)
    logger.info("Covariate rows after traffic cleaning: %d", len(covariate_df))

    logger.info("Applying IQR filter (1.5x IQR) to decibel readings")
    noise_df = apply_iqr_filter(noise_df, column="noise_level_db", k=1.5)
    logger.info("Noise rows after IQR filter: %d", len(noise_df))

    logger.info("Aggregating daily noise metrics per (grid_id, date)")
    noise_df = aggregate_daily_metrics(noise_df)
    logger.info("Rows after daily aggregation: %d", len(noise_df))

    logger.info("Harmonizing noise and covariate data into unified grid")
    harmonized_gdf = harmonize_spatial_data(noise_df, covariate_df)
    logger.info("Harmonized dataset contains %d rows", len(harmonized_gdf))

    if len(harmonized_gdf) == 0:
        raise RuntimeError(
            "Harmonized dataset is empty; refusing to write an empty parquet file."
        )

    logger.info("Writing harmonized dataset to %s", output_path)
    harmonized_gdf.to_parquet(output_path, index=False)
    logger.info("Wrote %s (%d bytes)", output_path, output_path.stat().st_size)

    logger.info("Updating checksums in project state file")
    state_record = compute_and_record_checksums(project_root=project_root)
    logger.info(
        "Checksums recorded for %d artifacts",
        len(state_record.get("checksums", {})),
    )

    logger.info("T016 complete: harmonized dataset written and checksummed")
    return output_path


if __name__ == "__main__":
    main()