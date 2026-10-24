"""Download a real sample of InstructPix2Pix prompts (T001).

This script streams the public ``timbrooks/instruct-pix2pix`` 
training split via ``datasets.load_dataset(..., streaming=True)``. 
It extracts the first ``N_PROMPTS`` rows that contain a non‑empty 
``edit_prompt``. For each row a stable SHA‑256 checksum over the 
identifying fields is computed.

The loader **fails loudly** (raises ``RuntimeError``) if fewer than the
requested number of prompts can be collected – there is no synthetic
or mock fallback. The output is written as a parquet file to
``data/raw/prompts_sample.parquet`` and a checksum manifest is emitted
to ``data/raw/checksums_manifest.json``.

The script is intended to be run from the project root as:
    python -m code.src.data.download
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
# Verified dataset identifier on Hugging Face Hub
DATASET_ID = "timbrooks/instruct-pix2pix"
SPLIT = "train"
N_PROMPTS = 2000  # target number of prompts to collect

# Exported paths
OUTPUT_PATH = paths.data("raw", "prompts_sample.parquet")
MANIFEST_PATH = paths.data("raw", "checksums_manifest.json")
# ----------------------------------------------------------------------


def _row_checksum(row: Mapping[str, object]) -> str:
    """Compute a stable SHA‑256 checksum for a source row.

    The checksum is over the JSON serialisation of the fields
    that uniquely identify a prompt in the original dataset.
    """
    # Use 'edit_prompt' and 'original_prompt' as identifying fields
    payload = json.dumps(
        {
            "edit_prompt": row.get("edit_prompt"),
            "original_prompt": row.get("original_prompt"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iter_stream_hf() -> Iterator[Mapping[str, object]]:
    """Yield rows from the HF streaming loader using the verified recipe."""
    try:
        from datasets import load_dataset

        log.info(
            "Streaming load via datasets.load_dataset for %s/%s",
            DATASET_ID,
            SPLIT,
        )
        ds = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
        for row in ds:
            yield row
    except Exception as exc:
        log.error("HF streaming loader failed: %s", exc)
        raise RuntimeError(
            f"Unable to stream dataset {DATASET_ID} from Hugging Face"
        ) from exc


def collect_prompt_sample(n_prompts: int = N_PROMPTS) -> pd.DataFrame:
    """Collect the first ``n_prompts`` valid prompts from the streaming source.

    A row is considered valid when ``edit_prompt`` is a non‑empty string.
    """
    records: list[dict] = []
    scanned = 0

    for row in _iter_stream_hf():
        scanned += 1
        prompt = row.get("edit_prompt")
        if not prompt or not str(prompt).strip():
            continue

        records.append(
            {
                "row_id": len(records),
                "edit_prompt": str(prompt).strip(),
                "original_prompt": row.get("original_prompt"),
                "checksum": _row_checksum(row),
            }
        )
        if len(records) >= n_prompts:
            break

    if len(records) < n_prompts:
        raise RuntimeError(
            f"Collected only {len(records)} valid prompts (required {n_prompts}); "
            f"stream ended after scanning {scanned} rows."
        )

    df = pd.DataFrame(records)
    log.info(
        "Successfully collected %d prompts from %d scanned rows", len(df), scanned
    )
    return df


def main() -> int:
    """Entry point for ``python -m code.src.data.download``."""
    try:
        df = collect_prompt_sample()
    except RuntimeError as e:
        log.error("Data collection failed: %s", e)
        return 1

    # 1. Write the parquet file using pyarrow (default)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)  # engine defaults to pyarrow
    log.info("Wrote %d rows to %s", len(df), OUTPUT_PATH)

    # 2. Generate the checksums manifest (row_id -> checksum)
    manifest = df.set_index("row_id")["checksum"].to_dict()
    manifest_str = {str(k): v for k, v in manifest.items()}
    MANIFEST_PATH.write_text(json.dumps(manifest_str, indent=2))
    log.info("Wrote checksum manifest to %s", MANIFEST_PATH)

    # 3. Observable verification
    check_df = pd.read_parquet(OUTPUT_PATH)
    assert len(check_df) >= N_PROMPTS, "Parquet contains fewer than required prompts"
    assert check_df["edit_prompt"].notna().all(), "Null edit_prompt present"
    assert check_df["checksum"].notna().all(), "Null checksums present"

    # Verify manifest matches parquet
    with open(MANIFEST_PATH, "r") as f:
        loaded_manifest = json.load(f)
    for _, row in check_df.iterrows():
        assert loaded_manifest[str(row["row_id"])] == row["checksum"], (
            f"Checksum mismatch for row {row['row_id']}"
        )

    log.info(
        "Verification passed: Parquet and Manifest are consistent and complete."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
