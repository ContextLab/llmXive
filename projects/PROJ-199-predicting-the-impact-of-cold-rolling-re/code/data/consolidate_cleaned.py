"""
Consolidate all processed EBSD parquet files into a single cleaned dataset.

This script is part of task T015. It loads all intermediate parquet files
produced by the preprocessing step (code/data/preprocess.py) and writes a
consolidated Parquet file with the required metadata (material, reduction,
confidence) to ``data/processed/cleaned_ebsd.parquet``.
"""

import logging
from pathlib import Path

# The project’s package layout places the ``data`` package under ``code``.
# Import the helper functions that already exist in the code base.
from data.consolidate import (
    load_all_processed_datasets,
    write_consolidated_parquet,
)

# Configure a simple logger – the toolkit provides a ``get_logger`` helper,
# but the standard library logger is sufficient for this script.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Execute the consolidation workflow.

    1. Load all processed parquet files from the ``interim`` directory.
    2. Verify that the resulting DataFrame contains at least one row.
    3. Write the consolidated DataFrame to the canonical output location.
    4. Log a short summary for the user.

    Raises
    ------
    RuntimeError
        If the loaded DataFrame is empty (i.e. no valid EBSD points survived
        preprocessing). In this case the task must fail according to the
        specification.
    """
    logger.info("Starting consolidation of processed EBSD data.")
    df = load_all_processed_datasets()
    logger.info("Loaded %d rows from intermediate parquet files.", len(df))

    if df.empty:
        # According to T015 we must fail when there are zero valid rows.
        raise RuntimeError(
            "No valid EBSD rows after preprocessing; cleaned_ebsd.parquet will not be created."
        )

    # The helper defaults to the required output path.
    output_path: Path = write_consolidated_parquet(df)
    logger.info("Consolidated cleaned EBSD data written to %s", output_path)

    # Provide a quick summary of the material/reduction distribution.
    if "material" in df.columns and "reduction" in df.columns:
        summary = (
            df.groupby(["material", "reduction"])
            .size()
            .reset_index(name="rows")
        )
        logger.info("Data summary (material, reduction, rows):\n%s", summary)

if __name__ == "__main__":
    main()