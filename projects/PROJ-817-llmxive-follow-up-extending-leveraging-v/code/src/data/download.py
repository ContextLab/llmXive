"""Download a real sample of InstructPix2Pix prompts (T001).

This script streams a public InstructPix2Pix dataset from the Hugging Face Hub,
extracts the first ``N_PROMPTS`` rows that contain a non‑empty instruction prompt,
computes a stable SHA‑256 checksum for each row, and writes two artefacts:

1. ``data/raw/prompts_sample.parquet`` – a Parquet file with the collected rows.
2. ``data/raw/checksums_manifest.json`` – a JSON manifest mapping ``row_id`` to
   its checksum.

The loader **fails loudly** (raises ``RuntimeError``) if fewer than the requested
number of prompts can be collected – no synthetic fallback is performed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Iterator, Mapping

import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Primary dataset identifier on Hugging Face Hub.
PRIMARY_DATASET_ID = "timbrooks/instructpix2pix"
# Direct URL to the primary parquet shard to bypass Hub API 401 errors on some runners.
PRIMARY_PARQUET_URL = "https://huggingface.co/datasets/timbrooks/instructpix2pix/resolve/main/data/train-00000-of-00001.parquet"
SPLIT = "train"
N_PROMPTS = 2000  # target number of prompts to collect

# Exported paths (created automatically by ``paths`` helpers)
OUTPUT_PATH = paths.data("raw", "prompts_sample.parquet")
MANIFEST_PATH = paths.data("raw", "checksums_manifest.json")
# ----------------------------------------------------------------------


def _row_checksum(row: Mapping[str, object]) -> str:
    """Compute a stable SHA‑256 checksum for a source row.

    The checksum is over the JSON serialisation of the fields that uniquely
    identify a prompt in the original dataset.
    """
    # Handle different possible column names in the dataset
    edit_prompt = row.get("edit_prompt") or row.get("prompt") or ""
    original_prompt = row.get("original_prompt") or row.get("text") or ""
    payload = json.dumps(
        {
            "edit_prompt": edit_prompt,
            "original_prompt": original_prompt,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iter_stream_hf(dataset_id: str) -> Iterator[Mapping[str, object]]:
    """Yield rows from the HF streaming loader for a given ``dataset_id``.

    Tries the standard dataset loader first. If a 401/API error or Hub failure occurs,
    it falls back to reading the direct parquet URL via pandas to ensure reliability.
    """
    try:
        from datasets import load_dataset

        log.info(
            "Attempting streaming load via datasets.load_dataset for %s/%s",
            dataset_id,
            SPLIT,
        )
        ds = load_dataset(
            dataset_id,
            split=SPLIT,
            streaming=True,
            trust_remote_code=True,
        )
        for row in ds:
            yield row
    except Exception as exc:
        log.warning("Standard HF loader failed for %s: %s", dataset_id, exc)
        log.info("Attempting direct parquet load fallback for %s", dataset_id)
        try:
            # Use pandas to read the parquet file directly from the URL.
            # While this downloads the shard, it is the most robust way to bypass 
            # Hub API authentication/routing issues on restricted runners.
            df_shard = pd.read_parquet(PRIMARY_PARQUET_URL)
            for _, row in df_shard.iterrows():
                yield row.to_dict()
        except Exception as fallback_exc:
            log.error("Direct parquet load also failed: %s", fallback_exc)
            raise RuntimeError(
                f"Unable to fetch dataset {dataset_id} from Hugging Face via any method"
            ) from fallback_exc


def _collect_using_id(dataset_id: str, n_prompts: int) -> pd.DataFrame:
    """Collect ``n_prompts`` valid rows from ``dataset_id``."""
    records: list[dict] = []
    scanned = 0

    for row in _iter_stream_hf(dataset_id):
        scanned += 1
        # Accept a row if it contains a non‑empty instruction prompt.
        prompt = row.get("edit_prompt") or row.get("prompt")
        if not prompt or not str(prompt).strip():
            continue

        records.append(
            {
                "row_id": len(records),
                "edit_prompt": str(prompt).strip(),
                "original_prompt": row.get("original_prompt")
                or row.get("text")
                or "",
                "checksum": _row_checksum(row),
            }
        )
        if len(records) >= n_prompts:
            break

    if len(records) < n_prompts:
        raise RuntimeError(
            f"Collected only {len(records)} valid prompts (required {n_prompts}) "
            f"after scanning {scanned} rows from {dataset_id}."
        )
    return pd.DataFrame(records)


def collect_prompt_sample(n_prompts: int = N_PROMPTS) -> pd.DataFrame:
    """Collect the first ``n_prompts`` valid prompts."""
    return _collect_using_id(PRIMARY_DATASET_ID, n_prompts)


def main() -> int:
    """Entry point for ``python -m code.src.data.download``."""
    try:
        df = collect_prompt_sample()
    except RuntimeError as e:
        log.error("Data collection failed: %s", e)
        return 1

    # Ensure output directories exist
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write the parquet file
    df.to_parquet(OUTPUT_PATH, index=False)
    log.info("Wrote %d rows to %s", len(df), OUTPUT_PATH)

    # 2. Generate the checksums manifest (row_id -> checksum)
    manifest = df.set_index("row_id")["checksum"].to_dict()
    manifest_str = {str(k): v for k, v in manifest.items()}
    MANIFEST_PATH.write_text(json.dumps(manifest_str, indent=2))
    log.info("Wrote checksum manifest to %s", MANIFEST_PATH)

    # 3. Verify integrity
    check_df = pd.read_parquet(OUTPUT_PATH)
    assert len(check_df) >= N_PROMPTS, "Parquet contains fewer than required prompts"
    assert check_df["edit_prompt"].notna().all(), "Null edit_prompt present"
    assert check_df["checksum"].notna().all(), "Null checksums present"

    with open(MANIFEST_PATH, "r") as f:
        loaded_manifest = json.load(f)
    for _, row in check_df.iterrows():
        assert loaded_manifest[str(row["row_id"])] == row["checksum"], (
            f"Checksum mismatch for row {row['row_id']}"
        )

    log.info(
        "Verification passed: Parquet and manifest are consistent and complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())