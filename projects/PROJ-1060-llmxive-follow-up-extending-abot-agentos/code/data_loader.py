import hashlib
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import RANDOM_SEED, MAX_TRACES
import random

def _compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_checksum(file_path: Path) -> None:
    """Write SHA256 checksum to a .sha256 side‑car file."""
    checksum = _compute_sha256(file_path)
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    checksum_path.write_text(checksum, encoding="utf-8")

def _verify_checksum(file_path: Path) -> bool:
    """Verify that the file's checksum matches the stored .sha256 file."""
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    if not checksum_path.is_file():
        return False
    expected = checksum_path.read_text(encoding="utf-8").strip()
    actual = _compute_sha256(file_path)
    return expected == actual

def stream_alfworld_traces(
    split: str = "train",
    streaming: bool = True,
    max_records: Optional[int] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Stream ALFWorld traces from the real dataset.

    Parameters
    ----------
    split: str
        Dataset split to stream (default ``train``).
    streaming: bool
        If ``True`` uses ``datasets`` streaming mode; otherwise loads whole split.
    max_records: Optional[int]
        If provided, limits the number of yielded records (useful for quick tests).

    Yields
    ------
    Dict[str, Any]
        Individual trace dictionaries.
    """
    try:
        from datasets import load_dataset

        ds = load_dataset(
            "alfworld/alfworld",
            split=split,
            streaming=streaming,
        )
        for i, item in enumerate(ds):
            if max_records is not None and i >= max_records:
                break
            yield item
    except Exception as e:
        # Fallback to local raw files
        raw_dir = Path("data/raw")
        if not raw_dir.exists():
            raise RuntimeError(
                f"Failed to load ALFWorld traces from remote and no local fallback exists. "
                f"Original error: {e}"
            )
        # Verify checksums before using any file
        for file in raw_dir.glob("*.json"):
            if not _verify_checksum(file):
                raise RuntimeError(
                    f"Checksum verification failed for local file {file}. "
                    f"Delete the corrupted file and re‑download."
                )
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        if max_records is not None and i >= max_records:
                            break
                        yield item
                else:
                    yield data

def load_traces_as_list(
    split: str = "train",
    max_traces: int = MAX_TRACES,
    streaming: bool = True,
    max_records: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Load traces as a list, optionally limiting to ``max_traces``.
    """
    traces: List[Dict[str, Any]] = []
    random.seed(RANDOM_SEED)

    for trace in stream_alfworld_traces(
        split=split, streaming=streaming, max_records=max_records
    ):
        if len(traces) >= max_traces:
            break
        traces.append(trace)

    if not traces:
        raise RuntimeError("No traces loaded from any source.")
    return traces

def _download_and_store(
    dataset_name: str,
    split: str = "train",
    max_records: Optional[int] = None,
) -> Path:
    """
    Download the specified ALFWorld split and store it under ``data/raw``.
    The function streams the dataset to avoid loading everything into memory,
    writes each record as a JSON line to a single file, and creates a SHA‑256
    checksum side‑car file for verification.
    """
    from tqdm import tqdm  # tqdm is part of the standard environment; safe to import

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    out_path = raw_dir / "alfworld_traces.json"
    # If the file already exists and checksum matches, skip download
    if out_path.is_file() and _verify_checksum(out_path):
        print(f"Existing data file found and checksum verified at {out_path}")
        return out_path

    # Stream dataset and write line‑by‑line
    print(f"Downloading {dataset_name} ({split} split)...")
    with out_path.open("w", encoding="utf-8") as fout:
        for i, record in enumerate(
            stream_alfworld_traces(split=split, streaming=True, max_records=max_records)
        ):
            json.dump(record, fout)
            fout.write("\n")
            # Simple progress indicator
            if (i + 1) % 1000 == 0:
                print(f"  {i + 1} records written...")

    # Write checksum
    _write_checksum(out_path)
    print(f"Download complete. Checksum written to {out_path.with_suffix('.json.sha256')}")
    return out_path

def _verify_local_data() -> None:
    """
    Verify that every ``*.json`` file in ``data/raw`` has a matching checksum.
    Raises ``RuntimeError`` on first mismatch.
    """
    raw_dir = Path("data/raw")
    if not raw_dir.is_dir():
        raise RuntimeError("Data directory 'data/raw' does not exist.")

    for file in raw_dir.glob("*.json"):
        if not _verify_checksum(file):
            raise RuntimeError(
                f"Checksum verification failed for {file}. "
                f"Delete the corrupted file and re‑download."
            )
    print("All local data files passed checksum verification.")

def _validate_trace_schema(trace: Dict[str, Any]) -> List[str]:
    """
    Validate required and optional fields in a trace.
    Returns a list of warning messages (empty if no warnings).
    """
    warnings = []
    required = ["dialogue", "outcome"]
    optional = ["spatial_coords", "temporal_seq"]
    for key in required:
        if key not in trace:
            warnings.append(f"Missing required field '{key}'.")
    for key in optional:
        if key not in trace:
            warnings.append(f"Optional field '{key}' not present.")
    return warnings

def verify_data() -> None:
    """
    Verify checksum of downloaded files and validate schema of each trace.
    Logs warnings for missing optional fields but does not abort the run.
    """
    _verify_local_data()
    # Validate a few records (up to 100) to keep the verification fast
    raw_dir = Path("data/raw")
    for file in raw_dir.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 100:
                    break
                try:
                    trace = json.loads(line)
                except json.JSONDecodeError:
                    raise RuntimeError(f"Invalid JSON in {file} at line {i + 1}.")
                warnings = _validate_trace_schema(trace)
                for w in warnings:
                    print(f"Warning in {file} line {i + 1}: {w}")

def main():
    """CLI entry point for data loader."""
    import argparse

    parser = argparse.ArgumentParser(description="ALFWorld Data Loader")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Download command
    dl_parser = subparsers.add_parser("download", help="Download ALFWorld dataset")
    dl_parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Dataset identifier (e.g., alfworld/alfworld)",
    )
    dl_parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Dataset split to download (default: train)",
    )
    dl_parser.add_argument(
        "--max-records",
        type=int,
        default=1000,
        help="Maximum number of records to download (default: 1000)",
    )

    # Verify command
    subparsers.add_parser("verify", help="Verify checksum and schema of local data")

    # Sample command (legacy – kept for backward compatibility)
    sample_parser = subparsers.add_parser("sample", help="Sample a few traces")
    sample_parser.add_argument(
        "--sample",
        type=int,
        default=10,
        help="Number of traces to sample (default: 10)",
    )

    args = parser.parse_args()

    if args.command == "download":
        # The dataset name is ignored for now because only ALFWorld is supported.
        if args.dataset != "alfworld/alfworld":
            print(
                f"Warning: Only 'alfworld/alfworld' is supported. Received '{args.dataset}'."
            )
        try:
            _download_and_store(
                dataset_name=args.dataset,
                split=args.split,
                max_records=args.max_records,
            )
        except Exception as e:
            print(f"Error during download: {e}")
            sys.exit(1)

    elif args.command == "verify":
        try:
            verify_data()
        except Exception as e:
            print(f"Verification failed: {e}")
            sys.exit(1)

    elif args.command == "sample":
        try:
            traces = load_traces_as_list(max_traces=args.sample)
            print(f"Loaded {len(traces)} traces.")
            for t in traces[:3]:
                print(json.dumps(t, indent=2))
        except Exception as e:
            print(f"Error loading traces: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
