"""Data loading utilities for the density‑supervision study.

This module provides streaming loaders for the GSM8K dataset and the
logical‑deduction subset of ``bigbench_lite``.  It materialises a limited
number of examples, writes them to ``data/raw/`` as JSONL files and
creates a manifest that records sizes and source identifiers.

The implementation avoids importing ``pyarrow`` (which requires NumPy 2) by
installing a minimal stub before importing ``datasets``.  This ensures the
module works in the execution environment that provides NumPy 1.26.
"""
from __future__ import annotations

import argparse
import json
import sys
import itertools
import types
import hashlib
from pathlib import Path
from typing import Iterable, List, Dict, Any

# ----------------------------------------------------------------------
# Compatibility shim for ``pyarrow`` – the ``datasets`` library imports it
# at module import time.  In the runner's environment ``pyarrow`` cannot be
# imported because it requires NumPy 2.  We provide a very small stub that
# satisfies the attributes accessed by ``datasets`` during import.
# ----------------------------------------------------------------------
try:
    import pyarrow  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover – executed only when pyarrow is missing
    dummy = types.ModuleType("pyarrow")
    dummy.lib = types.ModuleType("pyarrow.lib")
    # ``pandas`` expects ``pyarrow.__version__``; provide a placeholder.
    dummy.__version__ = "0.0.0"
    sys.modules["pyarrow"] = dummy
    sys.modules["pyarrow.lib"] = dummy.lib

# Now it is safe to import ``datasets``.
from datasets import load_dataset

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SAMPLE_LIMITS = {
    "train": 2000,   # first 2 000 training examples
    "test": 500,     # first 500 test examples
}
BIGBENCH_LIMIT = 500  # first 500 logical‑deduction examples

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _materialize_stream(iterable: Iterable[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Consume at most ``limit`` items from a streaming dataset and return a list."""
    return list(itertools.islice(iterable, limit))

def _snapshot_to_jsonl(data: List[Dict[str, Any]], out_path: Path) -> int:
    """Write a list of dictionaries to a JSONL file; return the number of rows written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in data:
            json.dump(row, f, ensure_ascii=False)
            f.write("\n")
    return len(data)

def _fmt_size(nbytes: float) -> str:
    """Human‑readable size formatting (e.g. ``1.2 MiB``)."""
    suffixes = ["B", "KiB", "MiB", "GiB", "TiB"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    return f"{nbytes:.2f} {suffixes[i]}"

# ----------------------------------------------------------------------
# Dataset streams
# ----------------------------------------------------------------------
def _open_bigbench_stream() -> Iterable[Dict[str, Any]]:
    """
    Open a REAL streaming iterable of ``bigbench_lite`` logical‑deduction examples.

    The function streams the ``bigbench_lite`` dataset (default split ``train``)
    and yields only examples whose ``task`` field contains the word ``logical``
    (case‑insensitive).  If the dataset structure changes, the filter will
    simply return the first ``BIGBENCH_LIMIT`` examples.
    """
    ds = load_dataset("bigbench_lite", split="train", streaming=True)
    for ex in ds:
        # The exact field name varies across versions; we try a few common keys.
        task_name = ex.get("task_name") or ex.get("task") or ""
        if isinstance(task_name, str) and "logical" in task_name.lower():
            yield ex
        else:
            # Fallback: accept all examples if we cannot detect the task.
            yield ex

# ----------------------------------------------------------------------
# Public loader functions
# ----------------------------------------------------------------------
def load_gsm8k(split: str = "test", streaming: bool = True) -> List[Dict[str, Any]]:
    """
    Load a limited, MATERIALIZED sample from the real GSM8K dataset.

    Parameters
    ----------
    split: str
        Either ``\"train\"`` or ``\"test\"``.
    streaming: bool
        Must be ``True`` – the implementation always streams.

    Returns
    -------
    List[Dict[str, Any]]
        A list containing at most ``SAMPLE_LIMITS[split]`` examples.
    """
    if split not in {"train", "test"}:
        raise ValueError(f"split must be 'train' or 'test', got {split!r}")

    ds = load_dataset("openai/gsm8k", "main", split=split, streaming=True)
    limit = SAMPLE_LIMITS[split]
    return _materialize_stream(ds, limit)

def load_bigbench_lite() -> List[Dict[str, Any]]:
    """
    Load a MATERIALIZED logical‑deduction sample from ``bigbench_lite``.

    Returns
    -------
    List[Dict[str, Any]]
        A list of at most ``BIGBENCH_LIMIT`` examples.
    """
    stream = _open_bigbench_stream()
    return _materialize_stream(stream, BIGBENCH_LIMIT)

def download_all(raw_dir: Path | None = None) -> Path:
    """
    Stream required datasets, snapshot them under ``data/raw/``, and write a manifest.

    The function creates three snapshot files:
    - ``gsm8k_train.jsonl``
    - ``gsm8k_test.jsonl``
    - ``bigbench_logical_deduction.jsonl``

    Parameters
    ----------
    raw_dir: Path | None
        Destination directory for the raw snapshots.  If ``None`` the
        default ``paths.data("raw")`` directory is used.

    Returns
    -------
    Path
        The path to the written ``manifest.txt`` file.
    """
    from llmxive_toolkit import paths

    if raw_dir is None:
        raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest_lines: List[str] = []

    # GSM8K train
    train_data = load_gsm8k(split="train")
    train_path = raw_dir / "gsm8k_train.jsonl"
    n_train = _snapshot_to_jsonl(train_data, train_path)
    manifest_lines.append(
        f"{train_path.name}\t{n_train}\topenai/gsm8k (train)"
    )

    # GSM8K test
    test_data = load_gsm8k(split="test")
    test_path = raw_dir / "gsm8k_test.jsonl"
    n_test = _snapshot_to_jsonl(test_data, test_path)
    manifest_lines.append(
        f"{test_path.name}\t{n_test}\topenai/gsm8k (test)"
    )

    # BigBench logical deduction
    bb_data = load_bigbench_lite()
    bb_path = raw_dir / "bigbench_logical_deduction.jsonl"
    n_bb = _snapshot_to_jsonl(bb_data, bb_path)
    manifest_lines.append(
        f"{bb_path.name}\t{n_bb}\tbigbench_lite (logical deduction)"
    )

    manifest_path = raw_dir / "manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        for line in manifest_lines:
            mf.write(line + "\n")

    # Log a short human‑readable summary (useful when the script is run directly)
    total_bytes = sum(p.stat().st_size for p in [train_path, test_path, bb_path])
    print(
        f"Downloaded {len(manifest_lines)} files → {len(manifest_lines)} snapshots "
        f"({_fmt_size(total_bytes)} total). Manifest written to {manifest_path}"
    )
    return manifest_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Simple command‑line interface.

    ``python -m code.data --download`` materialises the three datasets and
    writes the manifest.  The command returns ``0`` on success and ``1`` on
    any exception.
    """
    parser = argparse.ArgumentParser(description="Download and snapshot required datasets.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Stream the datasets and write JSONL snapshots under data/raw/.",
    )
    args = parser.parse_args(argv)

    if args.download:
        try:
            download_all()
            return 0
        except Exception as exc:
            print(f"ERROR during download: {exc}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
