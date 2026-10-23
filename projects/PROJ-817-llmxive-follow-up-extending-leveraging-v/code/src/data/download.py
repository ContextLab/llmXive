"""Download a real sample of InstructPix2Pix prompts (T001).

This script streams the public ``timbrooks/instruct-pix2pix`` training split
via ``datasets.load_dataset(..., streaming=True)``. It extracts the first
``N_PROMPTS`` rows that contain a non‑empty ``edit_prompt``. For each row a
stable SHA‑256 checksum over the identifying fields is computed and stored
alongside the prompt text.

The loader **fails loudly** (raises ``RuntimeError``) if fewer than the
requested number of prompts can be collected – there is no synthetic or
mock fallback. The output is written as a parquet file to
``data/raw/prompts_sample.parquet`` and a provenance JSON file is emitted
to ``data/raw/prompts_sample_provenance.json``.

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
# Verified dataset identifier on Hugging Face Hub (the correct repo name)
DATASET_ID = "timbrooks/instruct-pix2pix"
SPLIT = "train"
N_PROMPTS = 2000  # target number of prompts to collect

# Exported paths for tests and quick‑start
OUTPUT_PATH = paths.data("raw", "prompts_sample.parquet")
PROVENANCE_PATH = paths.data("raw", "prompts_sample_provenance.json")
# ----------------------------------------------------------------------


def _row_checksum(row: Mapping[str, object]) -> str:
    """Compute a stable SHA‑256 checksum for a source row.

    The checksum is over the JSON serialisation of the three fields that
    uniquely identify a prompt in the original dataset.
    """
    payload = json.dumps(
        {
            "edit_prompt": row.get("edit_prompt"),
            "original_prompt": row.get("original_prompt"),
            "edit_type": row.get("edit_type"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iter_stream_hf() -> Iterator[Mapping[str, object]]:
    """Yield rows from the HF streaming loader.

    Primary method uses the ``datasets`` library. If that fails (e.g. due
    to missing ``pyarrow``), it falls back to downloading the raw parquet
    shards via the Hugging Face Hub and reading them with ``fastparquet``.
    """
    try:
        from datasets import load_dataset

        log.info(
            "Attempting primary streaming load via datasets.load_dataset for %s/%s",
            DATASET_ID,
            SPLIT,
        )
        ds = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
        for row in ds:
            yield row
    except Exception as exc:  # pragma: no cover – exercised only on failure
        log.warning(
            "Primary HF streaming loader failed (%s); falling back to raw parquet shards",
            exc,
        )
        # Fallback: use huggingface_hub to download parquet shards
        try:
            from huggingface_hub import HfFileSystem, hf_hub_download
            import fastparquet

            fs = HfFileSystem()
            repo_path = f"{DATASET_ID}/{SPLIT}"
            files = fs.ls(repo_path)
            parquet_files = [
                f["name"]
                for f in files
                if f["type"] == "file" and f["name"].endswith(".parquet")
            ]
            if not parquet_files:
                raise RuntimeError(
                    f"No parquet files found in {repo_path} on the HF hub."
                )
            for hf_path in parquet_files:
                local_path = hf_hub_download(
                    repo_id=DATASET_ID,
                    filename=hf_path,
                    repo_type="dataset",
                )
                pf = fastparquet.ParquetFile(local_path)
                for df in pf.iter_row_groups():
                    for _, row in df.iterrows():
                        yield row.to_dict()
        except Exception as fallback_exc:  # pragma: no cover
            log.error("Fallback parquet‑shard loader also failed: %s", fallback_exc)
            raise RuntimeError(
                "Unable to stream dataset from Hugging Face (both primary and fallback failed)"
            ) from fallback_exc


def collect_prompt_sample(
    n_prompts: int = N_PROMPTS,
) -> pd.DataFrame:
    """Collect the first ``n_prompts`` valid prompts from the streaming source.

    A row is considered valid when ``edit_prompt`` is a non‑empty string.
    The function raises ``RuntimeError`` if the source yields fewer than
    ``n_prompts`` valid rows.
    """
    records: list[dict] = []
    scanned = 0

    try:
        row_iter = _iter_stream_hf()
    except Exception as exc:
        log.exception("Failed to open the streaming dataset")
        raise RuntimeError("Unable to stream the dataset") from exc

    for row in row_iter:
        scanned += 1
        prompt = row.get("edit_prompt")
        if not prompt or not str(prompt).strip():
            continue
        records.append(
            {
                "edit_prompt": str(prompt).strip(),
                "original_prompt": row.get("original_prompt"),
                "edit_type": row.get("edit_type"),
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

    df = pd.DataFrame(records[:n_prompts])
    if df["edit_prompt"].isna().any() or df["checksum"].isna().any():
        raise RuntimeError("Null prompt or checksum in collected sample.")
    if df["checksum"].duplicated().any():
        raise RuntimeError("Duplicate row checksums in collected sample.")

    log.info(
        "Successfully collected %d prompts from %d scanned rows",
        len(df),
        scanned,
    )
    df.attrs["source"] = "datasets.load_dataset streaming (or fallback parquet shards)"
    df.attrs["scanned_rows"] = scanned
    return df


def main() -> int:
    """Entry point for ``python -m code.src.data.download``."""
    df = collect_prompt_sample()

    # Write the parquet file using fastparquet (engine chosen for compatibility)
    output_path = OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, engine="fastparquet")
    log.info("Wrote %d rows to %s", len(df), output_path)

    # Write provenance information.
    provenance = {
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "streaming_rule": (
            "datasets.load_dataset streaming primary; fallback to HF parquet shards"
        ),
        "source_used": df.attrs["source"],
        "rows_scanned": df.attrs["scanned_rows"],
        "n_rows_written": int(len(df)),
        "n_prompts_target": N_PROMPTS,
        "checksum_algorithm": "sha256 over (edit_prompt, original_prompt, edit_type) JSON",
        "output_file": str(output_path),
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }
    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2))
    log.info("Wrote provenance to %s", PROVENANCE_PATH)

    # Observable check – read back using fastparquet.
    check = pd.read_parquet(output_path, engine="fastparquet")
    assert len(check) >= N_PROMPTS, "fewer than required prompts"
    assert check["edit_prompt"].notna().all(), "null prompts present"
    assert check["checksum"].notna().all(), "null checksums present"
    log.info(
        "Check passed: %d rows, all prompts and checksums non‑null",
        len(check),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
