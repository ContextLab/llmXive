"""
src/pipeline/run.py
-------------------

This module provides the high‑level entry point for the project pipeline.
The ``run`` function orchestrates the end‑to‑end workflow required by the
quick‑start guide and the unit test ``code/tests/test_pipeline_entry.py``.
It performs the following steps:

1. **Download raw data** – uses ``src.data.download.main`` which either
   queries the Materials Project API (if ``MP_API_KEY`` is set) or falls
   back to a public CSV mirror.
2. **Featurise** – computes the twelve compositional descriptors and
   writes ``data/processed/features.csv`` together with the supporting
   logs.
3. **Validate** – runs a lightweight size/power check and writes
   ``data/processed/validation.log``.
4. **Train‑test split** – deterministic 80/20 split respecting the
   ``composition`` grouping, producing ``train.csv`` and ``test.csv``.
5. **Checksum generation** – calculates SHA‑256 digests for the raw and
   feature artefacts (delegated to ``src.utils.checksum_all``).

The function prints a concise success message that the quick‑start test
checks for and returns ``None`` on success.

The implementation deliberately avoids heavy model training or
evaluation to keep the pipeline fast for the CI test suite; those steps
are exercised in later tasks.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Pipeline sub‑steps
from src.data.download import main as download_main
from src.data.featurize import compute_features
from src.data.validate import main as validate_main
from src.models.split import split_dataset
from src.utils.checksum_all import main as checksum_all_main

log = get_logger(__name__)

def run() -> None:
    """
    Execute the full pipeline.

    Returns
    -------
    None
        The function prints a success message and returns ``None``.
    """
    # -----------------------------------------------------------------
    # 1️⃣  Download (or verify) the raw defect dataset.
    # -----------------------------------------------------------------
    raw_path = paths.data("raw", "materials_defects.csv")
    if not raw_path.is_file():
        log.info("Raw dataset not found – invoking download routine.")
        download_main()
    else:
        log.info(f"Raw dataset already present at {raw_path}")

    # -----------------------------------------------------------------
    # 2️⃣  Compute compositional descriptors.
    # -----------------------------------------------------------------
    features_path = paths.data("processed", "features.csv")
    compute_features(raw_path, features_path)

    # -----------------------------------------------------------------
    # 3️⃣  Validate the processed feature matrix.
    # -----------------------------------------------------------------
    validate_main()

    # -----------------------------------------------------------------
    # 4️⃣  Deterministic train‑test split (GroupShuffleSplit).
    # -----------------------------------------------------------------
    train_path = paths.data("processed", "train.csv")
    test_path = paths.data("processed", "test.csv")
    split_dataset(features_path, train_path, test_path)

    # -----------------------------------------------------------------
    # 5️⃣  Generate SHA‑256 checksums for the raw and feature files.
    # -----------------------------------------------------------------
    checksum_all_main()

    # -----------------------------------------------------------------
    # Completion message – required by the quick‑start integration test.
    # -----------------------------------------------------------------
    print("Pipeline completed successfully")
    log.info("Pipeline execution finished without errors.")
    return None

def main() -> None:
    """
    CLI entry point – ``python -m src.pipeline.run``.
    """
    try:
        run()
    except Exception as exc:
        log.error(f"Pipeline failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
