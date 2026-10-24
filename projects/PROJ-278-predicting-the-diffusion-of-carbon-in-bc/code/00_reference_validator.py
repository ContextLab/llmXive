"""Reference Validator Script

This script verifies that a given HuggingFace dataset URL corresponds to a
primary source (e.g., NIST or Materials Project) as required by
Constitution Principle II. It is used as a prerequisite step before the
raw data download (T009).

The verification logic is intentionally lightweight: it checks that the
provided URL points to a known, pre‑approved dataset identifier and that
the claimed source matches the approved mapping. If the check fails, a
`DataInsufficientError` is raised to halt the pipeline.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

# Import project‑specific utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from llmxive_toolkit import get_logger
from exceptions import DataInsufficientError

logger = get_logger(__name__)

# Mapping of approved dataset identifiers to their primary sources.
# This list can be extended as new verified datasets become available.
APPROVED_DATASETS = {
    "MeliDC/MeLiDC": "NIST",
    # Add other approved mappings here, e.g.,
    # "MaterialsProject/XYZ": "Materials Project",
}

def extract_dataset_id(url: str) -> str:
    """
    Extract the ``namespace/name`` identifier from a HuggingFace URL or
    return the string unchanged if it already looks like an identifier.

    Examples
    --------
    >>> extract_dataset_id("https://huggingface.co/datasets/MeliDC/MeLiDC")
    'MeliDC/MeLiDC'
    >>> extract_dataset_id("MeliDC/MeLiDC")
    'MeliDC/MeLiDC'
    """
    # If the input already matches the pattern ``owner/repo`` we keep it.
    if re.fullmatch(r"[^/]+/[^/]+", url.strip()):
        return url.strip()

    # Otherwise try to pull the identifier from a typical URL.
    match = re.search(r"datasets/([^/]+/[^/]+)", url)
    if match:
        return match.group(1)
    raise DataInsufficientError(f"Could not parse dataset identifier from URL: {url}")

def verify_dataset(dataset_id: str, source: str) -> None:
    """
    Verify that ``dataset_id`` is in the approved list and that the
    associated primary source matches ``source`` (case‑insensitive).

    Parameters
    ----------
    dataset_id : str
        The ``namespace/name`` identifier of the HuggingFace dataset.
    source : str
        The claimed primary source (e.g., ``NIST`` or ``Materials Project``).

    Raises
    ------
    DataInsufficientError
        If the dataset is not approved or the source does not match.
    """
    approved_source = APPROVED_DATASETS.get(dataset_id)
    if not approved_source:
        raise DataInsufficientError(
            f"Dataset '{dataset_id}' is not in the list of approved sources."
        )
    if approved_source.lower() != source.strip().lower():
        raise DataInsufficientError(
            f"Source mismatch for dataset '{dataset_id}': expected '{approved_source}', got '{source}'."
        )
    logger.info(
        f"Reference validation successful: dataset '{dataset_id}' matches source '{approved_source}'."
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that a HuggingFace dataset URL matches a primary source."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Full HuggingFace dataset URL or identifier (e.g., https://huggingface.co/datasets/MeliDC/MeLiDC).",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Primary source name to validate against (e.g., NIST, Materials Project).",
    )
    args = parser.parse_args()

    try:
        dataset_id = extract_dataset_id(args.url)
        logger.info(f"Extracted dataset identifier: {dataset_id}")
        verify_dataset(dataset_id, args.source)
    except DataInsufficientError as e:
        logger.error(f"Reference validation failed: {e}")
        # Re‑raise so the calling process can handle the failure.
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during reference validation: {e}")
        raise DataInsufficientError(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()