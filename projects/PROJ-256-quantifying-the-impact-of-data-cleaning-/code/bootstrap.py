"""
Bootstrap utilities for the project.

This module provides a single public function `run_bootstrap` that performs
a bootstrap resampling procedure on a given dataset using a supplied
statistic function.  All bootstrap calls in the codebase must respect the
global configuration value ``config.BOOTSTRAP_ITERATIONS`` and must **not**
contain any fallback or conditional reduction logic.

The implementation relies on the central ``config`` module for the
iteration count, making the behaviour consistent across the entire
pipeline and satisfying the verification task T1220.
"""

import logging
import random
from pathlib import Path
from typing import Callable, List, Any, Dict, Tuple

import numpy as np
import pandas as pd

# Import the project configuration.  ``get_config`` returns the singleton
# ``Config`` instance which provides a ``get`` method for accessing stored
# values (see ``code/config.py``).
from config import get_config

logger = logging.getLogger(__name__)

def _default_iterations() -> int:
    """
    Retrieve the number of bootstrap iterations from the global
    configuration.  The configuration key ``BOOTSTRAP_ITERATIONS`` is
    defined in ``code/config.py`` (default 1000).  If the key is missing,
    a clear ``KeyError`` is raised – this is intentional because the
    pipeline must fail loudly rather than silently fall back to a
    fabricated value.
    """
    config = get_config()
    # ``Config.get`` returns ``default`` if the key is absent; we deliberately
    # do **not** supply a default here to let a missing key raise.
    iterations = config.get("BOOTSTRAP_ITERATIONS")
    if iterations is None:
        raise KeyError(
            "BOOTSTRAP_ITERATIONS not set in configuration. "
            "Define it in `code/config.py` or via environment variable."
        )
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError(
            f"Invalid BOOTSTRAP_ITERATIONS value: {iterations}. "
            "It must be a positive integer."
        )
    return iterations

def run_bootstrap(
    data: pd.DataFrame,
    statistic_func: Callable[[pd.DataFrame], Any],
    *,
    random_state: int | None = None,
    **kwargs: Any,
) -> List[Any]:
    """
    Perform bootstrap resampling on ``data`` and compute ``statistic_func``
    on each resample.

    Parameters
    ----------
    data : pd.DataFrame
        The input dataset to resample.
    statistic_func : Callable[[pd.DataFrame], Any]
        A function that computes the statistic of interest from a
        DataFrame.  It must accept a DataFrame and return a JSON‑serialisable
        value (or a Python primitive that can be stored in a list).
    random_state : int | None, optional
        Seed for reproducibility.  If ``None`` the global random state is
        used.  The seed is also propagated to ``numpy.random`` and Python's
        ``random`` module.
    **kwargs : Any
        Additional keyword arguments are **ignored** by the bootstrap core
        but are accepted for backward compatibility with older script
        signatures that may have passed an ``iterations`` argument.
        The function deliberately **does not** fall back to any alternative
        iteration count; it always uses the value from configuration.

    Returns
    -------
    List[Any]
        A list containing the statistic computed on each bootstrap sample.
    """
    # Resolve the number of iterations **once** from the configuration.
    iterations = _default_iterations()
    logger.info(
        "Running bootstrap with %d iterations (config.BOOTSTRAP_ITERATIONS)",
        iterations,
    )

    # Set seeds for reproducibility if requested.
    if random_state is not None:
        logger.debug("Setting random seed for bootstrap: %s", random_state)
        random.seed(random_state)
        np.random.seed(random_state)

    # Convert DataFrame to a NumPy array for faster indexing.
    data_array = data.to_numpy()
    n_rows = data_array.shape[0]

    if n_rows == 0:
        raise ValueError("Cannot bootstrap an empty dataset.")

    results: List[Any] = []
    for i in range(iterations):
        # Sample with replacement.
        sample_indices = np.random.randint(0, n_rows, size=n_rows)
        bootstrap_sample = pd.DataFrame(data_array[sample_indices], columns=data.columns)

        # Compute the statistic for this sample.
        try:
            stat = statistic_func(bootstrap_sample)
        except Exception as exc:
            logger.error(
                "Statistic function raised an exception on iteration %d: %s",
                i,
                exc,
            )
            raise

        results.append(stat)

    logger.info("Bootstrap completed successfully.")
    return results

# ----------------------------------------------------------------------
# Backward‑compatible entry point for scripts that previously imported
# ``main`` from this module.
# ----------------------------------------------------------------------
def main() -> None:
    """
    Minimal CLI for manual testing of the bootstrap routine.

    The command expects two positional arguments:
    1. Path to a CSV file containing the dataset.
    2. Dotted path to a callable statistic function (e.g.
       ``my_module.my_statistic``).  The callable must be importable.

    The script prints the list of bootstrap results to stdout.
    """
    import argparse
    import importlib

    parser = argparse.ArgumentParser(
        description="Run a bootstrap resampling on a CSV dataset."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the CSV dataset.")
    parser.add_argument(
        "statistic",
        type=str,
        help=(
            "Dotted path to the statistic function, e.g. "
            "'my_module.compute_metric'. The function must accept a "
            "pandas.DataFrame and return a JSON‑serialisable value."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducibility.",
    )
    args = parser.parse_args()

    # Load data.
    df = pd.read_csv(args.csv_path)

    # Dynamically import the statistic function.
    module_path, func_name = args.statistic.rsplit(".", 1)
    module = importlib.import_module(module_path)
    statistic_func = getattr(module, func_name)

    # Run bootstrap and print results.
    results = run_bootstrap(df, statistic_func, random_state=args.seed)
    print(results)

if __name__ == "__main__":
    # Allow the module to be executed directly.
    main()
