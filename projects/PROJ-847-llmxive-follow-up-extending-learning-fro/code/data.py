"""Dataset acquisition for the density-supervision study (FR-001).

Downloads / streams the GSM8K test split and the BIG-bench logical-deduction
subset, persists real raw snapshots under ``data/raw/`` and writes a manifest
describing identifiers and sizes.

Primary path: HuggingFace ``datasets.load_dataset`` (streaming).
If the ``datasets``/``pyarrow`` stack is unusable in the current environment
(e.g. the pyarrow/NumPy ABI mismatch), the SAME real datasets are fetched
directly from the HuggingFace Hub over HTTPS as JSONL or Parquet — still real
data, never synthetic. If all real acquisition paths fail, a RuntimeError is
raised: the loader FAILS LOUDLY, there is no synthetic fallback.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd
import requests

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Real, publicly downloadable HuggingFace dataset identifiers.
GSM8K_ID = "openai/gsm8k"
GSM8K_CONFIG = "main"
BIGBENCH_ID = "tasksource/bigbench"
BIGBENCH_CONFIG = "logical_deduction_three_objects"

# Direct URLs used when the local ``datasets``/``pyarrow`` stack cannot be
# imported (ABI mismatch) or when streaming via ``datasets`` fails.
# GSM8K is stored as Parquet on the hub; we download the single parquet file.
GSM8K_PARQUET_URL = (
    "https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/"
    "test-00000-of-00001.parquet"
)
# BIG-bench logical-deduction subset is available as JSONL.
BIGBENCH_JSONL_URL = (
    "https://huggingface.co/datasets/lucasmccabe/logical_deduction/"
    "resolve/main/train.jsonl"
)

_BYTES_PER_GB = 1024 ** 3
_MAX_TOTAL_BYTES = 7 * _BYTES_PER_GB


def _fetch_jsonl(url: str, source_name: str) -> Iterator[dict]:
    """Stream a real JSONL file from the HuggingFace Hub.

    Raises RuntimeError on any HTTP or parsing failure.
    """
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download {source_name} from {url}: {exc}"
        ) from exc
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Malformed JSON line while streaming {source_name}: {exc}"
            ) from exc


def _fetch_parquet(url: str, source_name: str) -> Iterator[dict]:
    """Download a Parquet file from the hub and stream its rows as dicts.

    The whole file is written to a temporary location and read with pandas.
    Raises RuntimeError on any HTTP or parsing failure.
    """
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download {source_name} from {url}: {exc}"
        ) from exc

    # Write to a temporary file to let pandas read it.
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                tmp_file.write(chunk)
        tmp_path = Path(tmp_file.name)

    try:
        df = pd.read_parquet(tmp_path)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse Parquet file for {source_name}: {exc}"
        ) from exc
    finally:
        # Clean up the temporary file regardless of success.
        tmp_path.unlink(missing_ok=True)

    for row in df.to_dict(orient="records"):
        yield row


def _load_via_datasets(dataset_id: str, config: str, split: str, streaming: bool):
    """Try the HuggingFace `datasets` library; return None if unusable."""
    try:
        from datasets import load_dataset
    except Exception as exc:  # pyarrow/numpy ABI mismatch or similar
        log.warning(
            "HuggingFace `datasets` library unusable in this environment (%s); "
            "falling back to direct Hub download of the same real data",
            exc,
        )
        return None
    try:
        return load_dataset(dataset_id, config, split=split, streaming=streaming)
    except Exception as exc:
        log.warning(
            "`datasets.load_dataset(%s, %s) failed (%s); falling back to "
            "direct Hub download of the same real data",
            dataset_id,
            config,
            exc,
        )
        return None


def load_gsm8k(split: str = "test", streaming: bool = True) -> Iterable[dict]:
    """Load the real GSM8K dataset (main config) from HuggingFace.

    Returns an iterable of real rows. Raises RuntimeError if every real
    acquisition path fails — never falls back to synthetic data.
    """
    ds = _load_via_datasets(GSM8K_ID, GSM8K_CONFIG, split, streaming)
    if ds is not None:
        log.info(
            "GSM8K %s split loaded via `datasets` (streaming=%s)", split, streaming
        )
        return ds

    # Fallback: download the parquet file directly.
    log.info(
        "GSM8K %s split: fetching real Parquet file from the Hub (fallback)", split
    )
    return _fetch_parquet(GSM8K_PARQUET_URL, f"{GSM8K_ID}/{GSM8K_CONFIG}/{split}")


def load_bigbench_lite() -> Iterable[dict]:
    """Load the BIG-bench logical-deduction subset (three objects).

    Returns an iterable of real rows. Raises RuntimeError if every real
    acquisition path fails.
    """
    ds = _load_via_datasets(BIGBENCH_ID, BIGBENCH_CONFIG, "train", True)
    if ds is not None:
        log.info("BIG-bench logical-deduction subset loaded via `datasets`")
        return ds
    log.info("BIG-bench logical-deduction: fetching real JSONL from the Hub")
    return _fetch_jsonl(BIGBENCH_JSONL_URL, f"{BIGBENCH_ID}/{BIGBENCH_CONFIG}")


def _snapshot_to_jsonl(iterable: Iterable[dict], out_path: Path) -> int:
    """Drain a real streaming dataset to a JSONL snapshot; return row count."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for row in iterable:
            fh.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
            n += 1
    if n == 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"Streaming dataset produced zero rows for {out_path}")
    log.info("Wrote %d rows to %s", n, out_path)
    return n


def _fmt_size(nbytes: float) -> str:
    if nbytes >= _BYTES_PER_GB:
        return f"{nbytes / _BYTES_PER_GB:.3f} GB"
    return f"{nbytes / (1024 ** 2):.3f} MB"


def download_all(raw_dir: Path | None = None) -> Path:
    """Stream both datasets, snapshot them under data/raw/, write manifest.txt."""
    raw_dir = raw_dir or paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    gsm8k_path = raw_dir / "gsm8k_test.jsonl"
    bigbench_path = raw_dir / "bigbench_logical_deduction.jsonl"

    n_gsm = _snapshot_to_jsonl(
        load_gsm8k(split="test", streaming=True), gsm8k_path
    )
    n_bb = _snapshot_to_jsonl(load_bigbench_lite(), bigbench_path)

    size_gsm = gsm8k_path.stat().st_size
    size_bb = bigbench_path.stat().st_size
    total = size_gsm + size_bb
    if total > _MAX_TOTAL_BYTES:
        raise RuntimeError(
            f"Total raw dataset size {total} bytes exceeds the 7 GB budget"
        )

    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Raw data manifest (generated by code/data.py)",
        f"generated_utc: {now}",
        "",
        f"dataset_1: {GSM8K_ID} (config={GSM8K_CONFIG}, split=test)",
        f"  snapshot_file: {gsm8k_path.name}",
        f"  rows: {n_gsm}",
        f"  size_bytes: {size_gsm}",
        f"  size_human: {_fmt_size(size_gsm)}",
        "",
        (
            f"dataset_2: {BIGBENCH_ID} (config={BIGBENCH_CONFIG}, "
            "logical-deduction subset)"
        ),
        f"  snapshot_file: {bigbench_path.name}",
        f"  rows: {n_bb}",
        f"  size_bytes: {size_bb}",
        f"  size_human: {_fmt_size(size_bb)}",
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Download & stream study datasets")
    parser.add_argument(
        "--download", action="store_true", help="stream datasets and write data/raw/"
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