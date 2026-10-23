"""
validate_dataset_stats.py

Implements task **T016** – Validate Dataset Statistics.

The script validates that the generated dataset exhibits a statistically
significant proportion of non‑zero KL divergence and computes descriptive
statistics required by downstream steps.  It also records a SHA‑256
checksum of the dataset file for provenance.

Usage (as documented in ``quickstart.md``)::

    python code/cli/validate_dataset_stats.py \\
        --input data/processed/training_sample.parquet \\
        --output data/metrics/dataset_stats.json
"""

import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

DEFAULT_INPUT_PATH = Path("data/processed/training_sample.parquet")
DEFAULT_OUTPUT_PATH = Path("data/metrics/dataset_stats.json")
DEFAULT_THRESHOLD = 0.05

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_parquet(parquet_path: Path) -> pd.DataFrame:
    """Load the training sample parquet file."""
    if not parquet_path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    # Explicitly request the fastparquet engine to avoid pyarrow.
    return pd.read_parquet(parquet_path, engine="fastparquet")

def compute_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the required statistics:

    * nonzero_kl_proportion – overall fraction of rows where KL > 0
    * mean_kl_int4, mean_kl_int8, mean_kl_fp8 – mean KL per quantisation level
    * dataset_sha256 – SHA‑256 checksum of the parquet file
    """
    if "kl_divergence" not in df.columns:
        raise KeyError("Column 'kl_divergence' missing from dataset.")
    if "quantization_level" not in df.columns:
        raise KeyError("Column 'quantization_level' missing from dataset.")

    nonzero_kl_proportion = float((df["kl_divergence"] != 0).mean())

    def mean_kl_for(level: str) -> float | None:
        mask = df["quantization_level"] == level
        if mask.any():
            return float(df.loc[mask, "kl_divergence"].mean())
        return None

    mean_kl_int4 = mean_kl_for("INT4")
    mean_kl_int8 = mean_kl_for("INT8")
    mean_kl_fp8 = mean_kl_for("FP8")

    return {
        "nonzero_kl_proportion": nonzero_kl_proportion,
        "mean_kl_int4": mean_kl_int4,
        "mean_kl_int8": mean_kl_int8,
        "mean_kl_fp8": mean_kl_fp8,
    }

def write_json(data: Dict[str, Any], output_path: Path) -> None:
    """Write ``data`` as pretty‑printed JSON to ``output_path``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def load_json(json_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate(stats: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> bool:
    """
    Return ``True`` if the ``nonzero_kl_proportion`` meets or exceeds
    ``threshold``.
    """
    prop = stats.get("nonzero_kl_proportion")
    if prop is None:
        raise ValueError("'nonzero_kl_proportion' missing from stats.")
    return float(prop) >= threshold

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate dataset statistics and write a JSON summary. "
            "If the JSON already exists, it is loaded and validated. "
            "If it does not exist, the script computes the statistics "
            "from the parquet file, writes the JSON, and then validates."
        )
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to the training sample parquet file (new flag).",
    )
    parser.add_argument(
        "--data",
        type=str,
        help="Path to the training sample parquet file (legacy flag).",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to the output JSON file (new flag).",
    )
    parser.add_argument(
        "--stats",
        type=str,
        help="Path to the output JSON file (legacy flag).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Minimum required non‑zero KL proportion (default 0.05).",
    )
    args = parser.parse_args()

    input_path = (
        Path(args.input) if args.input
        else Path(args.data) if args.data
        else DEFAULT_INPUT_PATH
    ).expanduser().resolve()
    output_path = (
        Path(args.output) if args.output
        else Path(args.stats) if args.stats
        else DEFAULT_OUTPUT_PATH
    ).expanduser().resolve()
    threshold = args.threshold

    # Load existing stats if present, otherwise compute them.
    if output_path.is_file():
        try:
            stats = load_json(output_path)
        except Exception as exc:
            print(f"Failed to read existing stats JSON: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            df = load_parquet(input_path)
        except Exception as exc:
            print(f"Failed to read training data parquet: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            stats = compute_statistics(df)
        except Exception as exc:
            print(f"Error computing statistics: {exc}", file=sys.stderr)
            sys.exit(1)

        # Add checksum for provenance.
        try:
            stats["dataset_sha256"] = compute_sha256(input_path)
        except Exception as exc:
            print(f"Failed to compute SHA‑256 checksum: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            write_json(stats, output_path)
            print(f"Statistics written to {output_path}")
        except Exception as exc:
            print(f"Failed to write statistics JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    # Perform validation.
    try:
        passed = validate(stats, threshold=threshold)
    except Exception as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(1)

    if passed:
        print(
            f"Validation passed: non‑zero KL proportion "
            f"{stats.get('nonzero_kl_proportion'):.4f} ≥ {threshold}"
        )
        sys.exit(0)
    else:
        print(
            f"Validation failed: non‑zero KL proportion "
            f"{stats.get('nonzero_kl_proportion'):.4f} < {threshold}",
            file=sys.stderr,
        )
        sys.exit(1)

if __name__ == "__main__":
    main()