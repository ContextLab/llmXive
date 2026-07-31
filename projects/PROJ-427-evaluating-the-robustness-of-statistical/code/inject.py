import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import numpy as np
import yaml

# Import the deterministic seed setter from the project
try:
    from random_seed import set_seed
except ImportError:
    # Fallback: define a no‑op if the module is not yet present
    def set_seed(seed: int) -> None:
        pass

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def load_config() -> Dict[str, Any]:
    """
    Load the injection configuration from ``config/error_rates.yaml``.
    The file is expected to contain a top‑level ``error_rates`` key with a
    list of floating‑point values representing the proportion of rows to
    corrupt (e.g., ``[0.01, 0.05, 0.10]``).

    Returns
    -------
    dict
        Dictionary with at least the key ``error_rates``.
    """
    config_path = Path(__file__).resolve().parents[1] / "config" / "error_rates.yaml"
    if not config_path.is_file():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Missing configuration file: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict) or "error_rates" not in cfg:
        logger.error("Invalid configuration format: missing 'error_rates' key")
        raise ValueError("Configuration must contain an 'error_rates' key")

    if not isinstance(cfg["error_rates"], list) or not all(
        isinstance(v, (float, int)) for v in cfg["error_rates"]
    ):
        logger.error("'error_rates' must be a list of numbers")
        raise ValueError("'error_rates' must be a list of numbers")

    logger.info(f"Loaded error rates: {cfg['error_rates']}")
    return cfg


def inject_random_replacement(
    input_path: Path,
    output_path: Path,
    error_rate: float,
    seed: int = 42,
) -> int:
    """
    Perform random value replacement on numeric columns of a CSV file.

    For each numeric column, a proportion ``error_rate`` of its rows are
    selected uniformly at random and replaced with a value drawn from a
    uniform distribution spanning the observed column minimum and maximum.

    Parameters
    ----------
    input_path : Path
        Path to the clean CSV file.
    output_path : Path
        Destination path for the corrupted CSV.
    error_rate : float
        Fraction of rows to corrupt (0 < error_rate <= 1).
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    int
        Total number of cell modifications performed.
    """
    set_seed(seed)
    df = pd.read_csv(input_path)

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    n_rows = len(df)
    if n_rows == 0:
        logger.warning(f"Empty dataset: {input_path}")
        return 0

    total_modified = 0

    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()

        # If the column has constant value, skip replacement (nothing to vary)
        if pd.isna(col_min) or pd.isna(col_max) or col_min == col_max:
            logger.debug(f"Column '{col}' has no variation; skipping.")
            continue

        n_modify = int(np.floor(n_rows * error_rate))
        if n_modify == 0:
            logger.debug(
                f"Error rate {error_rate} results in 0 modifications for column '{col}'."
            )
            continue

        # Choose rows without replacement
        rows_to_modify = np.random.choice(
            n_rows, size=n_modify, replace=False
        )
        random_values = np.random.uniform(col_min, col_max, size=n_modify)

        df.loc[rows_to_modify, col] = random_values
        total_modified += n_modify

        logger.debug(
            f"Replaced {n_modify} values in column '{col}' with uniform random numbers "
            f"between {col_min} and {col_max}."
        )

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(
        f"Injected random replacement into {input_path.name} (rate={error_rate:.2%}); "
        f"wrote corrupted file to {output_path}"
    )
    return total_modified


def run_injection() -> None:
    """
    Iterate over all cleaned datasets and all configured error rates,
    applying random value replacement and writing the results to
    ``data/corrupted/``.
    """
    cfg = load_config()
    error_rates: List[float] = cfg["error_rates"]

    # Directories
    cleaned_dir = Path(__file__).resolve().parents[1] / "data" / "raw" / "cleaned"
    corrupted_dir = Path(__file__).resolve().parents[1] / "data" / "corrupted"

    if not cleaned_dir.is_dir():
        logger.error(f"Cleaned data directory does not exist: {cleaned_dir}")
        raise FileNotFoundError(f"Missing directory: {cleaned_dir}")

    csv_files = list(cleaned_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in {cleaned_dir}")
        return

    for csv_path in csv_files:
        stem = csv_path.stem
        for rate in error_rates:
            # Construct a deterministic seed based on file name and rate
            seed = hash((stem, rate)) % (2**32)
            out_name = f"{stem}_replace_{int(rate*100)}pct.csv"
            out_path = corrupted_dir / out_name

            try:
                inject_random_replacement(
                    input_path=csv_path,
                    output_path=out_path,
                    error_rate=rate,
                    seed=seed,
                )
            except Exception as e:
                logger.exception(
                    f"Failed to inject errors into {csv_path.name} at rate {rate}: {e}"
                )
                raise


def main(argv: List[str] | None = None) -> int:
    """
    CLI entry point.

    Optional arguments can be provided to specify a custom configuration file.
    If omitted, the default ``config/error_rates.yaml`` is used.
    """
    parser = argparse.ArgumentParser(
        description="Inject random value replacement errors into cleaned CSV datasets."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "error_rates.yaml",
        help="Path to the YAML configuration file defining error rates.",
    )
    args = parser.parse_args(argv)

    # Override the global config path if a custom one is supplied
    if args.config != Path(__file__).resolve().parents[1] / "config" / "error_rates.yaml":
        # Load the custom config directly
        if not args.config.is_file():
            logger.error(f"Custom config file not found: {args.config}")
            return 1
        with open(args.config, "r", encoding="utf-8") as f:
            custom_cfg = yaml.safe_load(f)
        # Temporarily monkey‑patch the load_config function to return the custom config
        global load_config
        def load_config() -> Dict[str, Any]:  # type: ignore
            return custom_cfg

    run_injection()
    return 0


if __name__ == "__main__":
    sys.exit(main())
