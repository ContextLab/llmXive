"""
download.py
-------------
Discover and verify a real paired microbiome‑serology dataset.

This script attempts to locate an open‑access dataset that contains both
16S OTU abundances and influenza serology measurements.  The primary
source is the Hugging‑Face Hub dataset named ``influenza_microbiome``.
If the dataset cannot be accessed or does not contain the required
columns, the script falls back to a synthetic‑data flag.

The result is written to ``data/research/sra_status.json`` with the
following schema:

{
    "status": "real_data_found" | "no_real_data",
    "use_synthetic": bool,
    "accession": <NCBI SRA accession string | null>,
    "hf_dataset_id": <HuggingFace dataset identifier | null>
}

The verification step in ``tasks.md`` only checks that the keys
``status`` and ``use_synthetic`` exist, but we also include the optional
identifiers for downstream scripts.
"""

import json
import sys
from pathlib import Path

# llmxive toolkit helpers for consistent path handling
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# The Hugging‑Face ``datasets`` library is not part of the default
# environment; it is declared in ``requirements.txt``.
try:
    from datasets import load_dataset
except ImportError as exc:
    logger.error("The 'datasets' package is required but not installed.")
    raise

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {"subject_id", "titer_baseline", "titer_post"}
TAXON_PREFIX = "taxon_"  # any column starting with this is considered a taxon
HF_DATASET_ID = "influenza_microbiome"
HF_SPLIT = "train"


def dataset_has_required_columns(sample: dict) -> bool:
    """
    Verify that a sample from the HF dataset contains the mandatory columns
    and at least one taxon abundance column.
    """
    if not REQUIRED_COLUMNS.issubset(sample.keys()):
        logger.debug(
            "Missing mandatory columns. Required=%s, present=%s",
            REQUIRED_COLUMNS,
            sample.keys(),
        )
        return False

    taxon_cols = [c for c in sample.keys() if c.startswith(TAXON_PREFIX)]
    if not taxon_cols:
        logger.debug("No taxon columns found with prefix %s", TAXON_PREFIX)
        return False

    return True


def discover_hf_dataset() -> dict:
    """
    Attempt to load the HF dataset in streaming mode and validate its schema.
    Returns a dictionary with discovery information on success, otherwise
    raises an exception.
    """
    logger.info("Attempting to load HF dataset '%s' (streaming).", HF_DATASET_ID)
    ds = load_dataset(HF_DATASET_ID, split=HF_SPLIT, streaming=True)

    # Pull the first record to inspect its fields.
    try:
        first_record = next(iter(ds))
    except StopIteration:
        raise RuntimeError("HF dataset is empty.") from None

    if not dataset_has_required_columns(first_record):
        raise RuntimeError("HF dataset does not contain the required columns.")

    logger.info("HF dataset '%s' verified successfully.", HF_DATASET_ID)
    return {
        "status": "real_data_found",
        "use_synthetic": False,
        "accession": None,
        "hf_dataset_id": HF_DATASET_ID,
    }


def fallback_to_synthetic() -> dict:
    """
    Return a minimal status dict indicating that no suitable real dataset
    could be located; downstream pipelines will switch to synthetic mode.
    """
    logger.warning(
        "No suitable real paired microbiome‑serology dataset found. "
        "Falling back to synthetic data."
    )
    return {
        "status": "no_real_data",
        "use_synthetic": True,
        "accession": None,
        "hf_dataset_id": None,
    }


def write_status_file(status_dict: dict) -> None:
    """
    Write the discovery result to ``data/research/sra_status.json``.
    The directory hierarchy is created automatically by ``paths.data``.
    """
    out_path = paths.data("research", "sra_status.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the JSON is pretty‑printed for readability.
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(status_dict, fp, indent=2, sort_keys=True)

    logger.info("Wrote discovery status to %s", out_path)


def main() -> None:
    """
    Entry point for the script.  It first tries the HF dataset; if any step
    fails, it records a synthetic‑fallback status.
    """
    try:
        status = discover_hf_dataset()
    except Exception as exc:  # noqa: BLE001 (broad on purpose for discovery)
        logger.debug("HF discovery failed: %s", exc, exc_info=True)
        status = fallback_to_synthetic()

    write_status_file(status)


if __name__ == "__main__":
    # ``python code/download.py`` is the canonical way to run this step.
    # Any exception propagates to the caller (CI runner) so that a failure
    # is visible and not silently ignored.
    main()
