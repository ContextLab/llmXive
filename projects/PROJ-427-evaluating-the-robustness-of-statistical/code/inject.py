"""
Injection module for the robustness evaluation pipeline.

This module provides functions to inject three types of errors into tabular
datasets:

* Random value replacement (numeric columns)
* Category misclassification (categorical columns)
* MCAR missingness (random NaNs)

After each injection the resulting CSV and a JSON side‑car containing
metadata are written to ``data/corrupted/<error_type>/``.  The metadata is
validated against ``contracts/injection.schema.yaml`` and the actual
proportion of injected rows is checked against the declared error rate.

Public API (as required by the project specification):
    - load_config
    - inject_random_replacement
    - inject_category_misclassification
    - inject_mcar_missingness
    - run_injection
    - main
"""

import argparse
import json
import logging
import os
import random
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

# --------------------------------------------------------------------------- #
# Configuration utilities
# --------------------------------------------------------------------------- #
def load_config(config_path: Path = Path("config") / "injection.yaml") -> dict:
    """
    Load the injection configuration file.

    The configuration file is expected to be a YAML document with at least
    the following keys:

    * ``error_rates`` – list of floats (e.g., [0.01, 0.05, 0.10])
    * ``seed`` – optional integer seed for reproducibility

    Returns
    -------
    dict
        Parsed configuration.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"Injection config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Basic sanity check – the schema test (T005b) already ensures the
    # structure, but we raise a clear error if something is missing.
    if "error_rates" not in cfg or not isinstance(cfg["error_rates"], list):
        raise ValueError("`error_rates` must be defined as a list of floats in the config.")
    return cfg

# --------------------------------------------------------------------------- #
# Schema handling & validation
# --------------------------------------------------------------------------- #
_SCHEMA_PATH = Path("contracts") / "injection.schema.yaml"
_SCHEMA_CACHE = None

def _load_schema() -> dict:
    """Load and cache the JSON‑schema used for injection metadata."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        if not _SCHEMA_PATH.is_file():
            raise FileNotFoundError(f"Injection schema not found at {_SCHEMA_PATH}")
        with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
            _SCHEMA_CACHE = yaml.safe_load(f)
    return _SCHEMA_CACHE

def _validate_metadata(metadata: dict) -> None:
    """
    Validate a metadata dictionary against the injection schema.

    Parameters
    ----------
    metadata : dict
        The metadata to validate.

    Raises
    ------
    jsonschema.ValidationError
        If the metadata does not conform to the schema.
    """
    schema = _load_schema()
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(metadata), key=lambda e: e.path)
    if errors:
        messages = "; ".join([f"{'/'.join(map(str, e.path))}: {e.message}" for e in errors])
        raise ValidationError(f"Metadata validation failed: {messages}")

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _add_injection_flag(df: pd.DataFrame, injected_idx: pd.Index) -> pd.DataFrame:
    """Add a boolean ``__injected`` column marking rows that were altered."""
    df = df.copy()
    df["__injected"] = False
    df.loc[injected_idx, "__injected"] = True
    return df

def _write_output(
    df: pd.DataFrame,
    output_path: Path,
    error_type: str,
    error_rate: float,
    injected_rows: int,
) -> None:
    """
    Write the injected CSV and its accompanying metadata JSON, then validate.

    Parameters
    ----------
    df : pd.DataFrame
        The injected dataframe (must contain ``__injected`` column).
    output_path : Path
        Destination CSV file path.
    error_type : str
        One of ``random_replacement``, ``category_misclassification``,
        ``mcar_missingness``.
    error_rate : float
        Declared error rate used for injection.
    injected_rows : int
        Number of rows flagged as injected.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    df.to_csv(output_path, index=False)

    # Build metadata
    metadata = {
        "error_type": error_type,
        "error_rate": error_rate,
        "total_rows": len(df),
        "injected_rows": injected_rows,
    }

    # Validate metadata against schema
    _validate_metadata(metadata)

    # Verify actual proportion matches declared rate (tolerance 1e-6)
    actual_rate = injected_rows / len(df) if len(df) > 0 else 0.0
    if abs(actual_rate - error_rate) > 1e-6:
        raise ValueError(
            f"Injected proportion mismatch for {output_path.name}: "
            f"declared {error_rate:.6f}, actual {actual_rate:.6f}"
        )

    # Write side‑car JSON
    json_path = output_path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump(metadata, jf, indent=2)

# --------------------------------------------------------------------------- #
# Injection implementations
# --------------------------------------------------------------------------- #
def inject_random_replacement(
    df: pd.DataFrame, error_rate: float, rng: random.Random
) -> pd.DataFrame:
    """
    Replace a proportion of numeric values with uniformly sampled values
    within the column's observed min/max range.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    error_rate : float
        Fraction of rows to modify (0 < error_rate < 1).
    rng : random.Random
        Random number generator (seeded for reproducibility).

    Returns
    -------
    pd.DataFrame
        Dataframe with injected values and ``__injected`` flag column.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns available for random replacement.")

    total_rows = len(df)
    n_inject = int(round(total_rows * error_rate))
    inject_idx = rng.sample(range(total_rows), n_inject)

    df_mod = df.copy()
    for col in numeric_cols:
        col_min = df_mod[col].min()
        col_max = df_mod[col].max()
        # Sample uniformly for each selected row
        replacements = [
            rng.uniform(col_min, col_max) for _ in range(n_inject)
        ]
        df_mod.loc[inject_idx, col] = replacements

    return _add_injection_flag(df_mod, pd.Index(inject_idx))

def inject_category_misclassification(
    df: pd.DataFrame, error_rate: float, rng: random.Random
) -> pd.DataFrame:
    """
    Randomly misclassify a proportion of rows for each categorical column.
    The new category is drawn from the empirical distribution of the column,
    excluding the true value.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    error_rate : float
        Fraction of rows to corrupt.
    rng : random.Random
        Random number generator.

    Returns
    -------
    pd.DataFrame
        Dataframe with misclassifications and ``__injected`` flag column.
    """
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if len(cat_cols) == 0:
        raise ValueError("No categorical columns available for misclassification.")

    total_rows = len(df)
    n_inject = int(round(total_rows * error_rate))
    inject_idx = rng.sample(range(total_rows), n_inject)

    df_mod = df.copy()
    for col in cat_cols:
        # Empirical distribution (excluding current value when sampling)
        probs = df_mod[col].value_counts(normalize=True).to_dict()
        categories = list(probs.keys())
        for row in inject_idx:
            true_val = df_mod.at[row, col]
            # Build a list of possible alternatives
            alternatives = [c for c in categories if c != true_val]
            if not alternatives:
                # Column has only one unique value – cannot misclassify
                continue
            # Sample according to empirical probabilities (renormalised)
            alt_weights = [probs[c] for c in alternatives]
            total = sum(alt_weights)
            alt_weights = [w / total for w in alt_weights]
            new_val = rng.choices(alternatives, weights=alt_weights, k=1)[0]
            df_mod.at[row, col] = new_val

    return _add_injection_flag(df_mod, pd.Index(inject_idx))

def inject_mcar_missingness(
    df: pd.DataFrame, error_rate: float, rng: random.Random
) -> pd.DataFrame:
    """
    Introduce Missing Completely At Random (MCAR) NaNs across the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    error_rate : float
        Fraction of *cells* to replace with NaN.
    rng : random.Random
        Random number generator.

    Returns
    -------
    pd.DataFrame
        Dataframe with NaNs and ``__injected`` flag column indicating rows
        that received at least one NaN.
    """
    total_cells = df.size
    n_missing = int(round(total_cells * error_rate))

    # Choose random cell coordinates
    rows = rng.choices(range(df.shape[0]), k=n_missing)
    cols = rng.choices(range(df.shape[1]), k=n_missing)

    df_mod = df.copy()
    injected_rows = set()
    for r, c in zip(rows, cols):
        df_mod.iat[r, c] = pd.NA
        injected_rows.add(r)

    return _add_injection_flag(df_mod, pd.Index(list(injected_rows)))

# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run_injection(
    raw_dir: Path = Path("data") / "raw",
    output_root: Path = Path("data") / "corrupted",
    config_path: Path = Path("config") / "injection.yaml",
    seed: int = 42,
) -> None:
    """
    Iterate over all CSV files in ``raw_dir`` and apply each injection
    strategy for every error rate defined in the configuration.

    The function writes injected CSVs and JSON metadata files to
    ``output_root/<error_type>/`` and validates them on‑the‑fly.

    Parameters
    ----------
    raw_dir : Path
        Directory containing clean CSV files.
    output_root : Path
        Base directory for injected datasets.
    config_path : Path
        Path to the injection configuration YAML.
    seed : int
        Global seed for reproducibility (overridden by config if present).
    """
    logger = logging.getLogger(__name__)
    cfg = load_config(config_path)
    error_rates = cfg["error_rates"]
    if "seed" in cfg:
        seed = cfg["seed"]
    rng = random.Random(seed)

    csv_files = list(raw_dir.rglob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in %s", raw_dir)
        return

    injection_strategies = {
        "random_replacement": inject_random_replacement,
        "category_misclassification": inject_category_misclassification,
        "mcar_missingness": inject_mcar_missingness,
    }

    for csv_path in csv_files:
        df_original = pd.read_csv(csv_path)
        for error_type, func in injection_strategies.items():
            for rate in error_rates:
                logger.info(
                    "Injecting %s (rate=%.3f) into %s",
                    error_type,
                    rate,
                    csv_path.name,
                )
                df_injected = func(df_original, rate, rng)

                injected_rows = int(df_injected["__injected"].sum())
                out_dir = output_root / error_type
                out_path = out_dir / f"{csv_path.stem}_rate{rate:.3f}.csv"

                _write_output(
                    df_injected.drop(columns="__injected"),
                    out_path,
                    error_type,
                    rate,
                    injected_rows,
                )

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject errors into raw CSV datasets."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data") / "raw",
        help="Directory containing clean CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "corrupted",
        help="Base directory for injected datasets.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config") / "injection.yaml",
        help="Path to injection configuration YAML.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run_injection(
        raw_dir=args.raw_dir,
        output_root=args.output_dir,
        config_path=args.config,
        seed=args.seed,
    )

if __name__ == "__main__":
    main()
