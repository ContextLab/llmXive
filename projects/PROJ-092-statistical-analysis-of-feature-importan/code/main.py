"""End-to-end pipeline for the feature-importance drift analysis.

Runs on the REAL UCI Electricity Load Diagrams 2011-2014 dataset:
download -> preprocess -> per-window RF training + permutation
importance -> null baseline -> pairwise drift (Spearman rho) ->
significance tests (Mann-Kendall tau, block permutation p-value),
and writes the fully integrated ``outputs/drift_metrics.csv``
(T025 / FR-006).

Compute-budget note: the full 4-year, 370-customer series is far
too large for the CPU/time budget of a single run, so the analysis
uses a REAL, well-defined sample of the real dataset: the last
8 x 30-day windows of the record and the 40 highest-variance
active customer columns as features, with the system aggregate
load (row mean over all 370 customers) as the regression target.
No synthetic data is ever generated.
"""
import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from utils.config import get_config
from utils.logger import get_logger
from download import download_file
from train_and_importance import (
    train_model,
    evaluate_model,
    validate_model_performance,
    calculate_importance,
)
from utils.stats_aggregator import calculate_stability_metrics, save_stability_report
import drift_analysis
import null_baseline
import significance_test

# ------------------------------------------------------------------
# Constants (per spec / plan)
# ------------------------------------------------------------------
WINDOW_SIZE_DAYS = 30
MIN_R2_SCORE = 0.8
MIN_VARIANCE_THRESHOLD = 1e-7
RANDOM_SEED = 42
N_WINDOWS = 8                # real sample: last 8 x 30-day windows
N_FEATURES = 40              # real sample: top-variance customers
ROWS_PER_WINDOW = 96 * WINDOW_SIZE_DAYS  # 15-minute resolution
NUM_SHUFFLES = 100           # SC-004: multiple shuffled runs

DATASET_URLS = [
    "https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip",
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip",
]

logger = get_logger("main")


def ensure_directories(base_path: Path) -> None:
    """Ensure required output directories exist."""
    for d in (
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "outputs",
        base_path / "figures",
    ):
        d.mkdir(parents=True, exist_ok=True)


def acquire_raw_data(raw_dir: Path) -> Path:
    """Download (if needed) and extract the REAL UCI dataset.

    Fails loudly if the real source is unreachable — no synthetic
    fallback is ever used.
    """
    txt_candidates = sorted(raw_dir.rglob("LD2011_2014.txt"))
    if txt_candidates:
        return txt_candidates[0]

    zip_path = raw_dir / "electricity_load_diagrams.zip"
    if not zip_path.exists():
        ok = False
        for url in DATASET_URLS:
            logger.info("Downloading real UCI dataset from %s ...", url)
            ok = download_file(url, zip_path, chunk_size=1 << 20, timeout=300)
            if ok:
                break
        if not ok or not zip_path.exists():
            raise RuntimeError(
                "Data Source Unreachable: could not download the UCI "
                "Electricity Load Diagrams dataset from any known mirror."
            )

    logger.info("Extracting %s ...", zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".txt")]
        if not members:
            raise RuntimeError(f"No .txt data file inside archive {zip_path}")
        zf.extract(members[0], raw_dir)

    txt_candidates = sorted(raw_dir.rglob("LD2011_2014.txt"))
    if not txt_candidates:
        raise RuntimeError("Extraction finished but LD2011_2014.txt not found.")
    return txt_candidates[0]


def load_and_prepare(txt_path: Path) -> pd.DataFrame:
    """Load the real dataset and build the analysis frame.

    - semicolon-separated, comma-decimal UCI format
    - median imputation for missing values (FR-002)
    - target = aggregate system load (row mean over all customers)
    - features = the N_FEATURES highest-variance active customers
      over the sampled time range (real measured columns)
    """
    logger.info("Loading real dataset from %s ...", txt_path)
    df = pd.read_csv(
        txt_path, sep=";", index_col=0, parse_dates=True, decimal=","
    )
    df = df.sort_index()
    logger.info("Full dataset shape: %s", df.shape)

    # Real sample: the most recent N_WINDOWS * 30 days (all
    # customers active in this period).
    n_rows = N_WINDOWS * ROWS_PER_WINDOW
    sub = df.tail(n_rows).copy()
    del df

    # Median imputation (FR-002)
    medians = sub.median()
    sub = sub.fillna(medians)

    # Aggregate system load target (real measurement)
    sub["total_load"] = sub.mean(axis=1)

    variances = sub.var()
    active = [
        c for c in sub.columns
        if c != "total_load" and variances.get(c, 0.0) > MIN_VARIANCE_THRESHOLD
    ]
    if len(active) < N_FEATURES:
        raise RuntimeError(
            f"Only {len(active)} active feature columns in the sampled range."
        )
    # Highest-variance customers as features
    active.sort(key=lambda c: variances[c], reverse=True)
    feature_cols = active[:N_FEATURES]

    data = sub[feature_cols + ["total_load"]].copy()
    logger.info(
        "Analysis frame: %d rows, %d features + aggregate-load target",
        len(data), len(feature_cols),
    )
    return data, feature_cols


def split_windows(data: pd.DataFrame) -> List[pd.DataFrame]:
    """Split into non-overlapping sequential 30-day windows (FR-002)."""
    per_window = len(data) // N_WINDOWS
    if per_window < 100:
        raise RuntimeError("Not enough rows per 30-day window.")
    windows = [
        data.iloc[i * per_window:(i + 1) * per_window]
        for i in range(N_WINDOWS)
    ]
    logger.info("Split data into %d windows of %d rows.", len(windows), per_window)
    return windows


def process_window(
    window_idx: int,
    window_data: pd.DataFrame,
    feature_cols: List[str],
    output_row_index: int,
) -> Dict[str, Any] | None:
    """Train RF on one window, validate R^2, compute permutation importance.

    Returns a result dict on success, None when the window is
    skipped (R^2 < 0.8, FR-003b) or has no usable features.
    """
    window_id = f"window_{window_idx:03d}"
    logger.info("Processing %s ...", window_id)

    # Per-window variance check (drop zero-variance features)
    var = window_data[feature_cols].var()
    keep = [c for c in feature_cols if var[c] > MIN_VARIANCE_THRESHOLD]
    dropped = [c for c in feature_cols if c not in keep]
    if dropped:
        logger.warning("%s: dropping zero-variance features: %s", window_id, dropped)
    if len(keep) < 2:
        logger.warning("%s: fewer than 2 usable features, skipping.", window_id)
        return None

    X = window_data[keep].to_numpy(dtype=np.float64)
    y = window_data["total_load"].to_numpy(dtype=np.float64)

    model = train_model(X, y, RANDOM_SEED)
    r2 = evaluate_model(model, X, y)

    if not validate_model_performance(r2, MIN_R2_SCORE):
        logger.warning("%s: Model Failure — window skipped (FR-003b).", window_id)
        return None

    importance = calculate_importance(model, X, y, keep)
    return {
        "window_id": window_id,
        "seq": output_row_index,
        "r2_score": float(r2),
        "importance": importance,
    }


def integrate_final_metrics(drift_csv: Path) -> Dict[str, Any]:
    """T025 / FR-006: integrate Spearman rho, Kendall tau and the
    block-permutation p-value into the final drift_metrics.csv."""
    rhos = significance_test.load_correlation_sequence(str(drift_csv))
    if len(rhos) < 2:
        raise RuntimeError("Fewer than 2 rho values — cannot run trend tests.")

    tau, trend_direction, mk_p = significance_test.mann_kendall_test(rhos)
    small = significance_test.is_small_sample(rhos)
    p_value = significance_test.block_permutation_test(rhos)
    if small:
        logger.info(
            "Small sample (n=%d < 10): relying on block permutation "
            "p-value (FR-008 / T024).", len(rhos)
        )

    with open(drift_csv, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"{drift_csv} contains no rows.")

    fieldnames = list(rows[0].keys())
    for col in ("kendall_tau", "trend_direction", "p_value", "mann_kendall_p_value"):
        if col not in fieldnames:
            fieldnames.append(col)

    for row in rows:
        row["kendall_tau"] = f"{tau:.6f}"
        row["trend_direction"] = trend_direction
        row["p_value"] = f"{p_value:.6f}"
        row["mann_kendall_p_value"] = f"{mk_p:.6f}"

    with open(drift_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(
        "Integrated metrics: Kendall tau=%.4f (%s), block permutation "
        "p-value=%.4f written to %s",
        tau, trend_direction, p_value, drift_csv,
    )
    return {
        "kendall_tau": tau,
        "trend_direction": trend_direction,
        "p_value": p_value,
        "n_pairs": len(rhos),
    }


def run_pipeline(config_path: str | None = None) -> Dict[str, Any]:
    config = get_config(config_path)
    root = Path(config.project_root)
    ensure_directories(root)
    outputs = root / "outputs"

    logger.info("Starting pipeline execution...")

    # Step 1: acquire REAL data
    txt_path = acquire_raw_data(root / "data" / "raw")

    # Step 2: load / preprocess
    data, feature_cols = load_and_prepare(txt_path)
    windows = split_windows(data)

    # Step 3: per-window training + permutation importance
    results = []
    for idx, w in enumerate(windows):
        res = process_window(idx, w, feature_cols, len(results))
        if res is not None:
            results.append(res)

    if len(results) < 2:
        raise RuntimeError(
            f"Only {len(results)} windows passed R^2 validation; "
            "drift analysis needs at least 2."
        )
    logger.info(
        "Successful windows: %d/%d", len(results), len(windows)
    )

    # Step 4: write importance_profiles.csv
    profiles_path = outputs / "importance_profiles.csv"
    with open(profiles_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["window_id", "feature_name", "importance_score"]
        )
        writer.writeheader()
        for res in results:
            for name, d in res["importance"].items():
                writer.writerow(
                    {
                        "window_id": res["seq"],
                        "feature_name": name,
                        "importance_score": f"{d['mean_importance']:.8f}",
                    }
                )
    logger.info("Wrote %s", profiles_path)

    # Step 5: stability metrics (SC-003 / T012b)
    stability = calculate_stability_metrics(
        [{"r2_score": r["r2_score"]} for r in results]
    )
    save_stability_report(stability, outputs / "stability_report.json")

    # Step 6: null baseline via window shuffling (FR-007, SC-004)
    null_result = null_baseline.run_null_baseline(
        profiles_path, num_shuffles=NUM_SHUFFLES, seed=RANDOM_SEED
    )
    null_baseline.save_null_baseline(null_result, outputs / "null_baseline.json")

    # Step 7: pairwise drift (Spearman rho, FR-004)
    drift_csv = outputs / "drift_metrics.csv"
    drift_analysis.run_drift_analysis(
        str(profiles_path),
        str(outputs / "null_baseline.json"),
        "",
        str(drift_csv),
    )

    # Step 8: T025 — integrate tau / p-value into final drift_metrics.csv
    integrated = integrate_final_metrics(drift_csv)

    summary = {
        "status": "success",
        "total_windows": len(windows),
        "successful_windows": len(results),
        "failed_windows": len(windows) - len(results),
        "stability_metrics": stability,
        "integrated_metrics": integrated,
        "outputs": {
            "importance_profiles": str(profiles_path),
            "null_baseline": str(outputs / "null_baseline.json"),
            "drift_metrics": str(drift_csv),
            "stability_report": str(outputs / "stability_report.json"),
        },
    }
    with open(outputs / "pipeline_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Pipeline completed. Summary saved to outputs/pipeline_summary.json")
    return summary


def main() -> None:
    try:
        result = run_pipeline()
        print(
            f"Pipeline completed successfully. Processed "
            f"{result['successful_windows']}/{result['total_windows']} windows."
        )
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error in pipeline: %s", e, exc_info=True)
        print(f"Fatal error in pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()