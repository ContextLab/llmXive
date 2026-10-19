"""
src/pipeline/run.py
-------------------

Entry point for the end‑to‑end defect formation energy pipeline.

This implementation orchestrates the full data‑processing pipeline:
1. Download the raw defect dataset (if not already present).
2. Compute its SHA‑256 checksum (Constitution‑III, T015).
3. Compute compositional descriptors.
4. Check for missing descriptor values (FR‑006).
5. Compute a checksum for the processed feature matrix (Constitution‑III, T016).
6. Validate the resulting feature matrix (size & power analysis).
7. Print a success message.

Future steps (model training, evaluation, etc.) will be added in later tasks.
"""

from llmxive_toolkit import get_logger, paths

from src.data.download import main as _download_main
from src.featurize import main as _featurize_main
from src.data.validate import main as _validate_main
from src.utils.check_descriptor_gaps import check_descriptor_gaps
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def main() -> None:
    """Run the pipeline."""
    # Step 1: ensure raw data is available
    try:
        _download_main()
    except SystemExit as e:
        # If the download script exited with an error message (e.g., missing API key),
        # we allow the pipeline to continue only if the raw CSV already exists.
        raw_path = paths.data("raw", "materials_defects.csv")
        if not raw_path.is_file():
            raise
    # Step 2: compute checksum for the raw dataset (T015)
    raw_path = paths.data("raw", "materials_defects.csv")
    checksum_path = paths.data("checksums", "raw_defects.sha256")
    compute_checksum(raw_path, checksum_path)

    # Step 3: compute features
    processed_features_path = paths.data("processed", "features.csv")
    _featurize_main(
        str(raw_path),
        str(processed_features_path),
    )

    # Step 4: descriptor gap check (FR‑006)
    try:
        check_descriptor_gaps()
    except RuntimeError as exc:
        # Abort the pipeline with a clear message.
        log.error(str(exc))
        raise SystemExit(str(exc))

    # Step 5: compute checksum for the processed feature matrix (T016)
    features_checksum_path = paths.data("checksums", "features.sha256")
    compute_checksum(processed_features_path, features_checksum_path)

    # Step 6: validate the feature matrix
    _validate_main()

    # Final success message
    message = "Pipeline completed successfully"
    print(message)
    log.info(message)

if __name__ == "__main__":
    main()