import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

from utils.config import get_path, ensure_dirs_exist

def _write_parquet(split_name: str, split_iter, out_dir: Path, batch_size: int = 1000) -> Path:
    """Write a streaming split to a parquet file in batches."""
    out_file = out_dir / f"{split_name}.parquet"
    writer: Optional[pq.ParquetWriter] = None
    batch = []

    for item in split_iter:
        batch.append(item)
        if len(batch) >= batch_size:
            table = _batch_to_table(batch)
            if writer is None:
                writer = pq.ParquetWriter(str(out_file), table.schema)
            writer.write_table(table)
            batch.clear()

    # Write any remaining rows
    if batch:
        table = _batch_to_table(batch)
        if writer is None:
            writer = pq.ParquetWriter(str(out_file), table.schema)
        writer.write_table(table)

    if writer is not None:
        writer.close()
    else:
        # Empty split – create an empty parquet file
        out_file.touch()
    return out_file

def _batch_to_table(batch):
    """Convert a list of dicts to a pyarrow Table."""
    # Assume all dicts have the same keys
    first = batch[0]
    columns = {k: [d[k] for d in batch] for k in first}
    return pa.Table.from_pydict(columns)

def download_planbench_xl(output_dir: Optional[Path] = None, max_retries: int = 3) -> Path:
    """
    Download the PlanBench-XL dataset (streaming) and write each split to parquet files
    under ``output_dir`` (default ``data/raw``). Returns the directory containing the
    parquet files.
    """
    if output_dir is None:
        output_dir = get_path('data/raw')
    ensure_dirs_exist(output_dir)

    retry = 0
    last_error = None
    while retry < max_retries:
        try:
            # Load the dataset in streaming mode
            dataset = load_dataset("PlanBench/planbench-xl", streaming=True)

            for split_name in dataset.keys():
                split_iter = dataset[split_name]
                print(f"Downloading split '{split_name}'...", flush=True)
                _write_parquet(split_name, split_iter, output_dir)

            return output_dir
        except Exception as e:
            last_error = e
            retry += 1
            if retry < max_retries:
                wait = 2 ** retry
                print(f"Retry {retry}/{max_retries} after {wait}s due to error: {e}", file=sys.stderr)
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"Failed to download PlanBench-XL after {max_retries} attempts: {e}"
                ) from e

    raise RuntimeError(f"Download failed: {last_error}")

def load_injected_data(input_path: Optional[Path] = None) -> list:
    """Load the injected failure subset."""
    if input_path is None:
        input_path = get_path('data/derived/implicit_failure_subset.jsonl')

    data = []
    if input_path.exists():
        with open(input_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return data

def main():
    parser = argparse.ArgumentParser(description="PlanBench-XL data loader")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the raw PlanBench-XL dataset and write parquet files to data/raw/",
    )
    args = parser.parse_args()

    if args.download:
        out_dir = download_planbench_xl()
        print(f"Dataset parquet files written to: {out_dir}")
    else:
        print("No action specified. Use --download to fetch the dataset.", file=sys.stderr)

if __name__ == "__main__":
    main()
