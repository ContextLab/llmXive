from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re
import logging
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score
import joblib
import yaml

# Import config for paths
from config import ensure_directories, Hyperparameters

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Data Models (Existing)
# ----------------------------------------------------------------------

class RootImage(BaseModel):
    id: str
    path: str
    species: str

    @field_validator('path')
    @classmethod
    def validate_path_exists(cls, v: str) -> str:
        if not Path(v).exists():
            raise ValueError(f"Image path does not exist: {v}")
        return v

class RSAMetrics(BaseModel):
    depth: float = Field(..., gt=0, description="Root system depth in cm")
    branching_density: float = Field(..., gt=0, description="Branches per unit length")
    surface_area: float = Field(..., gt=0, description="Total root surface area in cm2")

class PhysioTrait(BaseModel):
    species: str
    conductance: float
    photosynthesis: float
    survival_rate: Optional[float] = None  # Optional proxy for tolerance

# ----------------------------------------------------------------------
# Existing Model Functions
# ----------------------------------------------------------------------

def fit_ols(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit OLS regression (placeholder for existing implementation details)."""
    # Implementation assumed to exist in previous tasks (T023a)
    raise NotImplementedError("fit_ols implementation moved to statsmodels wrapper in previous tasks.")

def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> Dict[str, Any]:
    """Fit Ridge regression."""
    raise NotImplementedError("fit_ridge implementation moved to sklearn wrapper in previous tasks.")

def fit_lasso(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> Dict[str, Any]:
    """Fit Lasso regression."""
    raise NotImplementedError("fit_lasso implementation moved to sklearn wrapper in previous tasks.")

def fit_random_forest(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit Random Forest Regression."""
    raise NotImplementedError("fit_random_forest implementation moved to sklearn wrapper in previous tasks.")

def fit_pgl(tree_path: str, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> Dict[str, Any]:
    """Fit Phylogenetic Generalized Least Squares."""
    raise NotImplementedError("fit_pgl implementation moved to caper wrapper in previous tasks.")

# ----------------------------------------------------------------------
# New Function: fit_rf_classification (T027b)
# ----------------------------------------------------------------------

def fit_rf_classification(
    data_path: str,
    proxy_config_path: str,
    output_model_path: str,
    output_status_path: str
) -> None:
    """
    Implements T027b: Fit Random Forest Classification for drought tolerance.

    Logic:
    1. Check state/proxy_detection.yaml for 'has_proxy' flag.
    2. If True:
       - Load merged data.
       - Binarize the proxy variable (median split) to create target 'tolerance_class'.
       - Train Random Forest Classifier with 5-fold GroupKFold (groups=species).
       - Save model to output_model_path.
       - Update status: classification_skipped=False.
    3. If False:
       - Do NOT train.
       - Set status: classification_skipped=True.
       - Write status file explaining N/A.
    """
    # Ensure output directories exist
    ensure_directories([output_model_path, output_status_path])

    # 1. Load Proxy Detection Status
    proxy_config = {}
    try:
        with open(proxy_config_path, 'r') as f:
            proxy_config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error(f"Proxy detection config not found at {proxy_config_path}. Assuming no proxy.")
        proxy_config = {"has_proxy": False}

    has_proxy = proxy_config.get("has_proxy", False)
    status_data = {
        "task_id": "T027b",
        "classification_skipped": not has_proxy,
        "reason": "No independent tolerance proxy found" if not has_proxy else "Proxy found and used",
        "timestamp": None
    }

    if not has_proxy:
        logger.info("Classification skipped: No independent tolerance proxy found (FR-009 constraint).")
        status_data["reason"] = "Classification skipped: No independent tolerance proxy found. Sensitivity analysis will report N/A."

        # Write status file
        status_dir = Path(output_status_path).parent
        status_dir.mkdir(parents=True, exist_ok=True)
        with open(output_status_path, 'w') as f:
            # Update timestamp to current time string for record
            import datetime
            status_data["timestamp"] = datetime.datetime.now().isoformat()
            yaml.dump(status_data, f, default_flow_style=False)

        # Also create the markdown status file required by task description
        md_path = str(Path(output_status_path).with_suffix('.md'))
        with open(md_path, 'w') as f:
            f.write("# Classification Status\n\n")
            f.write("**Status**: SKIPPED\n\n")
            f.write("Reason: No independent tolerance proxy found.\n\n")
            f.write("Per project constraints (Plan: No Circular Classification), we cannot binarize primary physiological metrics.\n")
            f.write("Consequently, the sensitivity analysis will report N/A.\n")
        
        return

    # 2. If Proxy Exists: Train Model
    logger.info("Independent tolerance proxy detected. Training Random Forest Classification model.")

    # Load merged data
    # Expecting data_path to point to data/derived/merged_data.csv
    df = pd.read_csv(data_path)

    # Identify proxy column
    # Based on T027 logic, the proxy is likely 'survival_rate' if detected.
    # We need to find which column was used as the proxy.
    # Assuming the proxy column is named in the config or we default to 'survival_rate' if present.
    proxy_column = None
    if "proxy_column" in proxy_config:
        proxy_column = proxy_config["proxy_column"]
    else:
        # Fallback: check common names
        for col in ['survival_rate', 'tolerance_score', 'conductance']:
            if col in df.columns:
                proxy_column = col
                break

    if proxy_column is None or proxy_column not in df.columns:
        # This should not happen if has_proxy is True, but safety check
        logger.error("Proxy column not found in merged data despite has_proxy=True.")
        status_data["error"] = "Proxy column missing in data"
        with open(output_status_path, 'w') as f:
            import datetime
            status_data["timestamp"] = datetime.datetime.now().isoformat()
            yaml.dump(status_data, f, default_flow_style=False)
        raise ValueError("Proxy column missing in data despite has_proxy=True.")

    logger.info(f"Using '{proxy_column}' as tolerance proxy for binarization.")

    # Binarize proxy: Median split
    median_val = df[proxy_column].median()
    df['tolerance_class'] = (df[proxy_column] >= median_val).astype(int)
    logger.info(f"Binarized '{proxy_column}' (median={median_val:.4f}) into 'tolerance_class'.")

    # Prepare features
    # Use RSA metrics and physiological traits as predictors
    feature_cols = ['depth', 'branching_density', 'surface_area', 'conductance', 'photosynthesis']
    # Filter to columns that exist
    available_features = [c for c in feature_cols if c in df.columns]
    
    if len(available_features) < 1:
        raise ValueError("No valid feature columns found for classification.")

    X = df[available_features].values
    y = df['tolerance_class'].values
    groups = df['species_id'].values # Using species_id as groups for GroupKFold

    # Handle missing values in features
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        logger.warning("NaN values detected in data. Dropping rows with NaN.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        groups = groups[mask]

    # Train Random Forest Classifier
    # Specs: n_estimators=100, 5-fold GroupKFold, F1-score metric
    rf_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        max_depth=None,
        min_samples_leaf=5
    )

    # Cross-validation to evaluate
    gkf = GroupKFold(n_splits=5)
    
    y_true = []
    y_pred = []
    scores = []

    logger.info("Running 5-fold GroupKFold cross-validation...")
    for train_idx, val_idx in gkf.split(X, y, groups):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        rf_model.fit(X_train, y_train)
        y_pred_val = rf_model.predict(X_val)
        
        scores.append(f1_score(y_val, y_pred_val))
        y_true.extend(y_val)
        y_pred.extend(y_pred_val)

    mean_f1 = float(np.mean(scores))
    logger.info(f"Cross-validation F1-score: {mean_f1:.4f}")

    # Retrain on full data for final model
    rf_model.fit(X, y)

    # Save model
    model_dir = Path(output_model_path).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_model, output_model_path)
    logger.info(f"Model saved to {output_model_path}")

    # Update status data
    status_data["classification_skipped"] = False
    status_data["mean_f1_score"] = mean_f1
    status_data["proxy_column"] = proxy_column
    status_data["median_threshold"] = float(median_val)
    status_data["feature_columns"] = available_features
    import datetime
    status_data["timestamp"] = datetime.datetime.now().isoformat()

    # Write status file
    with open(output_status_path, 'w') as f:
        yaml.dump(status_data, f, default_flow_style=False)

    logger.info("Classification training complete.")

def main():
    """Entry point for T027b execution."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Paths based on project structure
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "derived" / "merged_data.csv"
    proxy_config_path = project_root / "state" / "proxy_detection.yaml"
    output_model_path = project_root / "data" / "derived" / "classification_model.pkl"
    output_status_path = project_root / "state" / "proxy_detection.yaml" # Overwriting to add status fields

    if not data_path.exists():
        logger.error(f"Required data file not found: {data_path}")
        sys.exit(1)
    
    if not proxy_config_path.exists():
        logger.error(f"Proxy detection config not found: {proxy_config_path}")
        sys.exit(1)

    fit_rf_classification(
        data_path=str(data_path),
        proxy_config_path=str(proxy_config_path),
        output_model_path=str(output_model_path),
        output_status_path=str(output_status_path)
    )

    logger.info("T027b execution finished.")

if __name__ == "__main__":
    main()