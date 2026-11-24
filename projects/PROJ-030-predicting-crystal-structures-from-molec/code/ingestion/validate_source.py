"""
Module: code/ingestion/validate_source.py

Purpose:
Validate the HuggingFace dataset citation and accessibility before processing.
Implements the Reference-Validator integration (Constitution Principle II).

This script checks that the dataset metadata retrieved from HuggingFace
contains an expected citation string that matches the primary source for the
COD organic subset. The result of the validation is written to
`data/validation/source_validation.json`.  If the validation fails or the
dataset cannot be reached, the script exits with a non‑zero status and
logs the error.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

# Ensure the project root is on the import path so that sibling modules can be imported.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_validation, ensure_directory
from logging_config import get_logger, log_event
from exceptions import CitationVerificationError, SourceUnreachableError

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Expected citation snippet – this is a minimal check that the dataset
# metadata references the Crystallography Open Database.  In a full
# implementation this would be a DOI or exact citation string.
EXPECTED_CITATION_SNIPPET = "Crystallography Open Database"
# Output file name (as required by the task specification)
VALIDATION_OUTPUT_PATH = get_path_validation() / "source_validation.json"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_dataset_metadata(dataset_name: str) -> Dict[str, Any]:
    """
    Fetches metadata for the dataset from HuggingFace.

    Args:
        dataset_name (str): The name of the dataset on HuggingFace.

    Returns:
        Dict[str, Any]: A dictionary with selected metadata fields.

    Raises:
        SourceUnreachableError: If the dataset cannot be accessed.
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        info = api.dataset_info(dataset_name)

        # Extract a subset of fields that are useful for citation verification.
        metadata = {
            "id": info.id,
            "author": info.author,
            "description": info.description,
            "tags": info.tags,
            "last_modified": info.last_modified,
            "cardData": info.cardData,
            "citation": getattr(info, "citation", None)  # Some datasets expose a citation field.
        }
        return metadata
    except Exception as exc:
        logger.error(f"Unable to retrieve metadata for dataset '{dataset_name}': {exc}")
        raise SourceUnreachableError(
            f"Failed to fetch metadata for dataset '{dataset_name}'."
        ) from exc

def verify_citation(dataset_name: str, metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifies that the dataset citation matches the expected primary source.

    The verification follows a simple heuristic:
    * The metadata must contain a non‑empty ``id`` field.
    * The ``citation`` field (if present) or the ``description`` must contain
      the ``EXPECTED_CITATION_SNIPPET`` string (case‑insensitive).

    Args:
        dataset_name (str): The name of the dataset.
        metadata (Dict[str, Any]): The metadata dictionary obtained from HuggingFace.

    Returns:
        Tuple[bool, str]: ``(is_valid, message)`` where ``is_valid`` indicates
        whether the citation check passed.
    """
    if not metadata.get("id"):
        return False, "Dataset metadata missing required 'id' field."

    # Prefer an explicit citation field; fall back to description.
    citation_text: Optional[str] = metadata.get("citation") or metadata.get("description")
    if not citation_text:
        return False, "No citation or description found in dataset metadata."

    if EXPECTED_CITATION_SNIPPET.lower() in citation_text.lower():
        return True, "Citation verification succeeded."
    else:
        return (
            False,
            f"Citation does not contain expected reference to '{EXPECTED_CITATION_SNIPPET}'."
        )

def save_validation_result(
    dataset_name: str,
    is_valid: bool,
    message: str,
    metadata: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Writes the validation result to ``output_path`` as JSON.

    The JSON structure matches the task specification and includes a
    timestamp for reproducibility.

    Args:
        dataset_name (str): Dataset identifier.
        is_valid (bool): Result of the validation.
        message (str): Human‑readable message.
        metadata (Dict[str, Any]): Full dataset metadata.
        output_path (Path): Destination file path.
    """
    ensure_directory(output_path.parent)

    validation_record = {
        "dataset_name": dataset_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "is_valid": is_valid,
        "message": message,
        "metadata": metadata
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validation_record, f, indent=2, ensure_ascii=False)

    logger.info(f"Source validation record written to {output_path}")

# ----------------------------------------------------------------------
# Core validation routine
# ----------------------------------------------------------------------
def validate_source(dataset_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Perform the full validation workflow.

    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: ``(is_valid, metadata)``.
        ``metadata`` is ``None`` only when the dataset could not be reached.
    """
    try:
        metadata = get_dataset_metadata(dataset_name)
        is_valid, message = verify_citation(dataset_name, metadata)

        # Persist the result.
        save_validation_result(
            dataset_name,
            is_valid,
            message,
            metadata,
            VALIDATION_OUTPUT_PATH
        )

        # Log the event for downstream audit.
        if is_valid:
            log_event("source_validated", {"dataset": dataset_name, "message": message})
        else:
            log_event("source_validation_failed", {"dataset": dataset_name, "message": message})

        return is_valid, metadata

    except SourceUnreachableError as exc:
        logger.error(f"Source unreachable: {exc}")
        raise  # Propagate so the CLI can exit with a non‑zero status
    except Exception as exc:
        logger.error(f"Unexpected error during source validation: {exc}")
        raise CitationVerificationError(
            f"Unexpected error during validation of dataset '{dataset_name}': {exc}"
        ) from exc

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the HuggingFace COD organic dataset citation and accessibility."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Full HuggingFace dataset identifier (e.g., 'crystallography-open-database/organic')."
    )
    args = parser.parse_args()

    try:
        is_valid, _ = validate_source(args.dataset)
        if is_valid:
            print(f"Validation successful for dataset '{args.dataset}'.")
            sys.exit(0)
        else:
            print(f"Validation failed for dataset '{args.dataset}'. See log for details.")
            sys.exit(1)
    except Exception as exc:
        print(f"Validation error: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
