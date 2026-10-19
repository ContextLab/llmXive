"""
Sensitivity Sweep of Persistence-Image Vectorization Resolution (Task T007, FR-006).

For each grid resolution in {10, 20, 30}:
  (a) invoke code/02_tda_computation.py --grid <g> (skipped if the CSV
      for that grid already exists on disk),
  (b) retrain the SAME models as T005 (Ridge alpha=1.0 and RandomForest
      100 trees / max_depth=10 / seed=42) on the three feature sets
      (traditional, topological, combined) using the existing
      scaffold-based 5-fold splits (data/processed/splits.json),
  (c) aggregate mean R^2 and its std per resolution.

Output:
  * reports/metrics/sensitivity_report.json  (canonical)
  * data/results/sensitivity_report.json     (durable, non-gitignored copy)

The report is a JSON list with one object per grid:
  {"grid_size": <int>, "r2_mean": <float>, "r2_std": <float>, "detail": {...}}
where ``r2_mean``/``r2_std`` summarise the per-fold R^2 of the
combined-feature models (Ridge and RandomForest averaged per fold),
and ``detail`` gives the full per-model / per-feature-set breakdown.

Note on efficiency: the traditional feature set and the splits are
identical for every grid size, so traditional-only results are computed
once and reused across resolutions (they are mathematically invariant
to the vectorization grid).
"""

import argparse
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# 04_model_training starts with a digit -> import via importlib.
# Public names used: setup_logging, check_gpu_disabled,
# select_feature_columns, train_and_evaluate, load_splits.
mt = importlib.import_module("04_model_training")

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
REPORTS_DIR = PROJECT_ROOT / "reports" / "metrics"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

FEATURE_SETS = ("traditional", "topological", "combined")
MODELS = ("linear", "rf")


def ensure_tda_features(grid: int, logger) -> Path:
    """Run code/02_tda_computation.py --grid <grid> if its CSV is missing."""
    csv_path = PROCESSED_DIR / f"topological_features_{grid}x{grid}.csv"
    if csv_path.is_file() and pd.read_csv(csv_path).shape[0] > 0:
        logger.info(f"Grid {grid}x{grid}: TDA features already present ({csv_path}).")
        return csv_path
    cmd = [sys.executable, str(CODE_DIR / "02_tda_computation.py"), "--grid", str(grid)]
    logger.info(f"Grid {grid}x{grid}: running TDA computation: {' '.join(cmd)}")
    rc = subprocess.run(cmd).returncode
    if rc != 0 or not csv_path.is_file():
        raise RuntimeError(
            f"TDA computation for grid {grid} failed (exit code {rc})."
        )
    return csv_path


def load_base_frame() -> pd.DataFrame:
    """Combined feature matrix without pixel columns (traditional + target)."""
    path = PROCESSED_DIR / "combined_features.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path} - run T004 first.")
    df = pd.read_csv(path, low_memory=False)
    df["molecule_id"] = df["molecule_id"].astype(str)
    non_pixel = [c for c in df.columns if not c.startswith("pixel_")]
    return df[non_pixel].copy()


def build_grid_frame(base: pd.DataFrame, grid: int) -> pd.DataFrame:
    """Left-merge the grid's pixel columns onto the base frame (order preserved)."""
    topo_path = PROCESSED_DIR / f"topological_features_{grid}x{grid}.csv"
    topo = pd.read_csv(topo_path, low_memory=False)
    topo["molecule_id"] = topo["molecule_id"].astype(str)
    pixel_cols = [c for c in topo.columns if c.startswith("pixel_")]
    if not pixel_cols:
        raise ValueError(f"No pixel_ columns in {topo_path}.")
    keep = topo[["molecule_id"] + pixel_cols].copy()
    df = base.merge(keep, on="molecule_id", how="left")
    if df[pixel_cols].isnull().any().any():
        missing = int(df[pixel_cols].isnull().sum().sum())
        raise ValueError(
            f"{missing} missing topological values after merge for grid {grid} "
            "- molecule_id sets differ between combined_features.csv and the TDA output."
        )
    return df


def evaluate_feature_set(
    X: np.ndarray,
    y: np.ndarray,
    splits,
    logger,
    label: str,
) -> Dict[str, Dict[str, List[float]]]:
    """Train Ridge and RF across the 5 scaffold folds; return per-fold R^2."""
    out: Dict[str, Dict[str, List[float]]] = {}
    for model_type in MODELS:
        r2s: List[float] = []
        for fold_idx, (tr, te) in enumerate(splits):
            r2, _rmse, _model = mt.train_and_evaluate(
                X[tr], y[tr], X[te], y[te], model_type
            )
            r2s.append(r2)
            logger.info(f"  [{label}] {model_type} fold {fold_idx}: R2={r2:.4f}")
        out[model_type] = {"r2_per_fold": r2s}
    return out


def summarise(per_model: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, float]]:
    return {
        m: {
            "r2_mean": float(np.mean(v["r2_per_fold"])),
            "r2_std": float(np.std(v["r2_per_fold"])),
            "r2_per_fold": [float(x) for x in v["r2_per_fold"]],
        }
        for m, v in per_model.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sensitivity sweep of persistence-image grid resolution (FR-006)."
    )
    parser.add_argument(
        "--grids", type=int, nargs="+", default=[10, 20, 30],
        help="Grid resolutions to sweep (default: 10 20 30).",
    )
    args = parser.parse_args()
    grids: List[int] = sorted(set(int(g) for g in args.grids))
    if len(grids) < 3:
        print("Warning: FR-006 expects at least three grid resolutions.")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = mt.setup_logging(LOGS_DIR / "sensitivity.log")
    logger.info("=== Sensitivity Analysis (Task T007, FR-006) ===")
    logger.info(f"Grid resolutions: {grids}")

    # FR-008: CPU-only guard (reuses the dependency-free check from T005).
    mt.check_gpu_disabled()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    base = load_base_frame()
    logger.info(
        f"Base frame: {base.shape[0]} rows x {base.shape[1]} cols (traditional + target)."
    )
    if "logP" not in base.columns:
        raise ValueError("Target column 'logP' missing from combined_features.csv.")
    y = pd.to_numeric(base["logP"], errors="coerce")
    if y.isna().any():
        raise ValueError(f"{int(y.isna().sum())} non-numeric logP values.")
    y = y.values

    splits = mt.load_splits(logger)
    n = len(base)
    for tr, te in splits:
        if tr.max(initial=-1) >= n or te.max(initial=-1) >= n:
            raise ValueError("Split indices exceed base frame row count.")

    # ------------------------------------------------------------------
    # Traditional-only results are grid-invariant -> compute once.
    # ------------------------------------------------------------------
    _all_cols, _tda_cols, trad_cols = mt.select_feature_columns(base)
    if not trad_cols:
        raise ValueError("No traditional feature columns found.")
    logger.info(f"Traditional features ({len(trad_cols)} cols): training once (grid-invariant).")
    X_trad = (
        base[trad_cols].apply(pd.to_numeric, errors="coerce").astype(float).values
    )
    trad_results = evaluate_feature_set(X_trad, y, splits, logger, "traditional")

    # ------------------------------------------------------------------
    # Per-grid sweep
    # ------------------------------------------------------------------
    report: List[Dict] = []
    start = time.time()
    for grid in grids:
        logger.info(f"--- Grid {grid}x{grid} ---")
        ensure_tda_features(grid, logger)
        df = build_grid_frame(base, grid)

        _all_cols, tda_cols, _trad = mt.select_feature_columns(df)
        if not tda_cols:
            raise ValueError(f"No topological columns for grid {grid}.")
        logger.info(
            f"Grid {grid}: topological={len(tda_cols)} cols, "
            f"combined={len(_all_cols)} cols."
        )

        detail: Dict[str, Dict] = {
            "traditional": summarise(trad_results)
        }

        X_topo = (
            df[tda_cols].apply(pd.to_numeric, errors="coerce").astype(float).values
        )
        detail["topological"] = summarise(
            evaluate_feature_set(X_topo, y, splits, logger, f"topological_{grid}")
        )

        X_comb = (
            df[_all_cols].apply(pd.to_numeric, errors="coerce").astype(float).values
        )
        comb = evaluate_feature_set(X_comb, y, splits, logger, f"combined_{grid}")
        detail["combined"] = summarise(comb)

        # Headline metric: per-fold R^2 of the combined-feature models
        # (Ridge and RandomForest averaged within each fold).
        per_fold_combined = [
            0.5 * (comb["linear"]["r2_per_fold"][i] + comb["rf"]["r2_per_fold"][i])
            for i in range(len(splits))
        ]
        entry = {
            "grid_size": int(grid),
            "r2_mean": float(np.mean(per_fold_combined)),
            "r2_std": float(np.std(per_fold_combined)),
            "r2_per_fold_combined": [float(v) for v in per_fold_combined],
            "detail": detail,
        }
        report.append(entry)
        logger.info(
            f"Grid {grid}: combined r2_mean={entry['r2_mean']:.4f} "
            f"(std {entry['r2_std']:.4f})"
        )

    elapsed = time.time() - start

    # ------------------------------------------------------------------
    # Write reports (canonical + durable copy)
    # ------------------------------------------------------------------
    payload = {
        "task": "T007",
        "sensitivity": report,
        "metadata": {
            "seed": mt.SEED,
            "n_folds": len(splits),
            "split_method": "scaffold_based_5fold",
            "models": {
                "linear": {"type": "Ridge", "alpha": mt.LINEAR_ALPHA},
                "rf": {"type": "RandomForestRegressor",
                       "n_estimators": mt.RF_TREES,
                       "max_depth": mt.RF_MAX_DEPTH,
                       "random_state": mt.SEED},
            },
            "target_property": "logP",
            "n_molecules": int(n),
            "elapsed_seconds": float(elapsed),
        },
    }

    canonical = REPORTS_DIR / "sensitivity_report.json"
    with canonical.open("w") as f:
        json.dump(payload, f, indent=2)
    durable = RESULTS_DIR / "sensitivity_report.json"
    with durable.open("w") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"Sensitivity report written to {canonical}")
    logger.info(f"Durable copy written to {durable}")
    logger.info(f"Sensitivity sweep completed in {elapsed:.2f} seconds.")

    # Sanity check: three numeric fields per entry (task verification).
    for e in report:
        assert isinstance(e["grid_size"], int)
        assert isinstance(e["r2_mean"], float) and np.isfinite(e["r2_mean"])
        assert isinstance(e["r2_std"], float) and np.isfinite(e["r2_std"])
    print(f"Sensitivity analysis complete: {len(report)} grid resolutions evaluated.")


if __name__ == "__main__":
    main()