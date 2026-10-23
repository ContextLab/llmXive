"""
generate_ground_truth.py (wrapper)

This module provides a convenient programmatic wrapper around the CLI
implementation of task **T015** (`code/cli/generate_ground_truth.py`).  The
wrapper is used by the integration test
`tests/cli/test_generate_ground_truth.py`.  It runs the CLI script,
generates the Parquet dataset, computes a lightweight statistics JSON
file, and writes both artifacts to the locations expected by the test
suite.

The CLI script already implements the full data‑generation pipeline –
loading a GSM8K subset, extracting gradient norms, computing curvature,
quantising the model, and writing a Parquet file that conforms to the
schema in `specs/001-llmxive-follow-up-extending-the-mirage-o/contracts/dataset.schema.yaml`.

The wrapper simply orchestrates the call and produces the additional
`dataset_stats.json` file with the shape required by the test:

  {
    "per_level_statistics": {
      "INT4": {"mean_kl": <float>},
      "INT8": {"mean_kl": <float>},
      "FP8": {"mean_kl": <float>}
    },
    "overall_non_zero_kl_significant": <bool>
  }

All paths are resolved relative to the project root using the
``llmxive_toolkit.paths`` helpers, which automatically create any
required parent directories.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _run_cli(
    model: str,
    levels: List[str],
    sample_size: int,
    output_path: Path,
) -> None:
    """
    Execute the CLI implementation of T015.

    Parameters
    ----------
    model: str
        Hugging‑Face identifier (e.g. ``distilgpt2`` or a larger model).
    levels: List[str]
        Quantisation levels – a subset of ``[\"INT4\", \"INT8\", \"FP8\"]``.
    sample_size: int
        Number of GSM8K prompts to process.
    output_path: Path
        Destination for the generated Parquet file.
    """
    cli_path = Path(__file__).parents[2] / "cli" / "generate_ground_truth.py"
    cmd = [
        sys.executable,
        str(cli_path),
        "--model",
        model,
        "--quant_levels",
        *levels,
        "--prompt_source",
        "gsm8k",
        "--sample-size",
        str(sample_size),
        "--output",
        str(output_path),
    ]

    log.info(f"Running CLI: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        log.error("CLI failed")
        log.error("STDOUT:\n%s", result.stdout)
        log.error("STDERR:\n%s", result.stderr)
        raise RuntimeError(f"generate_ground_truth CLI exited with code {result.returncode}")

def _compute_stats(df: pd.DataFrame, levels: List[str]) -> dict:
    """
    Compute the minimal statistics required by the test suite.

    Returns a dictionary matching the expected JSON schema.
    """
    per_level = {}
    for lvl in levels:
        mask = df["quantization_level"] == lvl
        if mask.any():
            per_level[lvl] = {"mean_kl": float(df.loc[mask, "kl_divergence"].mean())}
        else:
            per_level[lvl] = {"mean_kl": 0.0}

    nonzero_prop = float((df["kl_divergence"] != 0).mean())
    overall_flag = nonzero_prop > 0.05

    return {
        "per_level_statistics": per_level,
        "overall_non_zero_kl_significant": overall_flag,
    }

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def run_wrapper(
    model: str,
    levels: List[str],
    output_path: str,
    sample_size: int = 300,
) -> None:
    """
    Generate the ground‑truth dataset and accompanying statistics.

    This function is deliberately lightweight – it invokes the existing
    CLI script (which performs the heavy lifting) and then writes a JSON
    file ``dataset_stats.json`` alongside the Parquet output.

    Parameters
    ----------
    model: str
        Hugging‑Face model identifier.  The CLI falls back to
        ``distilgpt2`` if the requested model cannot be loaded, which
        keeps the integration test fast.
    levels: List[str]
        Quantisation levels to generate (e.g. ``[\"INT8\"]`` for the test).
    output_path: str
        Destination path for the Parquet file (must be writable).
    sample_size: int, optional
        Number of GSM8K prompts to process.  The default (300) matches
        the quick‑start documentation; the test passes a much smaller
        value to keep runtime low.
    """
    parquet_path = Path(output_path).expanduser().resolve()
    stats_path = parquet_path.parent / "dataset_stats.json"

    # ------------------------------------------------------------------- #
    # 1️⃣ Run the CLI to produce the Parquet dataset
    # ------------------------------------------------------------------- #
    _run_cli(
        model=model,
        levels=levels,
        sample_size=sample_size,
        output_path=parquet_path,
    )

    # ------------------------------------------------------------------- #
    # 2️⃣ Load the generated dataset and compute statistics
    # ------------------------------------------------------------------- #
    df = pd.read_parquet(parquet_path, engine="fastparquet")
    stats = _compute_stats(df, levels)

    # ------------------------------------------------------------------- #
    # 3️⃣ Write the statistics JSON to the expected location
    # ------------------------------------------------------------------- #
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)

    log.info(f"Statistics written to {stats_path}")

# --------------------------------------------------------------------------- #
# CLI entry point – allows the wrapper to be executed directly if desired.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Wrapper for T015 – generate ground‑truth dataset and stats."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging‑Face model identifier (e.g. distilgpt2).",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        required=True,
        choices=["INT4", "INT8", "FP8"],
        help="Quantisation levels to generate.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the output Parquet file.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of GSM8K prompts to process.",
    )
    args = parser.parse_args()

    run_wrapper(
        model=args.model,
        levels=args.levels,
        output_path=args.output,
        sample_size=args.sample_size,
    )
