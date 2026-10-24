"""
Data splitting utilities for molecular permeability datasets.

Implements stratified and random splitting strategies with strict validation
for polymer type stratification as required by FR‑003. Writes both CSV and
Parquet versions of the splits to satisfy downstream expectations.

The script can be invoked via the CLI:
    python code/data/split.py
"""

import json
import logging
import yaml
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

# Set up logger
log = get_logger(__name__)

def _load_config() -> dict:
    """Load configuration from config.yaml in the project root."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    if not config_path.exists():
        log.warning(f"Config file not found at {config_path}. Using defaults.")
        return {
            "staged_mode": False,
            "stratification_diff_threshold": 0.05,
            "target_column": "target",
        }

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------
# Retention check (FR‑011)
# ----------------------------------------------------------------------
def _retention_check(df: pd.DataFrame, target_col: str) -> float:
    """
    Compute the proportion of rows that contain a non‑null target value.
    The function aborts with ``SystemExit(1)`` if the retention is below
    95 %.

    Returns
    -------
    float
        Retention rate (0‑1).
    """
    total = len(df)
    if total == 0:
        log.error("Dataframe is empty – cannot compute retention.")
        raise SystemExit(1)

    valid = df.dropna(subset=[target_col])
    retention = len(valid) / total
    log.info(f"Retention check: {len(valid)}/{total} rows have a target → {retention:.2%}")

    if retention < 0.95:
        log.error(
            f"Retention {retention:.2%} is below the 95 % threshold required by FR‑011."
        )
        raise SystemExit(1)

    return retention


# ----------------------------------------------------------------------
# Bias check (FR‑013)
# ----------------------------------------------------------------------
def _bias_check(
    df: pd.DataFrame, target_col: str, corr_threshold: float = 0.85
) -> Tuple[bool, dict]:
    """
    Compute Pearson correlation between each numeric descriptor and the
    target. If any absolute correlation exceeds ``corr_threshold`` the
    function returns ``True`` for ``bias_violation`` and a mapping of the
    offending columns.

    Parameters
    ----------
    df : pd.DataFrame
        Processed data frame.
    target_col : str
        Name of the target column.
    corr_threshold : float, optional
        Absolute correlation threshold, by default 0.85.

    Returns
    -------
    Tuple[bool, dict]
        ``bias_violation`` flag and a dict ``{col: r}`` for columns that
        exceed the threshold.
    """
    if target_col not in df.columns:
        log.error(f"Target column '{target_col}' not found for bias check.")
        raise SystemExit(1)

    # Keep only numeric columns (descriptors + target)
    numeric_df = df.select_dtypes(include=[np.number])
    if target_col not in numeric_df.columns:
        log.error(f"Target column '{target_col}' is not numeric.")
        raise SystemExit(1)

    # Exclude the target itself from the correlation loop
    descriptor_cols = [c for c in numeric_df.columns if c != target_col]

    bias_violations = {}
    for col in descriptor_cols:
        # Drop rows where either column is NaN
        clean = df[[col, target_col]].dropna()
        if clean.empty:
            continue
        r, _ = pearsonr(clean[col], clean[target_col])
        if abs(r) > corr_threshold:
            bias_violations[col] = r
            log.warning(
                f"Bias violation: column '{col}' has |r|={abs(r):.3f} > {corr_threshold}"
            )

    bias_violation = len(bias_violations) > 0
    if bias_violation:
        log.error(
            f"Bias check failed – {len(bias_violations)} descriptor(s) exceed the "
            f"{corr_threshold:.2f} correlation threshold."
        )
    else:
        log.info("Bias check passed – no descriptor exceeds the correlation threshold.")

    return bias_violation, bias_violations


# ----------------------------------------------------------------------
# Existing random / stratified split helpers (unchanged)
# ----------------------------------------------------------------------
def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a simple random split of the dataframe.
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1 (exclusive).")

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    log.info(
        f"Random split completed: Train={len(train_df)}, Test={len(test_df)}"
    )
    return train_df, test_df


def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    max_distribution_diff: Optional[float] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split ensuring distribution difference < threshold.
    """
    config = _load_config()
    if max_distribution_diff is None:
        max_distribution_diff = config.get(
            "stratification_diff_threshold", 0.05
        )

    if stratify_col not in df.columns:
        log.error(
            f"Stratification column '{stratify_col}' not found in dataframe. "
            f"Available columns: {list(df.columns)}"
        )
        raise SystemExit(
            f"Stratification by {stratify_col} required by FR‑003. "
            f"Dataset lacks this metadata."
        )

    if df[stratify_col].isna().any():
        log.warning(
            f"Found NaN values in stratification column '{stratify_col}'. Dropping rows."
        )
        df = df.dropna(subset=[stratify_col])

    if df[stratify_col].nunique() < 2:
        log.error(
            f"Stratification column '{stratify_col}' has fewer than 2 unique classes."
        )
        raise ValueError(
            f"Cannot stratify by '{stratify_col}': only {df[stratify_col].nunique()} unique class found."
        )

    try:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df[stratify_col],
            shuffle=True,
        )
    except ValueError as e:
        log.error(f"Stratified split failed: {e}")
        raise SystemExit(
            f"Stratified split failed. Ensure each class in '{stratify_col}' has sufficient samples "
            f"to support a {test_size * 100:.0f}% test split."
        )

    # Validate distribution difference
    train_dist = (
        train_df[stratify_col].value_counts(normalize=True).sort_index()
    )
    test_dist = (
        test_df[stratify_col].value_counts(normalize=True).sort_index()
    )
    all_classes = train_dist.index.union(test_dist.index)
    train_dist = train_dist.reindex(all_classes, fill_value=0)
    test_dist = test_dist.reindex(all_classes, fill_value=0)

    diff = (train_dist - test_dist).abs()
    max_diff = diff.max()

    log.info(f"Stratification column: {stratify_col}")
    log.info(f"Train distribution:\n{train_dist}")
    log.info(f"Test distribution:\n{test_dist}")
    log.info(
        f"Max distribution difference: {max_diff:.4f} (threshold: {max_distribution_diff})"
    )

    if max_diff > max_distribution_diff:
        log.error(
            f"Stratification failed: Max distribution difference ({max_diff:.4f}) exceeds "
            f"threshold ({max_distribution_diff})."
        )
        raise SystemExit(
            f"Stratification validation failed. Distribution difference ({max_diff:.4f}) "
            f"exceeds allowed threshold ({max_distribution_diff})."
        )

    log.info(
        f"Stratified split successful: Train={len(train_df)}, Test={len(test_df)}"
    )
    return train_df, test_df


# ----------------------------------------------------------------------
# Report & metrics generation
# ----------------------------------------------------------------------
def _write_stratification_report(
    report_path: Path,
    retention_rate: float,
    bias_violation: bool,
    bias_details: dict,
    split_strategy: str,
    stratify_column: Optional[str],
    distribution_stats: Optional[dict],
) -> None:
    """
    Create a markdown report summarising the split procedure and
    pre‑split checks.
    """
    lines = [
        "# Data Split Report",
        "",
        "## Retention Check (FR‑011)",
        f"- Retention rate: {retention_rate:.2%}",
        f"- Requirement: ≥ 95 % → {'PASSED' if retention_rate >= 0.95 else 'FAILED'}",
        "",
        "## Bias Check (FR‑013)",
        f"- Bias violation flag: {'TRUE' if bias_violation else 'FALSE'}",
    ]

    if bias_violation:
        lines.append("- Columns exceeding correlation threshold (|r| > 0.85):")
        for col, r in bias_details.items():
            lines.append(f"  - `{col}`: r = {r:.3f}")

    lines.extend(
        [
            "",
            "## Split Strategy (FR‑003)",
            f"- Strategy used: **{split_strategy}**",
        ]
    )

    if stratify_column:
        lines.append(f"- Stratification column: `{stratify_column}`")
    else:
        lines.append("- No stratification column available; random split performed.")

    if distribution_stats:
        lines.extend(
            [
                "",
                "### Class distribution difference",
                f"- Maximum absolute percentage‑point difference: "
                f"{distribution_stats.get('max_diff', 'N/A'):.4f}",
            ]
        )
    else:
        lines.append("- Distribution statistics not applicable (random split).")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))
    log.info(f"Stratification report written to {report_path}")


def _write_metrics_json(
    metrics_path: Path,
    retention_rate: float,
    bias_violation: bool,
    bias_details: dict,
    split_strategy: str,
    stratify_column: Optional[str],
    max_distribution_diff: Optional[float],
) -> None:
    """
    Persist a JSON file that downstream steps can read.
    """
    metrics = {
        "retention_rate": retention_rate,
        "bias_violation": bias_violation,
        "bias_details": bias_details,
        "split_strategy": split_strategy,
        "stratify_column": stratify_column,
        "max_distribution_diff": max_distribution_diff,
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    log.info(f"Split metrics written to {metrics_path}")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def execute_split(
    df: pd.DataFrame,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify_column: str = "polymer_type",
) -> Tuple[str, str]:
    """
    Full split workflow implementing FR‑011, FR‑013 and FR‑003.

    Returns
    -------
    Tuple[str, str]
        Paths (as strings) to the generated ``train.csv`` and ``test.csv``.
    """
    config = _load_config()
    target_col = config.get("target_column", "target")

    # ------------------------------------------------------------------
    # 0️⃣ Filter to rows with a non‑null target (as required by the spec)
    # ------------------------------------------------------------------
    df = df.dropna(subset=[target_col])
    if df.empty:
        log.error("No rows with a non‑null target after filtering.")
        raise SystemExit(1)

    # ------------------------------------------------------------------
    # 1️⃣ Retention check
    # ------------------------------------------------------------------
    retention_rate = _retention_check(df, target_col)

    # ------------------------------------------------------------------
    # 2️⃣ Bias check
    # ------------------------------------------------------------------
    bias_violation, bias_details = _bias_check(df, target_col)

    if bias_violation:
        # Record metrics before aborting so downstream steps can see the flag.
        metrics_path = paths.data("results", "metrics.json")
        _write_metrics_json(
            metrics_path,
            retention_rate,
            bias_violation,
            bias_details,
            split_strategy="aborted_due_to_bias",
            stratify_column=None,
            max_distribution_diff=None,
        )
        raise SystemExit(
            "Bias check failed (FR‑013). Pipeline aborted as required."
        )

    # ------------------------------------------------------------------
    # 3️⃣ Split (stratified if possible, else random)
    # ------------------------------------------------------------------
    if stratify_column in df.columns:
        log.info(
            f"Found stratification column '{stratify_column}'. Performing stratified split."
        )
        train_df, test_df = stratified_split(
            df,
            stratify_col=stratify_column,
            test_size=test_size,
            random_state=random_state,
        )
        split_strategy = "stratified"
    else:
        log.warning(
            f"Stratification column '{stratify_column}' missing – falling back to random split."
        )
        train_df, test_df = random_split(
            df, test_size=test_size, random_state=random_state
        )
        split_strategy = "random (fallback)"

    # ------------------------------------------------------------------
    # 4️⃣ Persist splits (both CSV and Parquet)
    # ------------------------------------------------------------------
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    train_csv_path = output_path / "train.csv"
    test_csv_path = output_path / "test.csv"
    train_parquet_path = output_path / "train.parquet"
    test_parquet_path = output_path / "test.parquet"

    train_df.to_csv(train_csv_path, index=False)
    test_df.to_csv(test_csv_path, index=False)
    train_df.to_parquet(train_parquet_path, index=False)
    test_df.to_parquet(test_parquet_path, index=False)

    log.info(f"Split saved to CSV: {train_csv_path} and {test_csv_path}")
    log.info(f"Split saved to Parquet: {train_parquet_path} and {test_parquet_path}")
    log.info(
        f"Strategy used: {split_strategy} – Train size: {len(train_df)}, Test size: {len(test_df)}"
    )

    # ------------------------------------------------------------------
    # 5️⃣ Generate report & metrics JSON
    # ------------------------------------------------------------------
    distribution_stats = None
    max_diff = None
    if split_strategy == "stratified":
        train_dist = (
            train_df[stratify_column].value_counts(normalize=True).sort_index()
        )
        test_dist = (
            test_df[stratify_column].value_counts(normalize=True).sort_index()
        )
        all_classes = train_dist.index.union(test_dist.index)
        train_dist = train_dist.reindex(all_classes, fill_value=0)
        test_dist = test_dist.reindex(all_classes, fill_value=0)
        diff = (train_dist - test_dist).abs()
        max_diff = diff.max()
        distribution_stats = {
            "train_distribution": train_dist.to_dict(),
            "test_distribution": test_dist.to_dict(),
            "max_diff": float(max_diff),
            "threshold": config.get("stratification_diff_threshold", 0.05),
        }

    report_path = paths.data("results", "stratification_report.md")
    _write_stratification_report(
        report_path,
        retention_rate,
        bias_violation,
        bias_details,
        split_strategy,
        stratify_column if split_strategy == "stratified" else None,
        distribution_stats,
    )

    metrics_path = paths.data("results", "metrics.json")
    _write_metrics_json(
        metrics_path,
        retention_rate,
        bias_violation,
        bias_details,
        split_strategy,
        stratify_column if split_strategy == "stratified" else None,
        max_diff,
    )

    return str(train_csv_path), str(test_csv_path)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main():
    """
    CLI entry point for the split stage.
    By default reads the processed parquet file produced by the
    preprocessing step.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Split molecular data for training/testing."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=False,
        help="Path to preprocessed data (CSV or Parquet). "
             "Defaults to data/processed/processed_data.parquet",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Output directory for train/test splits",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set ratio",
    )
    parser.add_argument(
        "--stratify-col",
        type=str,
        default="polymer_type",
        help="Column to stratify by",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        # Default to the parquet file created by preprocess.py
        input_path = paths.data("processed", "processed_data.parquet")

    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        sys.exit(1)

    log.info(f"Loading data from {input_path}...")
    # Load based on file extension
    if input_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    if df.empty:
        log.error("Input dataframe is empty.")
        sys.exit(1)

    log.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    try:
        train_path, test_path = execute_split(
            df,
            output_dir=args.output,
            test_size=args.test_size,
            random_state=args.seed,
            stratify_column=args.stratify_col,
        )
        log.info(
            f"Successfully split data. Train: {train_path}, Test: {test_path}"
        )
    except SystemExit as e:
        log.error(f"Split process terminated: {e}")
        sys.exit(1)
    except Exception as e:
        log.exception(f"Unexpected error during split: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()