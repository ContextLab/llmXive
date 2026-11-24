"""
T006 – Download the Stack Overflow “Tech Stack” taxonomy from the verified HuggingFace dataset
and write it to ``data/taxonomy/survey_2023.json``.

The script follows the “fail loudly” policy:
* If the target file already exists and its SHA‑256 matches the published checksum,
  the script exits successfully without re‑downloading.
* Otherwise it streams the ``stack-exchange/stackoverflow-tags`` dataset from HuggingFace,
  extracts the unique tag names, writes a well‑formed JSON file, and verifies the checksum.
* Any mismatch between the computed checksum and the published value raises an error,
  causing the pipeline to fail loudly.

The published checksum is taken from the repository’s current ``data/taxonomy/survey_2023.json``
(SHA‑256 ``b32d843c60537f7b23e2b43f50186f1c9f14a364d128a2fa677e38c6c0d628ab``).
"""

import sys
import json
import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# The logger is optional but useful for debugging in CI runs.
log = get_logger(__name__)

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
# Published checksum of the correct taxonomy file (as stored in the repo).
PUBLISHED_SHA256 = (
    "b32d843c60537f7b23e2b43f50186f1c9f14a364d128a2fa677e38c6c0d628ab"
)
# HuggingFace dataset that contains the Stack Overflow tag taxonomy.
HF_DATASET_ID = "stack-exchange/stackoverflow-tags"
# The split name – the dataset provides a single split named "train".
HF_SPLIT = "train"

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_existing_checksum(file_path: Path) -> str | None:
    """Return the checksum of *file_path* if it exists, else ``None``."""
    if file_path.is_file():
        return compute_sha256(file_path)
    return None

def write_taxonomy(tags: set[str], output_path: Path) -> None:
    """Write the taxonomy JSON file to *output_path*."""
    taxonomy = {"tags": sorted(tags)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2, ensure_ascii=False)

# -------------------------------------------------------------------------
# Main download logic
# -------------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the taxonomy download script.

    Returns:
        int: 0 on success, non‑zero on failure.
    """
    output_path = paths.data("taxonomy", "survey_2023.json")
    log.info(f"Target taxonomy file: {output_path}")

    # -----------------------------------------------------------------
    # 1. If the file already exists and matches the published checksum,
    #    we are done.
    # -----------------------------------------------------------------
    existing_checksum = load_existing_checksum(output_path)
    if existing_checksum:
        log.info(f"Existing file checksum: {existing_checksum}")
        if existing_checksum == PUBLISHED_SHA256:
            log.info("Existing taxonomy file matches the published checksum – nothing to do.")
            return 0
        else:
            log.warning(
                "Existing taxonomy file checksum differs from the published value. "
                "It will be overwritten with the authoritative dataset."
            )

    # -----------------------------------------------------------------
    # 2. Stream the dataset from HuggingFace.
    # -----------------------------------------------------------------
    try:
        from datasets import load_dataset
    except Exception as exc:
        log.error(f"Failed to import the 'datasets' library: {exc}")
        raise RuntimeError("The 'datasets' package is required for taxonomy download.") from exc

    log.info(f"Loading HuggingFace dataset '{HF_DATASET_ID}' (split='{HF_SPLIT}') in streaming mode...")
    try:
        ds = load_dataset(
            HF_DATASET_ID,
            split=HF_SPLIT,
            streaming=True,
            trust_remote_code=False,
        )
    except Exception as exc:
        log.error(f"Failed to load dataset from HuggingFace: {exc}")
        raise RuntimeError("Unable to load the Stack Overflow tag taxonomy from HuggingFace.") from exc

    # -----------------------------------------------------------------
    # 3. Extract unique tag names.
    #    The dataset may expose the tag under different field names;
    #    we handle the common possibilities.
    # -----------------------------------------------------------------
    tags: set[str] = set()
    for idx, record in enumerate(ds):
        # The record is expected to be a mapping.
        if isinstance(record, dict):
            # Known possible keys (checked in order of likelihood).
            for key in ("tag", "tag_name", "name"):
                if key in record and isinstance(record[key], str):
                    tags.add(record[key].strip().lower())
                    break
        else:
            # Unexpected format – skip but log the first occurrence.
            if idx == 0:
                log.warning(
                    f"Unexpected record format from the dataset: {type(record)}. "
                    "Skipping records that are not mappings."
                )
        # Periodic progress logging (every 100 k records).
        if (idx + 1) % 100_000 == 0:
            log.info(f"Processed {idx + 1} records, collected {len(tags)} unique tags so far...")

    if not tags:
        raise RuntimeError("No tags were extracted from the HuggingFace taxonomy dataset.")

    log.info(f"Extracted {len(tags)} unique tags from the dataset.")

    # -----------------------------------------------------------------
    # 4. Write the taxonomy JSON.
    # -----------------------------------------------------------------
    write_taxonomy(tags, output_path)
    log.info(f"Taxonomy written to {output_path}")

    # -----------------------------------------------------------------
    # 5. Verify checksum against the published value.
    # -----------------------------------------------------------------
    new_checksum = compute_sha256(output_path)
    log.info(f"Computed SHA‑256 of the new file: {new_checksum}")

    if new_checksum != PUBLISHED_SHA256:
        # The checksum mismatch is considered a fatal error because the
        # file no longer matches the authoritative reference.
        error_msg = (
            f"Checksum mismatch: expected {PUBLISHED_SHA256}, got {new_checksum}. "
            "The downloaded taxonomy does not match the published reference."
        )
        log.error(error_msg)
        raise RuntimeError(error_msg)

    log.info("Checksum verification passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
