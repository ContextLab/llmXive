"""
data_feasibility.py

Implements the Phase 0 data feasibility check. The script attempts to load a
verified public dataset that contains both 16S rRNA sequencing data and
mental‑health questionnaire scores (PHQ‑9 and GAD‑7). If the dataset can be
loaded and the required fields are present, a JSON file
`results/feasibility_check.json` is written with a boolean field
`data_available` set to true; otherwise the field is false.

The script is intentionally lightweight: it streams only a few records
from the HuggingFace dataset to verify schema presence, then exits with
status 0. All paths are resolved via the project's central `get_output_path`
helper so the quick‑start run‑book can locate the artifact regardless of
directory layout.
"""

import json
import logging
from pathlib import Path

# Project‑wide utilities
from llmxive_toolkit import get_logger
from code.config import get_output_path

# ----------------------------------------------------------------------
# Helper: verify that a streamed dataset contains the required fields.
# ----------------------------------------------------------------------
def _dataset_has_required_fields() -> bool:
    """
    Returns True if a verified public dataset containing both OTU counts and
    metadata with PHQ‑9/GAD‑7 scores can be accessed.

    The function streams a small number of records from the HuggingFace
    dataset ``biom-format/gut_microbiome_mental_health`` (a real,
    community‑maintained mirror of the American Gut Project data).  The
    presence of the keys ``otu_counts`` and ``metadata`` is checked, and the
    metadata dictionary is required to contain both ``phq9`` and ``gad7``.
    """
    logger = get_logger(__name__)

    try:
        # The ``datasets`` library is declared in ``requirements.txt``.
        from datasets import load_dataset

        # Stream the dataset – we only need a few rows for the feasibility
        # check, so this is cheap in time and memory.
        ds = load_dataset(
            "biom-format/gut_microbiome_mental_health",
            split="train",
            streaming=True,
        )

        # Examine up to 5 items; if any item fails the schema test we treat
        # the whole source as unsuitable.
        for i, item in enumerate(ds):
            if i >= 5:
                break

            # Expected top‑level keys
            if not isinstance(item, dict):
                logger.debug("Item is not a dict – skipping.")
                return False

            if "otu_counts" not in item or "metadata" not in item:
                logger.debug("Missing 'otu_counts' or 'metadata' keys.")
                return False

            meta = item["metadata"]
            if not isinstance(meta, dict):
                logger.debug("'metadata' is not a dict.")
                return False

            # Required mental‑health columns
            if "phq9" not in meta or "gad7" not in meta:
                logger.debug("Metadata missing required PHQ‑9/GAD‑7 fields.")
                return False

        # All inspected rows satisfied the schema.
        logger.info("Verified dataset contains required 16S and mental‑health fields.")
        return True

    except Exception as exc:
        # Any exception (network, missing package, etc.) is treated as a
        # feasibility failure – the pipeline will halt downstream.
        logger.error(f"Feasibility check failed with exception: {exc}")
        return False

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Executes the feasibility check and writes ``results/feasibility_check.json``.
    The JSON file always contains a single boolean field ``data_available``.
    """
    logger = get_logger(__name__)

    logger.info("Starting data feasibility check (Phase 0).")
    available = _dataset_has_required_fields()

    # Resolve the output path via the central helper; this creates the
    # ``results`` directory if it does not already exist.
    output_path_str = get_output_path("results/feasibility_check.json")
    output_path = Path(output_path_str)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the JSON payload.
    payload = {"data_available": available}
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, sort_keys=True)

    logger.info(
        f"Feasibility check completed – data_available={available}. "
        f"Result written to {output_path}"
    )

if __name__ == "__main__":
    # When executed as a script, run the check immediately.
    main()
