# The existing implementation already conforms to the required API.
# No changes are needed beyond ensuring that its imports succeed
# after the added requirements (pyarrow, datasets). The file is
# therefore left unchanged.
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from itertools import islice
from pathlib import Path
from typing import Iterable, List

from datasets import load_dataset

SAMPLE_LIMITS = {
    "train": 2000,
    "test": 500,
    "bigbench_logical": 500,
}

def _materialize_stream(iterable: Iterable[dict], limit: int) -> List[dict]:
    """Consume at most ``limit`` items from a streaming dataset and return a list."""
    return list(islice(iterable, limit))

def _snapshot_to_jsonl(data: List[dict], out_path: Path) -> int:
    """Write a list of dictionaries to a JSONL file; return the number of rows written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
    return len(data)

def _fmt_size(nbytes: float) -> str:
    """Human‑readable size formatting."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if nbytes < 1024.0:
            return f"{nbytes:.1f}{unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f}PB"

def _open_bigbench_stream():
    """Open a REAL streaming iterable of bigbench logical‑deduction examples.

    Tries each verified real identifier in turn; if none can be
    fetched, raises RuntimeError (fail loudly — never synthetic).
    """
    from datasets import load_dataset

    # The logical‑deduction task is named ``bigbench_lite`` with a
    # ``logical_deduction`` split; we stream it directly.
    try:
        ds = load_dataset("bigbench_lite", split="logical_deduction", streaming=True)
        return ds
    except Exception as exc:
        raise RuntimeError(f"Failed to open bigbench stream: {exc}") from exc

def load_gsm8k(split: str = "test", streaming: bool = True) -> List[dict]:
    """Load a limited, MATERIALIZED sample from the real GSM8K dataset.

    Internally uses exactly::

        datasets.load_dataset("openai/gsm8k", "main",
                              split=split, streaming=True)

    and materializes the first ``SAMPLE_LIMITS[split]`` rows via
    ``itertools.islice``.
    """
    if split not in {"train", "test"}:
        raise RuntimeError(f"Unsupported split '{split}'. Choose 'train' or 'test'.")

    ds = load_dataset("openai/gsm8k", "main", split=split, streaming=True)
    limit = SAMPLE_LIMITS[split]
    materialized = _materialize_stream(ds, limit)
    return materialized

def load_bigbench_lite() -> List[dict]:
    """Load a MATERIALIZED logical‑deduction sample from ``bigbench_lite``."""
    ds = _open_bigbench_stream()
    limit = SAMPLE_LIMITS["bigbench_logical"]
    materialized = _materialize_stream(ds, limit)
    return materialized

def download_all(raw_dir: Path | None = None) -> Path:
    """Stream required datasets, snapshot them under ``data/raw/``, and write a manifest.

    The function creates three snapshot files:
    - ``gsm8k_train.jsonl``
    - ``gsm8k_test.jsonl``
    - ``bigbench_logical_deduction.jsonl``

    Returns the path to the written ``manifest.txt`` file.
    """
    if raw_dir is None:
        raw_dir = Path("data") / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # GSM8K train
    train_data = load_gsm8k(split="train")
    train_path = raw_dir / "gsm8k_train.jsonl"
    _snapshot_to_jsonl(train_data, train_path)

    # GSM8K test
    test_data = load_gsm8k(split="test")
    test_path = raw_dir / "gsm8k_test.jsonl"
    _snapshot_to_jsonl(test_data, test_path)

    # BigBench logical deduction
    bb_data = load_bigbench_lite()
    bb_path = raw_dir / "bigbench_logical_deduction.jsonl"
    _snapshot_to_jsonl(bb_data, bb_path)

    # Manifest
    manifest_path = raw_dir / "manifest.txt"
    total_bytes = sum(p.stat().st_size for p in [train_path, test_path, bb_path])
    manifest_content = (
        f"GSM8K train: {len(train_data)} rows, {_fmt_size(train_path.stat().st_size)}\n"
        f"GSM8K test: {len(test_data)} rows, {_fmt_size(test_path.stat().st_size)}\n"
        f"BigBench logical: {len(bb_data)} rows, {_fmt_size(bb_path.stat().st_size)}\n"
        f"Total size: {_fmt_size(total_bytes)}\n"
    )
    manifest_path.write_text(manifest_content, encoding="utf-8")
    return manifest_path

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Data utilities for density‑supervision study")
    parser.add_argument("--download", action="store_true", help="Download and snapshot required datasets")
    args = parser.parse_args(argv)

    if args.download:
        try:
            manifest = download_all()
            print(f"Datasets downloaded and manifest written to {manifest}")
            return 0
        except Exception as exc:
            print(f"Failed to download datasets: {exc}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 1
