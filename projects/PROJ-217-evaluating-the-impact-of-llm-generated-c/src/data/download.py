"""
src.data.download
-----------------
Downloads a deterministic sample of the CodeSearchNet Python dataset
(via the parquet-backed Hugging Face mirror ``codeparrot/code-search-net``),
writes each split sample to a local parquet file, verifies (or bootstraps)
SHA-256 checksums in ``data/artifact_hashes.yaml``, and writes:

* ``data/raw_snippets.jsonl`` – one record per valid snippet containing
  ``snippet_id``, ``code`` and ``human_comment``.
* ``data/excluded_records.json`` – records that were filtered out, each
  with a ``reason`` field.

Run via:
    python -m src.data.download

The script exits with a non-zero status if a recorded checksum does not
match, or if fewer than 50 valid snippets are found.
"""

import hashlib
import itertools
import json
import uuid
from pathlib import Path

import pandas as pd
import yaml
from datasets import load_dataset
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Real, programmatically-accessible source of the CodeSearchNet corpus
# (parquet-backed HF mirror; no dataset scripts, no synthetic fallback).
DATASET_REPO = "codeparrot/code-search-net"
DATASET_CONFIG = "python"
SPLITS = ["train", "validation", "test"]
MAX_RECORDS_PER_SPLIT = 200
MIN_VALID_SNIPPETS = 50


def _sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_expected_hashes() -> dict:
    """Load the expected parquet file hashes from ``data/artifact_hashes.yaml``."""
    hashes_file = paths.data("artifact_hashes.yaml")
    if not hashes_file.is_file():
        log.info(f"Hash manifest not found at {hashes_file}; initializing new manifest.")
        return {}
    with hashes_file.open() as f:
        data = yaml.safe_load(f) or {}
    return data


def _write_excluded(excluded: list, out_path: Path) -> None:
    """Write the list of excluded records as a pretty-printed JSON array."""
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(excluded, f, indent=2, ensure_ascii=False)


def _snippet_id(split: str, index: int) -> str:
    """Deterministic snippet id from the split name and record index."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"codesearchnet/{split}/{index}"))


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load expected checksums (may be an empty bootstrap manifest)
    # ------------------------------------------------------------------
    expected_hashes = _load_expected_hashes()
    manifest_updated = False

    # ------------------------------------------------------------------
    # 2. Prepare output paths
    # ------------------------------------------------------------------
    raw_path = paths.data("raw_snippets.jsonl")
    excluded_path = paths.data("excluded_records.json")
    hashes_file = paths.data("artifact_hashes.yaml")

    excluded_records = []
    valid_count = 0

    with raw_path.open("w", encoding="utf-8") as raw_file:
        # ------------------------------------------------------------------
        # 3. Stream each split, materialise a parquet file, verify checksum
        # ------------------------------------------------------------------
        for split in SPLITS:
            log.info(f"Streaming {split} split from {DATASET_REPO} ({DATASET_CONFIG})...")
            ds = load_dataset(
                DATASET_REPO, DATASET_CONFIG, split=split, streaming=True
            )
            records = list(
                tqdm(
                    itertools.islice(iter(ds), MAX_RECORDS_PER_SPLIT),
                    total=MAX_RECORDS_PER_SPLIT,
                    desc=f"Fetching {split}",
                )
            )

            # Materialise the fetched records as a parquet file so it can be
            # checksummed and archived as a source artifact.
            frame = pd.DataFrame(
                [
                    {
                        "func_name": r.get("func_name") or "",
                        "code": r.get("code") or "",
                        "docstring": r.get("docstring") or "",
                    }
                    for r in records
                ]
            )
            parquet_path = paths.data(f"{split}.parquet")
            frame.to_parquet(parquet_path, index=False, engine="pyarrow")

            # Verify SHA-256 against the manifest. On the very first run the
            # manifest is a bootstrap placeholder; we record the observed
            # checksum so every subsequent run is verified against it.
            actual_hash = _sha256(parquet_path)
            key = f"{split}.parquet"
            expected = expected_hashes.get(key)
            if expected is None:
                log.warning(
                    f"No recorded hash for {key}; bootstrapping manifest with "
                    f"observed checksum {actual_hash}"
                )
                expected_hashes[key] = actual_hash
                manifest_updated = True
            elif actual_hash != expected:
                log.error(
                    f"Checksum mismatch for {key} – expected {expected}, got {actual_hash}"
                )
                raise RuntimeError(f"Checksum verification failed for {key}")
            else:
                log.info(f"Checksum verified for {key}")

            # --------------------------------------------------------------
            # 4. Separate valid / invalid records
            # --------------------------------------------------------------
            for index, record in enumerate(records):
                code = record.get("code") or ""
                doc = record.get("docstring") or ""

                if not str(code).strip():
                    excluded_records.append(
                        {
                            "snippet_id": _snippet_id(split, index),
                            "code": code,
                            "human_comment": doc,
                            "reason": "missing_code",
                        }
                    )
                    continue
                if not str(doc).strip():
                    excluded_records.append(
                        {
                            "snippet_id": _snippet_id(split, index),
                            "code": code,
                            "human_comment": doc,
                            "reason": "invalid_docstring",
                        }
                    )
                    continue

                raw_file.write(
                    json.dumps(
                        {
                            "snippet_id": _snippet_id(split, index),
                            "code": code,
                            "human_comment": doc,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                valid_count += 1

    _write_excluded(excluded_records, excluded_path)

    if manifest_updated:
        with hashes_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                expected_hashes, f, default_flow_style=False, sort_keys=True
            )
        log.info(f"Updated hash manifest at {hashes_file}")

    # ------------------------------------------------------------------
    # 5. Final sanity check
    # ------------------------------------------------------------------
    if valid_count < MIN_VALID_SNIPPETS:
        log.error(
            f"Only {valid_count} valid snippets were extracted "
            f"(minimum required is {MIN_VALID_SNIPPETS})."
        )
        raise RuntimeError("Insufficient valid snippets")
    log.info(f"Successfully wrote {valid_count} valid snippets to {raw_path}")
    log.info(f"Wrote {len(excluded_records)} excluded records to {excluded_path}")


if __name__ == "__main__":
    main()