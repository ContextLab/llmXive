"""
Thin end‑to‑end pipeline (T003)

This script runs a reproducible 100‑sample (actually 600‑sample to obtain a
100‑sample test set) pipeline for each of the three material datasets,
trains a baseline XGBoost regressor and the four UQ methods (GPR, MC‑Dropout,
Deep Ensemble, Split‑Conformal XGBoost), and writes the unified per‑sample
predictions to ``data/results/per_sample_errors.csv``.  It also produces a
``pipeline_run.json`` that conforms to ``specs/001-assessing-uncertainty-quantification-tec/
contracts/pipeline.schema.yaml``.

The script accepts the same CLI arguments as the quick‑start guide; arguments
that are not needed for the thin run are parsed but ignored.
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import xgboost as xgb

from llmxive_toolkit import paths, get_logger
from create_skeleton import main as skeleton_main
from download import download_all
from featurize import process_dataset
from models.gpr import run_gpr
from models.mc_dropout import run_mc_dropout
from models.deep_ensemble import run_deep_ensemble
from models.conformal import run_conformal_prediction

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _write_per_sample_errors(df: pd.DataFrame) -> None:
    """
    Write the unified per‑sample predictions DataFrame to the required CSV.
    The DataFrame must contain the columns:
    ``sample_id, dataset, method, prediction, lower_bound,
    upper_bound, ground_truth, abs_error``.
    """
    out_path = paths.data("results", "per_sample_errors.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info(f"Wrote per‑sample errors to {out_path}")

def _build_pipeline_log(steps: list, status: str, start_ts: float, end_ts: float) -> dict:
    """
    Construct a JSON object that satisfies the pipeline schema.
    """
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "steps": steps,
        "memory_peak_mb": round(psutil.Process().memory_info().rss / (1024 ** 2), 2),
        "total_duration_seconds": round(end_ts - start_ts, 2),
    }

def _write_pipeline_log(log_dict: dict) -> None:
    out_path = paths.data("results", "pipeline_run.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(log_dict, indent=2))
    log.info(f"Wrote pipeline log to {out_path}")

# ----------------------------------------------------------------------
# Model runners
# ----------------------------------------------------------------------
def _run_xgboost(X_train, y_train, X_test, y_test):
    """Train a simple XGBoost regressor and return a DataFrame with
    prediction, lower_bound, upper_bound (both set to the point prediction)."""
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        objective="reg:squarederror",
        n_jobs=1,
        random_state=42,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    df = pd.DataFrame({
        "prediction": preds,
        "lower_bound": preds,
        "upper_bound": preds,
        "ground_truth": y_test.values,
    })
    return df

def _run_method(method_name: str, data_dict: dict, extra_args: dict):
    """
    Dispatch to the appropriate model runner based on ``method_name``.
    Returns a DataFrame with the required columns (prediction, lower_bound,
    upper_bound, ground_truth) or ``None`` on failure.
    """
    if method_name == "xgboost":
        return _run_xgboost(
            data_dict["X_train"], data_dict["y_train"],
            data_dict["X_test"], data_dict["y_test"]
        )
    elif method_name == "gpr":
        return run_gpr(
            data_dict["X_train"], data_dict["y_train"],
            data_dict["X_test"], data_dict["y_test"]
        )
    elif method_name == "mc_dropout":
        return run_mc_dropout(
            {
                "X_train": data_dict["X_train"],
                "y_train": data_dict["y_train"],
                "X_test": data_dict["X_test"],
                "y_test": data_dict["y_test"],
            },
            dataset_name=data_dict.get("dataset_name", "unknown"),
            max_passes=extra_args.get("mc_dropout_passes", 200),
        )
    elif method_name == "deep_ensemble":
        return run_deep_ensemble(
            data_dict["X_train"], data_dict["y_train"],
            data_dict["X_test"], data_dict["y_test"]
        )
    elif method_name == "conformal":
        return run_conformal_prediction(
            data_dict["X_train"], data_dict["y_train"],
            data_dict["X_test"], data_dict["y_test"]
        )
    else:
        raise ValueError(f"Unsupported method: {method_name}")

# ----------------------------------------------------------------------
# CLI parsing
# ----------------------------------------------------------------------
def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thin pipeline (100‑sample subset) for T003."
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=600,
        help="Maximum number of rows per raw dataset before splitting. "
             "A value of 600 yields ~100 test samples (15 % of 600).",
    )
    parser.add_argument(
        "--mc-dropout-passes",
        type=int,
        default=200,
        help="Number of stochastic forward passes for MC‑Dropout.",
    )
    parser.add_argument(
        "--ensemble-size",
        type=int,
        default=3,
        help="Number of sub‑models for deep‑ensemble (max 3).",
    )
    parser.add_argument(
        "--coverage-sweep-start",
        type=float,
        default=0.80,
        help="Start of nominal coverage sweep (ignored in thin run).",
    )
    parser.add_argument(
        "--coverage-sweep-stop",
        type=float,
        default=0.99,
        help="End of nominal coverage sweep (ignored in thin run).",
    )
    parser.add_argument(
        "--coverage-sweep-step",
        type=float,
        default=0.01,
        help="Step size for coverage sweep (ignored in thin run).",
    )
    parser.add_argument(
        "--thin",
        action="store_true",
        help="Run the thin (100‑sample) pipeline. Equivalent to leaving defaults.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (used by downstream modules).",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    args = _parse_cli()

    # Ensure deterministic behaviour globally
    np.random.seed(args.seed)

    # ------------------------------------------------------------------
    # Step 0 – project skeleton
    # ------------------------------------------------------------------
    start_ts = time.time()
    steps = []

    log.info("Creating project skeleton (directories + schema).")
    skeleton_main()
    steps.append(
        {"step_name": "skeleton_creation", "status": "passed", "duration_seconds": 0.0}
    )

    # ------------------------------------------------------------------
    # Step 1 – download raw datasets (they may already exist)
    # ------------------------------------------------------------------
    log.info("Downloading raw datasets (if not present).")
    download_start = time.time()
    try:
        download_all()
        steps.append(
            {
                "step_name": "download_data",
                "status": "passed",
                "duration_seconds": round(time.time() - download_start, 2),
            }
        )
    except Exception as exc:
        steps.append(
            {
                "step_name": "download_data",
                "status": "failed",
                "duration_seconds": round(time.time() - download_start, 2),
                "error_message": str(exc),
            }
        )
        raise

    # ------------------------------------------------------------------
    # Step 2 – process each dataset (subset to args.max_samples rows, featurize, split)
    # ------------------------------------------------------------------
    raw_dir = paths.data("raw")
    dataset_files = sorted(raw_dir.glob("*.csv"))
    all_predictions = []  # list of DataFrames to concatenate later

    for csv_path in dataset_files:
        dataset_id = csv_path.stem  # e.g. "band_gap"
        log.info(f"Processing dataset: {dataset_id}")

        # Ensure the cap is applied for the thin run
        os.environ["MAX_SAMPLES"] = str(args.max_samples)

        proc_start = time.time()
        # ``process_dataset`` now returns the split dict directly when a single
        # dataset name is supplied.
        data_dict = process_dataset(dataset_name=dataset_id, cap=args.max_samples)
        steps.append(
            {
                "step_name": f"process_{dataset_id}",
                "status": "passed",
                "duration_seconds": round(time.time() - proc_start, 2),
            }
        )

        # Attach dataset name for downstream use
        data_dict["dataset_name"] = dataset_id

        # ----------------------------------------------------------------
        # Train/evaluate each method on the test split
        # ----------------------------------------------------------------
        methods = ["xgboost", "gpr", "mc_dropout", "deep_ensemble", "conformal"]
        for method in methods:
            method_start = time.time()
            try:
                result_df = _run_method(
                    method,
                    data_dict,
                    extra_args={
                        "mc_dropout_passes": args.mc_dropout_passes,
                        "ensemble_size": args.ensemble_size,
                    },
                )
                if result_df is None:
                    raise RuntimeError(f"{method} returned None")
            except Exception as exc:
                steps.append(
                    {
                        "step_name": f"{method}_{dataset_id}",
                        "status": "failed",
                        "duration_seconds": round(time.time() - method_start, 2),
                        "error_message": str(exc),
                    }
                )
                raise

            # Cast numeric columns to the correct dtypes (float64) to satisfy schema
            for col in ["prediction", "lower_bound", "upper_bound", "ground_truth"]:
                result_df[col] = result_df[col].astype(float)

            # Add required identifier columns
            result_df["sample_id"] = [
                f"{dataset_id}_{i}" for i in range(len(result_df))
            ]
            result_df["dataset"] = dataset_id
            result_df["method"] = method
            # Compute absolute error
            result_df["abs_error"] = np.abs(
                result_df["prediction"] - result_df["ground_truth"]
            )
            # Re‑order columns to match schema
            result_df = result_df[
                [
                    "sample_id",
                    "dataset",
                    "method",
                    "prediction",
                    "lower_bound",
                    "upper_bound",
                    "ground_truth",
                    "abs_error",
                ]
            ]
            all_predictions.append(result_df)

            steps.append(
                {
                    "step_name": f"{method}_{dataset_id}",
                    "status": "passed",
                    "duration_seconds": round(time.time() - method_start, 2),
                }
            )

    # ------------------------------------------------------------------
    # Step 3 – write unified per‑sample errors file
    # ------------------------------------------------------------------
    if not all_predictions:
        raise RuntimeError("No predictions were generated.")
    per_sample_df = pd.concat(all_predictions, ignore_index=True)
    _write_per_sample_errors(per_sample_df)
    steps.append(
        {
            "step_name": "write_per_sample_errors",
            "status": "passed",
            "duration_seconds": 0.0,
        }
    )

    # ------------------------------------------------------------------
    # Final pipeline log
    # ------------------------------------------------------------------
    end_ts = time.time()
    pipeline_log = _build_pipeline_log(
        steps=steps, status="success", start_ts=start_ts, end_ts=end_ts
    )
    _write_pipeline_log(pipeline_log)

    log.info("Thin pipeline (T003) completed successfully.")

if __name__ == "__main__":
    main()
