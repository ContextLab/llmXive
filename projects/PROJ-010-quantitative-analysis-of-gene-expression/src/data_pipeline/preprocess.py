"""
Preprocess script for the gene‑expression dynamics pipeline.

This thin wrapper invokes the core pipeline implementation located in
``code/data_pipeline.py``.  The script exists under ``src/data_pipeline`` to
match the path referenced in ``quickstart.md`` and the run‑book.

It parses the same command‑line arguments as the core implementation
(``--dataset`` and ``--output``) and forwards them by temporarily
overwriting ``sys.argv`` before calling the imported ``main`` function.

The core pipeline performs:
  * Real data download (a publicly available H5AD file)
  * QC, normalization, batch correction with Harmony
  * Gap detection, LISI calculation, variance‑explained checks
  * Writes the integrated AnnData object to the requested output path

The script exits with the same status as the core pipeline and logs
progress via the shared ``llmxive_toolkit`` logger.
"""
import argparse
import sys
from llmxive_toolkit import get_logger

# Import the core pipeline implementation.  The module lives in the
# top‑level ``code`` package.
from code.data_pipeline import main as pipeline_main

log = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command‑line arguments expected by the quickstart."""
    parser = argparse.ArgumentParser(
        description="Run the data acquisition & preprocessing pipeline."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="fetal_brain_atlas",
        help="Identifier of the dataset to download (currently ignored, kept for API compatibility).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/integrated_atlas.h5ad",
        help="Path where the integrated AnnData object will be saved.",
    )
    return parser.parse_args()

def main() -> None:
    """Entry point that forwards arguments to the core pipeline."""
    args = parse_args()
    # Preserve the original argv so we can restore it after the call.
    original_argv = sys.argv.copy()
    try:
        # Build a minimal argv list that mimics a direct call to
        # ``code/data_pipeline.py``.
        sys.argv = [
            original_argv[0],
            "--dataset",
            args.dataset,
            "--output",
            args.output,
        ]
        log.info(
            "Invoking core data pipeline with dataset=%s, output=%s",
            args.dataset,
            args.output,
        )
        pipeline_main()
    finally:
        # Restore the original argv to avoid side‑effects for any
        # subsequent code that might rely on it.
        sys.argv = original_argv

if __name__ == "__main__":
    main()
