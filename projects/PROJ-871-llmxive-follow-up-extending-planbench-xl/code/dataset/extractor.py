"""
Extractor for the implicit‑failure subset of the PlanBench‑XL dataset.

This script streams the raw parquet files produced by ``loader.py`` (stored in
``data/raw/``), filters tasks whose ``ground_truth`` field is equal to the
string ``"implicit_failure"``, and writes the filtered records to a JSON‑Lines
file at ``data/derived/implicit_failure_subset.jsonl``.

The implementation is deliberately streaming‑friendly to keep memory usage
low – each parquet file is read in batches and rows are processed one by
one.  If the raw data directory does not exist or contains no parquet files,
a ``FileNotFoundError`` is raised so that the failure is loud and visible
to the execution harness.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List

import pyarrow.parquet as pq

from utils.config import get_path, ensure_dirs_exist

def _iter_parquet_rows(parquet_path: Path) -> Iterable[dict]:
    """
    Yield rows from a parquet file as plain Python dictionaries.

    Parameters
    ----------
    parquet_path: Path
        Path to the parquet file.

    Yields
    ------
    dict
        One row of the parquet file.
    """
    # ``ParquetFile.iter_batches`` yields RecordBatch objects; we convert each
    # batch to a list of dictionaries with ``to_pylist`` which is efficient
    # and avoids loading the whole file into memory.
    pq_file = pq.ParquetFile(str(parquet_path))
    for batch in pq_file.iter_batches():
        for row in batch.to_pylist():
            yield row

def _stream_raw_dataset(raw_dir: Path) -> Iterable[dict]:
    """
    Stream all rows from every parquet file in ``raw_dir``.

    Parameters
    ----------
    raw_dir: Path
        Directory containing parquet files written by ``loader.py``.

    Yields
    ------
    dict
        One task record.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_dir}")

    parquet_files = sorted(raw_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {raw_dir}")

    for parquet_path in parquet_files:
        yield from _iter_parquet_rows(parquet_path)

def extract_implicit_failure_subset(
    raw_dir: Path,
    output_path: Path,
    ground_truth_key: str = "ground_truth",
    target_value: str = "implicit_failure",
) -> Path:
    """
    Filter the raw dataset for tasks whose ``ground_truth`` equals
    ``target_value`` and write them to ``output_path`` as JSON‑Lines.

    Parameters
    ----------
    raw_dir: Path
        Directory with the raw parquet files.
    output_path: Path
        Destination JSONL file for the filtered subset.
    ground_truth_key: str, optional
        The dictionary key that stores the ground‑truth label. Defaults to
        ``"ground_truth"``.
    target_value: str, optional
        The value indicating an implicit failure. Defaults to
        ``"implicit_failure"``.

    Returns
    -------
    Path
        The path to the written JSONL file.
    """
    ensure_dirs_exist(output_path.parent)

    # Write incrementally to avoid holding all filtered rows in memory.
    with open(output_path, "w", encoding="utf-8") as out_f:
        for record in _stream_raw_dataset(raw_dir):
            if record.get(ground_truth_key) == target_value:
                json_line = json.dumps(record, ensure_ascii=False)
                out_f.write(json_line + "\n")
    return output_path

def main() -> None:
    """
    CLI entry point.

    Usage
    -----
    python code/dataset/extractor.py [--output <path>]

    Options
    -------
    --output : Optional path for the JSONL output. If omitted, the default
               location ``data/derived/implicit_failure_subset.jsonl`` is
               used.
    """
    parser = argparse.ArgumentParser(
        description="Extract the implicit‑failure subset from the raw PlanBench‑XL data."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the JSONL subset (default: data/derived/implicit_failure_subset.jsonl).",
    )
    args = parser.parse_args()

    raw_dir = get_path("data/raw")
    output_path = (
        Path(args.output) if args.output is not None else get_path("data/derived/implicit_failure_subset.jsonl")
    )

    try:
        result_path = extract_implicit_failure_subset(raw_dir, output_path)
        print(f"Implicit‑failure subset written to: {result_path}")
    except Exception as exc:
        # Propagate the exception so the execution harness sees a non‑zero exit code.
        raise RuntimeError(f"Failed to extract implicit‑failure subset: {exc}") from exc

if __name__ == "__main__":
    main()
