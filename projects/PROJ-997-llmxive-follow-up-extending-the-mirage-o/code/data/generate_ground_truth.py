"""
generate_ground_truth.py (wrapper)

Provides a convenient ``run_wrapper`` function used by the integration tests.
The wrapper invokes the CLI implementation in ``code/cli/generate_ground_truth.py``,
then computes the dataset statistics required by the downstream validation step
and writes them to ``data/processed/dataset_stats.json``.

The function is deliberately lightweight and avoids any side‑effects other than
the files it creates.  It can be called from test code or other Python scripts
without needing to spawn a new Python interpreter for the CLI, but for maximum
fidelity we invoke the CLI via ``subprocess`` so that argument parsing and logging
behave exactly as in the documented quick‑start command.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List

# Import the validation helpers so we can compute the JSON stats after the
# ground‑truth generation completes.
from cli.validate_dataset_stats import (
    load_parquet,
    compute_statistics,
    write_json,
)

def run_wrapper(
    *,
    model: str,
    levels: List[str],
    output_path: str,
    sample_size: int = 5,
    seed: int = 42,
) -> None:
    """
    Execute the ground‑truth generation pipeline and write a statistics JSON.

    Parameters
    ----------
    model: str
        Hugging‑Face model identifier (e.g. ``distilgpt2`` for the fast test).
    levels: List[str]
        Quantisation levels – a subset of ``[\"INT4\", \"INT8\", \"FP8\"]``.
    output_path: str
        Destination parquet file (e.g. ``data/processed/test_sample.parquet``).
    sample_size: int, optional
        Number of GSM8K prompts to process.  Defaults to ``5`` for quick tests.
    seed: int, optional
        Random seed for reproducibility.  Defaults to ``42``.
    """
    # Resolve absolute paths – the CLI expects a path it can write to.
    parquet_path = Path(output_path).expanduser().resolve()
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the CLI command.  We invoke the script via the current interpreter
    # to avoid any environment‑specific shebang issues.
    cli_script = (
        Path(__file__).parents[2]  # <project>/code
        / "cli"
        / "generate_ground_truth.py"
    )
    cmd = [
        sys.executable,
        str(cli_script),
        "--model",
        model,
        "--quant_levels",
        *levels,
        "--prompt_source",
        "gsm8k",
        "--output",
        str(parquet_path),
        "--sample-size",
        str(sample_size),
        "--seed",
        str(seed),
    ]

    # Run the CLI.  ``check=True`` propagates any non‑zero exit status as an
    # exception, which the test harness will surface as a failure.
    subprocess.run(cmd, check=True)

    # -----------------------------------------------------------------
    # Compute and write the statistics JSON expected by the test suite.
    # -----------------------------------------------------------------
    stats_output_path = Path("data/processed/dataset_stats.json")
    df = load_parquet(parquet_path)
    stats = compute_statistics(df)
    # The validation script also adds a SHA‑256 checksum – we reuse that
    # implementation indirectly by calling ``write_json`` which will create
    # the parent directory if needed.
    write_json(stats, stats_output_path)

# When the module is executed directly (e.g. ``python -m code.data.generate_ground_truth``)
# we forward the arguments to ``run_wrapper`` for a convenient manual run.
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Wrapper for generate_ground_truth that also writes statistics."
    )
    parser.add_argument("--model", required=True, help="HF model identifier")
    parser.add_argument(
        "--levels",
        nargs="+",
        required=True,
        choices=["INT4", "INT8", "FP8"],
        help="Quantisation levels",
    )
    parser.add_argument(
        "--output", required=True, help="Path to the output Parquet file"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of GSM8K samples to process",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    run_wrapper(
        model=args.model,
        levels=args.levels,
        output_path=args.output,
        sample_size=args.sample_size,
        seed=args.seed,
    )