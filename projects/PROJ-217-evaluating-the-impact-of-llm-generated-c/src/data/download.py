"""
src.data.download
-----------------
Downloads the CodeSearchNet Python dataset, verifies SHA‑256 checksums,
extracts valid code snippets with their human docstrings, and writes two
JSON‑Lines files:

* ``data/raw_snippets.jsonl`` – one record per valid snippet containing
  ``snippet_id``, ``code`` and ``human_comment``.
* ``data/excluded_records.json`` – records that were filtered out, each
  with a ``reason`` field.

The script is intended to be run via:
    python -m src.data.download

It exits with a non‑zero status if any checksum does not match the
expected values in ``data/artifact_hashes.yaml`` or if fewer than 50
valid snippets are found.
"""

import hashlib
import json
import uuid
from pathlib import Path

import yaml
from datasets import load_dataset
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_expected_hashes() -> dict:
    """Load the expected parquet file hashes from ``data/artifact_hashes.yaml``."""
    hashes_file = paths.data("artifact_hashes.yaml")
    if not hashes_file.is_file():
        log.error(f"Missing hashes manifest: {hashes_file}")
        raise FileNotFoundError(str(hashes_file))
    with hashes_file.open() as f:
        return yaml.safe_load(f) or {}

def _write_excluded(excluded: list, out_path: Path) -> None:
    """Write the list of excluded records as a pretty‑printed JSON array."""
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(excluded, f, indent=2, ensure_ascii=False)

def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load expected checksums
    # ------------------------------------------------------------------
    expected_hashes = _load_expected_hashes()

    # ------------------------------------------------------------------
    # 2. Prepare output paths
    # ------------------------------------------------------------------
    raw_path = paths.data("raw_snippets.jsonl")
    excluded_path = paths.data("excluded_records.json")

    raw_file = raw_path.open("w", encoding="utf-8")
    excluded_records = []

    # ------------------------------------------------------------------
    # 3. Download each split, verify checksum, and extract snippets
    # ------------------------------------------------------------------
    dataset_name = "code_search_net"
    language = "python"
    splits = ["train", "validation", "test"]
    valid_count = 0

    for split in splits:
        log.info(f"Loading {split} split from the CodeSearchNet dataset...")
        # Load the split; this will download the parquet file under the hood.
        ds = load_dataset(dataset_name, language, split=split)

        # Store the split as parquet so we can checksum it
        parquet_path = paths.data(f"{split}.parquet")
        ds.to_parquet(parquet_path)

        # Verify SHA‑256
        actual_hash = _sha256(parquet_path)
        expected = expected_hashes.get(f"{split}.parquet")
        if expected is None:
            log.error(f"No expected hash entry for {split}.parquet in artifact_hashes.yaml")
            raise RuntimeError("Missing expected checksum")
        if actual_hash != expected:
            log.error(
                f"Checksum mismatch for {split}.parquet – expected {expected}, got {actual_hash}"
            )
            raise RuntimeError("Checksum verification failed")
        log.info(f"Checksum verified for {split}.parquet")

        # ------------------------------------------------------------------
        # 4. Iterate over records and separate valid / invalid entries
        # ------------------------------------------------------------------
        for record in tqdm(ds, desc=f"Processing {split}"):
            code = record.get("func_code")
            doc = record.get("docstring")

            # Normalise missing values
            if code is None:
                code = ""
            if doc is None:
                doc = ""

            # Determine validity
            if not code.strip() or not doc.strip():
                reason = "invalid_docstring" if not doc.strip() else "missing_code"
                snippet_id = str(uuid.uuid4())
                excluded_records.append(
                    {
                        "snippet_id": snippet_id,
                        "code": code,
                        "human_comment": doc,
                        "reason": reason,
                    }
                )
                continue

            # Valid record
            snippet_id = str(uuid.uuid4())
            raw_file.write(
                json.dumps(
                    {
                        "snippet_id": snippet_id,
                        "code": code,
                        "human_comment": doc,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            valid_count += 1

    raw_file.close()
    _write_excluded(excluded_records, excluded_path)

    # ------------------------------------------------------------------
    # 5. Final sanity check
    # ------------------------------------------------------------------
    if valid_count < 50:
        log.error(f"Only {valid_count} valid snippets were extracted (minimum required is 50).")
        raise RuntimeError("Insufficient valid snippets")
    log.info(f"Successfully wrote {valid_count} valid snippets to {raw_path}")
    log.info(f"Wrote {len(excluded_records)} excluded records to {excluded_path}")

if __name__ == "__main__":
    main()