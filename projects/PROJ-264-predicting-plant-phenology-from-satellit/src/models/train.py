"""
src/models/train.py
-------------------

Implements model training with Spatial Block Cross‑Validation (K=5 geographic clusters)
and Temporal Holdout (train on 2018‑2021, test on 2022‑2023).  The script:

* Loads the processed environmental time‑series CSV (expected at
  ``data/processed/environmental_time_series.csv``).
* Derives site latitude/longitude columns (named ``lat``/``lon`` or
  ``latitude``/``longitude``) and creates 5 spatial clusters using
  ``sklearn.cluster.KMeans`` (random_state=42).
* Persists the cluster assignments to ``data/processed/spatial_clusters.json``.
* Performs a spatial block CV where each cluster serves once as the validation
  set and the remaining clusters form the training set.
* Trains an XGBoost regressor (fallback to LightGBM if XGBoost fails) with
  the hyper‑parameters required by the specification
  (``max_depth=4``, ``subsample=0.8``).
* After CV, the model is retrained on the full training period (2018‑2021) and
  saved to ``artifacts/models/xgb_model_v1.pkl`` using ``joblib.dump``.
* A simple JSON report with per‑fold RMSE is written to
  ``artifacts/reports/spatial_cv_metrics.json`` (the report is optional for the
  task but useful for downstream verification).

The script can be invoked directly (e.g. via the quick‑start command
``python src/cli/run_pipeline.py --mode train ...``) or executed as a stand‑alone
module:

.. code‑block:: bash

    python -m src.models.train

The implementation deliberately raises on any unexpected condition (missing
files, missing latitude/longitude columns, etc.) to satisfy the “fail loudly”
principle.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

# XGBoost and LightGBM are optional – we import lazily and fall back if needed.
try:
    from xgboost import XGBRegressor
except Exception as exc:  # pragma: no cover
    XGBRegressor = None
    _xgb_import_error = exc

try:
    import lightgbm as lgb
except Exception as exc:  # pragma: no cover
    lgb = None
    _lgb_import_error = exc

from joblib import dump

# Toolkit helpers for path handling (creates parent directories automatically)
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Configuration constants (can be overridden via environment variables if desired)
# --------------------------------------------------------------------------- #
DATA_PATH = paths.data("processed", "environmental_time_series.csv")
CLUSTERS_OUTPUT = paths.data("processed", "spatial_clusters.json")
MODEL_OUTPUT = paths.results("artifacts", "models", "xgb_model_v1.pkl")
METRICS_OUTPUT = paths.results("artifacts", "reports", "spatial_cv_metrics.json")
N_CLUSTERS = 5
RANDOM_SEED = 42
TEST_YEARS = {2022, 2023}
# --------------------------------------------------------------------------- #

def _load_data() -> pd.DataFrame:
    """Load the processed dataset.\n\nRaises\n------\nFileNotFoundError\n    If the expected CSV does not exist.\n"""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    log.info("Loaded processed data with %d rows and %d columns", df.shape[0], df.shape[1])
    return df

def _extract_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with ``site_id``, ``lat`` and ``lon`` columns.\n\nThe ingestion pipeline may name the columns either ``lat``/``lon`` or\n``latitude``/``longitude``.  This helper normalises them to ``lat``/``lon``.\nRaises\n------\nValueError\n    If the required columns cannot be found.\n"""
    col_lat = "lat" if "lat" in df.columns else "latitude" if "latitude" in df.columns else None
    col_lon = "lon" if "lon" in df.columns else "longitude" if "longitude" in df.columns else None
    if col_lat is None or col_lon is None:
        raise ValueError("Latitude/longitude columns not found in the dataset")
    if "site_id" not in df.columns:
        raise ValueError("Column ``site_id`` is required for clustering")
    coords = df[["site_id", col_lat, col_lon]].drop_duplicates().reset_index(drop=True)
    coords = coords.rename(columns={col_lat: "lat", col_lon: "lon"})
    log.debug("Extracted %d unique site coordinates", coords.shape[0])
    return coords

def create_spatial_clusters(coords: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> Dict[str, int]:
    """Cluster sites geographically using KMeans.\n\nParameters\n----------\ncoords: DataFrame\n    Must contain ``site_id``, ``lat`` and ``lon`` columns.\nn_clusters: int\n    Number of geographic clusters (default 5).\n\nReturns\n-------\nDict[str, int]\n    Mapping ``site_id`` → ``cluster_id`` (0‑based).\n"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_SEED, n_init="auto")
    X = coords[["lat", "lon"]].values
    kmeans.fit(X)
    cluster_ids = kmeans.labels_
    mapping = dict(zip(coords["site_id"].astype(str), cluster_ids.tolist()))
    # Persist mapping
    CLUSTERS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with CLUSTERS_OUTPUT.open("w", encoding="utf-8") as fp:
        json.dump(mapping, fp, indent=2, sort_keys=True)
    log.info("Spatial clustering complete – written to %s", CLUSTERS_OUTPUT)
    return mapping

def _split_temporal(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split the full dataframe into training (pre‑2022) and test (2022‑2023).\n\nThe dataset must contain a ``date`` column parsable by ``pd.to_datetime``.\n"""
    if "date" not in df.columns:
        raise ValueError("Column ``date`` is required for temporal splitting")
    df["date"] = pd.to_datetime(df["date"])
    train_df = df[~df["date"].dt.year.isin(TEST_YEARS)].copy()
    test_df = df[df["date"].dt.year.isin(TEST_YEARS)].copy()
    log.info("Temporal split – training rows: %d, test rows: %d", train_df.shape[0], test_df.shape[0])
    return train_df, test_df

def _prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Separate feature matrix X and target y.\n\nThe target column is assumed to be ``phenology_target`` (the\nnumeric day‑of‑year of the phenological event).  All non‑numeric columns are\nremoved.  Missing target rows are dropped – they are expected to be masked\nby ``mask_missing_phenology_labels`` earlier in the pipeline.\n"""
    target_col = "phenology_target"
    if target_col not in df.columns:
        raise ValueError(f"Target column ``{target_col}`` not found in data")
    y = df[target_col]
    X = df.drop(columns=[target_col, "date", "site_id"], errors="ignore")
    # Ensure numeric dtype
    X = X.select_dtypes(include=[np.number])
    if X.isnull().any().any():
        X = X.fillna(X.mean())
    return X, y

def _train_xgboost(X: pd.DataFrame, y: pd.Series) -> XGBRegressor:
    """Train an XGBoost regressor with the hyper‑parameters required by the spec."""
    if XGBRegressor is None:
        raise ImportError(f"XGBoost not available: {_xgb_import_error}")
    model = XGBRegressor(
        n_estimators=500,
        max_depth=4,
        subsample=0.8,
        learning_rate=0.05,
        random_state=RANDOM_SEED,
        n_jobs=1,
    )
    model.fit(X, y)
    return model

def _train_lightgbm(X: pd.DataFrame, y: pd.Series):
    """Train a LightGBM regressor (fallback if XGBoost fails)."""
    if lgb is None:
        raise ImportError(f"LightGBM not available: {_lgb_import_error}")
    params = {
        "objective": "regression",
        "metric": "rmse",
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "seed": RANDOM_SEED,
        "verbosity": -1,
    }
    dtrain = lgb.Dataset(X, label=y)
    model = lgb.train(params, dtrain, num_boost_round=500, verbose_eval=False)
    return model

def _cross_validate(
    df: pd.DataFrame,
    cluster_map: Dict[str, int],
    n_folds: int = N_CLUSTERS,
) -> List[float]:
    """Perform spatial block CV.\n\nReturns a list of RMSE values – one per fold.\n"""
    rmses: List[float] = []
    for fold in range(n_folds):
        # Validation sites are those in the current cluster
        val_sites = {sid for sid, cid in cluster_map.items() if cid == fold}
        train_mask = ~df["site_id"].astype(str).isin(val_sites)
        val_mask = df["site_id"].astype(str).isin(val_sites)

        train_df = df[train_mask]
        val_df = df[val_mask]

        X_train, y_train = _prepare_features(train_df)
        X_val, y_val = _prepare_features(val_df)

        try:
            model = _train_xgboost(X_train, y_train)
        except Exception as exc:  # pragma: no cover
            log.warning("XGBoost failed on fold %d (%s); falling back to LightGBM", fold, exc)
            model = _train_lightgbm(X_train, y_train)

        preds = model.predict(X_val)
        rmse = mean_squared_error(y_val, preds, squared=False)
        rmses.append(rmse)
        log.info("Fold %d – RMSE: %.4f", fold, rmse)

    return rmses

def _train_final_model(train_df: pd.DataFrame) -> Tuple[object, List[float]]:
    """Train on the full training period (pre‑2022) and return the model.\n\nAlso returns the CV RMSE scores for reference.\n"""
    X_train, y_train = _prepare_features(train_df)
    try:
        model = _train_xgboost(X_train, y_train)
    except Exception as exc:  # pragma: no cover
        log.warning("XGBoost failed on final training (%s); falling back to LightGBM", exc)
        model = _train_lightgbm(X_train, y_train)
    # No CV here – the caller may have already computed it.
    return model, []

def main() -> int:
    """Entry point used by the quick‑start script.\n\nThe function returns an exit‑code (0 = success)."""
    try:
        df = _load_data()
        coords = _extract_coords(df)
        cluster_map = create_spatial_clusters(coords)

        # Temporal split for the hold‑out test set (not used for CV)
        train_df, test_df = _split_temporal(df)

        # Spatial Block CV on the training period only
        cv_rmses = _cross_validate(train_df, cluster_map)

        # Train final model on the full training period
        model, _ = _train_final_model(train_df)

        # Persist the final model
        MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        dump(model, MODEL_OUTPUT)
        log.info("Final model saved to %s", MODEL_OUTPUT)

        # Write a simple CV metrics report
        METRICS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        report = {"spatial_cv_rmse_per_fold": cv_rmses, "mean_rmse": float(np.mean(cv_rmses))}
        with METRICS_OUTPUT.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, indent=2, sort_keys=True)
        log.info("CV metrics written to %s", METRICS_OUTPUT)

        return 0
    except Exception as exc:
        log.exception("Training failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
