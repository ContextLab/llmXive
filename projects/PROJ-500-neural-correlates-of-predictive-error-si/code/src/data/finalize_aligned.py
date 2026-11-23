"""
finalize_aligned.py
--------------------
This script runs the finalization step for the neural correlates pipeline.
It merges the filtered aligned data (produced by T023) with the
accuracy blocks (produced by T021) and writes the final aligned dataset
to ``data/aligned_data.csv``.

The script is intended to be invoked directly from the command line,
for example:

    python code/src/data/finalize_aligned.py --data-dir data --analysis-mode error_signal
    
Parameters
----------
--data-dir : str, optional
    Path to the directory containing the pipeline intermediate files.
    Defaults to ``data`` relative to the project root.
--analysis-mode : str, optional
    Either ``error_signal`` or ``stimulus_driven``. Determines how
    under‑powered subjects are handled (exclusion vs. inclusion).
    Defaults to ``error_signal``.
"""

import argparse
from pathlib import Path

from src.data.finalize import run_finalization_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the finalization pipeline (T024) to produce aligned_data.csv"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Directory containing intermediate CSV files (default: %(default)s)",
    )
    parser.add_argument(
        "--analysis-mode",
        type=str,
        choices=["error_signal", "stimulus_driven"],
        default="error_signal",
        help="Analysis mode controlling power‑status filtering (default: %(default)s)",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    analysis_mode = args.analysis_mode
    
    try:
        output_path = run_finalization_pipeline(data_dir=data_dir, analysis_mode=analysis_mode)
        print(f"✅ Final aligned dataset written to: {output_path}")
    except Exception as exc:
        # Propagate the exception so the CI runner sees a non‑zero exit code.
        print(f"❌ Finalization failed: {exc}")
        raise


if __name__ == "__main__":
    main()
