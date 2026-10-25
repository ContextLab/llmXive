import sys
from pathlib import Path

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# The QM9 dataset as hosted on HuggingFace
DATASET_NAME = "deepchem/qm9"

# Columns that must be present according to the original QM9 publication
REQUIRED_COLUMNS = {"smiles", "homo"}


def download_and_verify() -> None:
    """
    Download the QM9 dataset from HuggingFace, verify that the required columns
    (SMILES and HOMO) are present, and persist the dataset as a parquet file for
    downstream steps.

    Raises:
        RuntimeError: If the dataset cannot be downloaded or required columns are
                      missing.
    """
    log.info(f"Loading QM9 dataset '{DATASET_NAME}' from HuggingFace")
    try:
        ds = load_dataset(DATASET_NAME)
    except Exception as exc:
        log.error(f"Failed to load dataset: {exc}")
        raise RuntimeError("Could not download QM9 dataset") from exc

    # The dataset contains splits (train/validation/test). For schema verification we
    # only need to inspect one split; the first one is sufficient.
    split_name = next(iter(ds))
    dataset = ds[split_name]

    missing = REQUIRED_COLUMNS - set(dataset.column_names)
    if missing:
        raise RuntimeError(
            f"QM9 dataset is missing required columns: {', '.join(sorted(missing))}"
        )
    log.info("All required columns are present in the QM9 dataset.")

    # Persist the full dataset to a parquet file for later pipeline stages.
    out_path: Path = paths.data("raw", "qm9.parquet")
    log.info(f"Saving QM9 dataset to {out_path}")
    dataset.to_parquet(str(out_path))
    log.info("Download and verification completed successfully.")


if __name__ == "__main__":
    download_and_verify()
