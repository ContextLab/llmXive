"""Dataset acquisition for the density-supervision study (FR-001).

Streams the GSM8K train and test splits (``openai/gsm8k``, config
``main``) and the logical-deduction subset of ``bigbench_lite``, and
persists real raw snapshots under ``data/raw/`` together with a
manifest describing identifiers, sample sizes, byte sizes, and the
representativeness limitations of the fixed samples.

Fail-loudly policy
------------------
If the real HuggingFace fetch fails for ANY reason, this module
raises ``RuntimeError`` immediately.  There is NO synthetic/mock
fallback anywhere in this file.
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
GSM8K_ID = "openai/gsm8k"
GSM8K_CONFIG = "main"

# bigbench_lite is published on the Hub under the ``bigbench``
# namespace; the bare name ``bigbench_lite`` is also accepted by the
# loader below as the first candidate (per the plan's Verified
# Datasets table).  Both candidates are REAL sources — if neither is
# reachable the loader raises (no synthetic fallback).
BIGBENCH_CANDIDATES = ("bigbench_lite", "bigbench/bigbench_lite")
BIGBENCH_TASK = "logical_deduction"

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
def _materialize_stream(iterable: Iterable[dict], limit: int) -> List[dict]:
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

def _open_bigbench_stream():
    """Open a REAL streaming iterable of bigbench logical-deduction examples.

    Tries each verified real identifier in turn; if none can be
    fetched, raises RuntimeError (fail loudly — never synthetic).
    """
    last_exc: Exception | None = None
    for ds_id in BIGBENCH_CANDIDATES:
        try:
            # bigbench_lite is config-per-task; the logical_deduction
            # config yields exactly the logical-deduction task rows.
            ds = load_dataset(ds_id, BIGBENCH_TASK, split="default", streaming=True)
            log.info("Streaming %s (task=%s)", ds_id, BIGBENCH_TASK)
            return ds
        except Exception as exc:  # try the next REAL identifier
            log.warning("Real source %s unavailable: %s", ds_id, exc)
            last_exc = exc
    raise RuntimeError(
        "Failed to load the logical-deduction subset of bigbench_lite "
        f"(tried {BIGBENCH_CANDIDATES}): {last_exc}"
    )

# ----------------------------------------------------------------------
# Public loader functions
# ----------------------------------------------------------------------
def load_gsm8k(split: str = "test", streaming: bool = True) -> List[dict]:
    """Load a limited, MATERIALIZED sample from the real GSM8K dataset.

    Internally uses exactly::

        datasets.load_dataset("openai/gsm8k", "main",
                              split=split, streaming=True)

    and materializes the first ``SAMPLE_LIMITS[split]`` rows via
    ``itertools.islice``.  Peak RAM stays far below 6 GB because the
    underlying parquet files are streamed in chunks.

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
        If the dataset cannot be fetched or an unsupported split is
        requested.  The error propagates immediately — there is no
        fallback of any kind.
    """
    if split not in {"train", "test"}:
        raise RuntimeError(f"Unsupported GSM8K split '{split}'. Use 'train' or 'test'.")

    limit = SAMPLE_LIMITS[split]
    ds = load_dataset(GSM8K_ID, GSM8K_CONFIG, split=split, streaming=True)
    log.info("Streaming GSM8K %s split (limit %d)", split, limit)
    materialized = _materialize_stream(ds, limit)
    if not materialized:
        raise RuntimeError(
            f"GSM8K {split} stream yielded zero rows for {GSM8K_ID}."
        )
    return materialized

def load_bigbench_lite() -> List[dict]:
    """Load a MATERIALIZED logical-deduction sample from ``bigbench_lite``.

    Streams the real bigbench_lite logical-deduction task and returns
    the first ``SAMPLE_LIMITS['bigbench_logical']`` examples as a
    list (via ``itertools.islice``).

    Returns
    -------
    List[dict]
        A list of logical-deduction examples (max 500 rows).

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched or the stream yields no rows.
    """
    limit = SAMPLE_LIMITS["bigbench_logical"]
    ds = _open_bigbench_stream()
    materialized = _materialize_stream(ds, limit)
    if not materialized:
        raise RuntimeError(
            "Logical deduction subset of bigbench_lite yielded zero rows."
        )
    return materialized

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

    gsm8k_train_path = raw_dir / "gsm8k_train.jsonl"
    gsm8k_test_path = raw_dir / "gsm8k_test.jsonl"
    logical_path = raw_dir / "bigbench_logical_deduction.jsonl"

    train_data = load_gsm8k(split="train")
    n_train = _snapshot_to_jsonl(train_data, gsm8k_train_path)

    test_data = load_gsm8k(split="test")
    n_test = _snapshot_to_jsonl(test_data, gsm8k_test_path)

    logical_data = load_bigbench_lite()
    n_logical = _snapshot_to_jsonl(logical_data, logical_path)

    size_train = gsm8k_train_path.stat().st_size
    size_test = gsm8k_test_path.stat().st_size
    size_logical = logical_path.stat().st_size
    total = size_train + size_test + size_logical

    if total > _MAX_TOTAL_BYTES:
        raise RuntimeError(
            f"Total raw dataset size {total} bytes exceeds the 7 GB budget"
        )

    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Raw data manifest (generated by code/data.py)",
        f"generated_utc: {now}",
        "",
        "## Datasets (all REAL HuggingFace sources; no synthetic data)",
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
        f"dataset_3: bigbench_lite (task={BIGBENCH_TASK})",
        f"  snapshot_file: {logical_path.name}",
        f"  rows: {n_logical}",
        f"  size_bytes: {size_logical}",
        f"  size_human: {_fmt_size(size_logical)}",
        "",
        "## Sample sizes and representativeness limitations",
        "",
        "  - GSM8K train: first 2,000 examples of the 7,473-example train",
        "    split, taken in dataset order via itertools.islice on the stream.",
        "  - GSM8K test: first 500 examples of the 1,319-example test split.",
        "  - bigbench logical_deduction: first 500 examples of the task's",
        "    split, taken in dataset order.",
        "  Limitations: these are fixed, non-random PREFIX samples, not",
        "  random samples; dataset ordering may correlate with difficulty",
        "  or source, so the samples may not be fully representative of",
        "  the full splits. All downstream accuracy figures are therefore",
        "  estimates on these fixed subsets, not on the full benchmarks.",
        "",
        "## Budget",
        "",
        f"total_size_bytes: {total}",
        f"total_size_human: {_fmt_size(total)}",
        "budget_limit: 7 GB",
        "within_budget: true",
        "peak_ram_note: datasets are streamed in chunks; peak RAM stays well below 6 GB.",
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
    download_all()
    print("Datasets downloaded; manifest written under data/raw/")
    return 0

if __name__ == "__main__":
    sys.exit(main())
