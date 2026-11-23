"""
save_permutation_results.py
---------------------------

This script loads the subject‑level reconfigurability metrics and the
corresponding behavioural scores (DSST), runs a permutation test that
shuffles the behavioural scores while keeping the metric values fixed,
and writes the raw permutation distribution to a TSV file.

The output file is required by task **T073** and must be created at the
exact location ``data/results/permutation_results.tsv``.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# Import public helpers from the existing analysis module.
# These functions are part of the declared API surface.
from analysis import (
    load_metrics_and_behavioral_data,
    run_permutation_test,
    calculate_permutation_p_value,
)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Output location – must match the specification exactly.
OUTPUT_TSV = Path("data/results/permutation_results.tsv")

# Number of permutations – the analysis module uses a default of 1000,
# but we expose it here for reproducibility and possible CLI use.
DEFAULT_NUM_PERMUTATIONS = 1000

# ----------------------------------------------------------------------
# Logger setup
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Basic configuration – the rest of the project uses a shared logger
    # via ``utils.setup_logger``; we keep things simple here.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )

# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def save_permutation_results(
    num_permutations: int = DEFAULT_NUM_PERMUTATIONS,
    output_path: Path = OUTPUT_TSV,
) -> None:
    """
    Run the permutation test and persist the raw results.

    Parameters
    ----------
    num_permutations : int
        Number of shuffled datasets to generate.
    output_path : pathlib.Path
        Destination of the TSV file.  Parent directories are created
        automatically if they do not exist.

    The TSV contains two columns:
        * ``shuffle_index`` – integer index of the permutation (starting at 1)
        * ``spearman_rho`` – Spearman correlation coefficient obtained for that
          shuffle.
    """
    logger.info("Loading metric and behavioural data...")
    metrics_df, behavior_series = load_metrics_and_behavioral_data()
    # ``load_metrics_and_behavioral_data`` returns a DataFrame with a column
    # named ``transition_count`` (the reconfigurability metric) and a Series
    # indexed by ``subject_id`` containing the DSST scores.

    logger.info(
        "Running permutation test with %d permutations...", num_permutations
    )
    # ``run_permutation_test`` yields a NumPy array of shape (num_permutations,)
    # containing the Spearman rho for each shuffle.
    permuted_rhos = run_permutation_test(
        metric_series=metrics_df["transition_count"],
        behaviour_series=behavior_series,
        n_permutations=num_permutations,
    )

    logger.info("Preparing DataFrame for output...")
    df = pd.DataFrame(
        {
            "shuffle_index": np.arange(1, num_permutations + 1, dtype=int),
            "spearman_rho": permuted_rhos,
        }
    )

    logger.info("Ensuring output directory exists: %s", output_path.parent)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Writing permutation results to %s", output_path)
    df.to_csv(output_path, sep="\t", index=False, float_format="%.12g")
    logger.info("Permutation results saved successfully.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Minimal CLI wrapper.

    Allows the script to be invoked directly:
        ``python code/save_permutation_results.py [--n-permutations N]``

    The quickstart documentation expects the script to run without any
    arguments, therefore we keep the default behaviour.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Save raw permutation test results to a TSV file."
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=DEFAULT_NUM_PERMUTATIONS,
        help="Number of permutations to perform (default: %(default)s).",
    )
    args = parser.parse_args()

    save_permutation_results(num_permutations=args.n_permutations)

if __name__ == "__main__":
    main()
