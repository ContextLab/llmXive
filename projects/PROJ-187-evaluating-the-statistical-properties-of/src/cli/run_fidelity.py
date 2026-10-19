"""Entry point for the fidelity evaluation pipeline.

This script orchestrates data loading, synthetic data generation using SDV,
and the computation of statistical fidelity metrics. It supports a '--smoke'
mode for rapid verification and a '--full' mode for the complete study.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import List

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

from src.data.loader import main as loader_main
from src.metrics.marginal import compute_marginal_metrics, detect_column_types
from src.metrics.correlation import compute_correlation_metrics
from src.models.synthesize import generate_and_save

log = get_logger(__name__)

def _load_processed_data(name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the train/hold‑out parquet files for a given dataset name."""
    train_path = paths.data("processed", name, "train.parquet")
    holdout_path = paths.data("processed", name, "holdout.parquet")
    if not train_path.is_file() or not holdout_path.is_file():
        raise FileNotFoundError(
            f"Processed files for dataset '{name}' not found: "
            f"{train_path}, {holdout_path}"
        )
    train_df = pd.read_parquet(train_path)
    holdout_df = pd.read_parquet(holdout_path)
    return train_df, holdout_df

def _compute_metrics(real_df: pd.DataFrame, synth_df: pd.DataFrame) -> List[dict]:
    """Run marginal and correlation fidelity metrics and return a flat list."""
    cont_cols, cat_cols = detect_column_types(real_df)

    # Marginal metrics
    marginal_rows = compute_marginal_metrics(
        real_df,
        synth_df,
        continuous_cols=cont_cols,
        categorical_cols=cat_cols,
    )

    # Correlation metrics
    correlation_rows = compute_correlation_metrics(
        real_df,
        synth_df,
        cols=cont_cols,
        n_permutations=1000,
        seed=42,
    )
    return marginal_rows + correlation_rows

def _augment_rows(
    rows: List[dict],
    dataset: str,
    model_name: str,
    seed: int,
) -> List[dict]:
    """Add provenance fields required by the contract schema."""
    for r in rows:
        r.update({
            "dataset": dataset,
            "model": model_name,
            "seed": seed,
        })
    return rows

def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the statistical‑fidelity pipeline."
    )
    parser.add_argument("--smoke", action="store_true", help="Run thin first pass.")
    parser.add_argument("--full", action="store_true", help="Run full grid.")
    parser.add_argument(
        "--seeds", nargs="+", type=int, default=[42, 123, 2026],
        help="Random seeds for model training / synthesis."
    )
    parser.add_argument("--max-epochs", type=int, default=30)
    parser.add_argument("--early-stopping-delta", type=float, default=0.001)
    parser.add_argument("--early-stopping-patience", type=int, default=3)
    
    args = parser.parse_args(argv)

    if args.smoke:
        log.info("Running smoke test: Adult, CTGAN, Seed 42")
        # Ensure data is loaded
        loader_main(["--datasets", "adult"])
        
        dataset_name = "adult"
        model_name = "CTGAN"
        seed = 42
        
        train_df, holdout_df = _load_processed_data(dataset_name)
        
        # Use real SDV synthesis instead of resampling
        synth_csv_path = generate_and_save(
            dataset_name=dataset_name,
            model_name=model_name,
            seed=seed,
            train_df=train_df,
            max_epochs=args.max_epochs,
            early_stopping_delta=args.early_stopping_delta,
            early_stopping_patience=args.early_stopping_patience,
        )
        
        synth_df = pd.read_csv(synth_csv_path)
        
        # Compute and augment metrics
        metric_rows = _compute_metrics(holdout_df, synth_df)
        metric_rows = _augment_rows(metric_rows, dataset_name, model_name, seed)
        
        # Write to smoke results file
        out_path = paths.outputs("metrics", "metric_results_smoke.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(metric_rows, f, indent=2, ensure_ascii=False)
        
        log.info("Smoke test complete. Results written to %s", out_path)
    
    elif args.full:
        # T005 implementation will go here
        log.info("Full grid execution not yet implemented in this task (T004).")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
