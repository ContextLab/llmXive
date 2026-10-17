"""Dataset acquisition for the density-supervision study (FR-001).

Downloads and streams the GSM8K train and test splits and a logical reasoning dataset
(filtered from ``bigbench_lite``) and persists real raw snapshots under ``data/raw/``.
Writes a manifest describing identifiers, sample sizes, and byte sizes.

This implementation strictly uses the HuggingFace ``datasets`` library.
If any download fails, a RuntimeError is raised to ensure no synthetic data is used.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from itertools import islice
from pathlib import Path
from typing import Iterable, List

from datasets import load_dataset
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Real, publicly downloadable HuggingFace dataset identifiers.
GSM8K_ID = "openai/gsm8k"
GSM8K_CONFIG = "main"
BIGBENCH_ID = "bigbench_lite"

# Sample limits (as required by the task)
SAMPLE_LIMITS = {
    "train": 2000,
    "test": 500,
    "bigbench_logical": 500,
}

_BYTES_PER_GB = 1024 ** 3
_MAX_TOTAL_BYTES = 7 * _BYTES_PER_GB

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _materialize_stream(
    iterable: Iterable[dict], limit: int
) -> List[dict]:
    """Consume at most ``limit`` items from a streaming dataset and return a list."""
    return list(islice(iterable, limit))

def _snapshot_to_jsonl(data: List[dict], out_path: Path) -> int:
    """Write a list of dictionaries to a JSONL file; return the number of rows written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in data:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    n = len(data)
    if n == 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"No rows were written to {out_path}")
    log.info("Wrote %d rows to %s", n, out_path)
    return n

def _fmt_size(nbytes: float) -> str:
    if nbytes >= _BYTES_PER_GB:
        return f"{nbytes / _BYTES_PER_GB:.3f} GB"
    return f"{nbytes / (1024 ** 2):.3f} MB"

# ----------------------------------------------------------------------
# Public loader functions
# ----------------------------------------------------------------------
def load_gsm8k(split: str = "test", streaming: bool = True) -> List[dict]:
    """Load a limited sample from the GSM8K dataset.

    Parameters
    ----------
    split: str
        Either ``"train"`` or ``"test"``.
    streaming: bool
        Kept for API compatibility; the function always streams internally.

    Returns
    -------
    List[dict]
        A list containing at most ``SAMPLE_LIMITS[split]`` rows.

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched or an unsupported split is requested.
    """
    if split not in {"train", "test"}:
        raise RuntimeError(f"Unsupported GSM8K split '{split}'. Use 'train' or 'test'.")

    limit = SAMPLE_LIMITS[split]
    try:
        ds = load_dataset(
            GSM8K_ID,
            GSM8K_CONFIG,
            split=split,
            streaming=True,
        )
        log.info("Streaming GSM8K %s split (limit %d)", split, limit)
        return _materialize_stream(ds, limit)
    except Exception as exc:
        raise RuntimeError(f"Failed to load GSM8K dataset {GSM8K_ID}: {exc}") from exc

def load_bigbench_lite() -> List[dict]:
    """Load a logical‑deduction subset from ``bigbench_lite``.

    The function streams the full ``bigbench_lite`` dataset, filters for the
    ``logical_deduction`` task, and returns the first ``SAMPLE_LIMITS['bigbench_logical']``
    examples as a list.

    Returns
    -------
    List[dict]
        A list of logical‑deduction examples (max 500 rows).

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched or the filtering yields no rows.
    """
    limit = SAMPLE_LIMITS["bigbench_logical"]
    try:
        ds = load_dataset(BIGBENCH_ID, streaming=True)
        log.info("Streaming bigbench_lite dataset for logical deduction (limit %d)", limit)

        # The dataset entries contain a ``task`` field naming the benchmark.
        filtered = (
            row for row in ds if str(row.get("task", "")).lower() == "logical_deduction"
        )
        materialized = _materialize_stream(filtered, limit)
        if not materialized:
            raise RuntimeError(
                "Logical deduction subset of bigbench_lite yielded zero rows."
            )
        return materialized
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load logical deduction subset from {BIGBENCH_ID}: {exc}"
        ) from exc

# ----------------------------------------------------------------------
# Download & manifest generation
# ----------------------------------------------------------------------
def download_all(raw_dir: Path | None = None) -> Path:
    """Stream required datasets, snapshot them under ``data/raw/``, and write a manifest.

    The function creates three snapshot files:
    - ``gsm8k_train.jsonl``
    - ``gsm8k_test.jsonl``
    - ``bigbench_logical_deduction.jsonl``

    Returns
    -------
    Path
        Path to the written ``manifest.txt`` file.
    """
    raw_dir = raw_dir or paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Paths for the snapshots
    gsm8k_train_path = raw_dir / "gsm8k_train.jsonl"
    gsm8k_test_path = raw_dir / "gsm8k_test.jsonl"
    logical_path = raw_dir / "bigbench_logical_deduction.jsonl"

    # Load and snapshot GSM8K train
    train_data = load_gsm8k(split="train")
    n_train = _snapshot_to_jsonl(train_data, gsm8k_train_path)

    # Load and snapshot GSM8K test
    test_data = load_gsm8k(split="test")
    n_test = _snapshot_to_jsonl(test_data, gsm8k_test_path)

    # Load and snapshot logical deduction subset
    logical_data = load_bigbench_lite()
    n_logical = _snapshot_to_jsonl(logical_data, logical_path)

    # Compute sizes
    size_train = gsm8k_train_path.stat().st_size
    size_test = gsm8k_test_path.stat().st_size
    size_logical = logical_path.stat().st_size
    total = size_train + size_test + size_logical

    if total > _MAX_TOTAL_BYTES:
        raise RuntimeError(
            f"Total raw dataset size {total} bytes exceeds the 7 GB budget"
        )

    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Raw data manifest (generated by code/data.py)",
        f"generated_utc: {now}",
        "",
        f"dataset_1: {GSM8K_ID} (config={GSM8K_CONFIG}, split=train)",
        f"  snapshot_file: {gsm8k_train_path.name}",
        f"  rows: {n_train}",
        f"  size_bytes: {size_train}",
        f"  size_human: {_fmt_size(size_train)}",
        "",
        f"dataset_2: {GSM8K_ID} (config={GSM8K_CONFIG}, split=test)",
        f"  snapshot_file: {gsm8k_test_path.name}",
        f"  rows: {n_test}",
        f"  size_bytes: {size_test}",
        f"  size_human: {_fmt_size(size_test)}",
        "",
        f"dataset_3: {BIGBENCH_ID} (logical_deduction subset)",
        f"  snapshot_file: {logical_path.name}",
        f"  rows: {n_logical}",
        f"  size_bytes: {size_logical}",
        f"  size_human: {_fmt_size(size_logical)}",
        "",
        f"total_size_bytes: {total}",
        f"total_size_human: {_fmt_size(total)}",
        "budget_limit: 7 GB",
        "within_budget: true",
    ]
    manifest = raw_dir / "manifest.txt"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Manifest written to %s (total %s)", manifest, _fmt_size(total))
    return manifest

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download & stream study datasets"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Stream datasets and write data/raw/",
    )
    args = parser.parse_args(argv)
    if not args.download:
        parser.print_help()
        return 1
    try:
        download_all()
    except Exception as exc:
        log.error("Failed during dataset download: %s", exc)
        return 1
    print("Datasets downloaded; manifest written under data/raw/")
    return 0

if __name__ == "__main__":
    sys.exit(main())