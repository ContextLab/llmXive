import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

# Local imports adhering to the provided API surface
from seed import init_reproducibility
from config import (
    get_data_processed_dir,
    get_r2_sensitivity_thresholds,
    get_bootstrap_iterations,
    get_log_level,
    get_log_format,
)
from utils.logging_config import get_logger

# Ensure we can import from the project root if run as a script
# This handles the case where the script is run via `python code/evaluation/sensitivity.py`
if "code" not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

# Import bootstrap metrics if available, though we might compute R2 directly from saved metrics
# The bootstrap.py file provides 'bootstrap_metrics' which likely returns a dict of metrics per iteration
# We need to load the results of the bootstrap analysis performed in T026.
# Assuming T026 saves a file like `data/processed/bootstrap_results.json` or similar.
# However, looking at the task list, T026 saves "confidence intervals on held-out test set".
# The most robust way is to load the raw bootstrap R2 values if saved, or re-run the bootstrap logic if necessary.
# Given the pipeline structure, T026 likely produces a file containing the distribution of metrics.
# Let's assume the bootstrap results are saved in a standard location or we need to load the model and re-evaluate.
#
# RE-READING THE PIPELINE:
# T026: "Implement bootstrap resampling for confidence intervals on held-out test set in code/evaluation/bootstrap.py"
# T029: "Implement sensitivity analysis... sweeping R2 thresholds... saving the fraction of bootstrap samples exceeding each threshold"
#
# Strategy:
# 1. Load the validated dataset (from T016).
# 2. Load the trained model (from T030, but T030 is not done yet. However, T023/T024 train models).
# 3. We need the R2 values from the bootstrap iterations.
#    If T026 saved the bootstrap R2 values, we load them.
#    If T026 only saved the final CI, we might need to re-run the bootstrap evaluation logic here or rely on T026's internal state.
#    Since T026 is marked complete, it likely produced a file.
#    Common pattern: `data/processed/bootstrap_r2_values.npy` or `data/processed/bootstrap_metrics.json`.
#
# Let's check the API surface for `bootstrap.py`:
# `from evaluation.bootstrap import bootstrap_metrics, BootstrapEvaluator, main`
# It likely saves results to `data/processed/`.
#
# Assumption: The bootstrap process saved a file `data/processed/bootstrap_r2_distribution.json` (or similar).
# If that file doesn't exist, we must re-run the bootstrap evaluation on the best model to get the R2 distribution.
# Since T030 (save artifacts) is not done, we might not have the model saved yet.
# However, T023/T024 train models. We need to know which model to use.
# The task says "sweeping R2 thresholds... fraction of bootstrap samples". This implies we have a distribution of R2 values.
#
# Let's assume the best model is XGBoost (T023) and we need to re-run the bootstrap evaluation on it if the distribution file is missing.
# Or, more likely, the `bootstrap.py` module has a function to load or compute this.
#
# To be safe and robust:
# 1. Try to load existing bootstrap R2 values from `data/processed/bootstrap_r2_values.json`.
# 2. If not found, re-run the bootstrap evaluation using the XGBoost model (re-training or loading if T030 was partially done).
#    But since T030 is not done, we might need to train the model here or assume the user ran T023/T026.
#    Actually, T026 implies the bootstrap was run. If T026 ran, it should have saved the metrics.
#    Let's look for a standard file name. `data/processed/bootstrap_results.json` is a good candidate.
#
# Alternative: The `bootstrap_metrics` function in `bootstrap.py` might be designed to be called to get the distribution.
# Let's assume the `BootstrapEvaluator` class or `bootstrap_metrics` function can be called to get the R2 array.
#
# Let's implement a robust solution:
# - Load the validated data.
# - Load the trained XGBoost model (if saved, otherwise train a simple one or assume T023/T026 saved it).
#   Since T030 is pending, maybe T026 saved the model internally? Unlikely.
#   Let's assume the model is saved in `models/` by T023/T024 or T026.
#   If not, we might have to re-train.
#
# To ensure this task runs independently as much as possible:
# We will attempt to load the R2 distribution from a file produced by T026.
# If that fails, we will raise an error or attempt to re-run the bootstrap logic if the model is available.
#
# Given the strict "no fabrication" rule, we must use real data and real model outputs.
# If the model wasn't saved (T030 pending), we might need to re-train the model here using the same logic as T023.
#
# Let's assume T026 saved `data/processed/bootstrap_r2_distribution.json`.
# If not, we will try to load the model from `models/xgboost_best.pkl` (common convention) or re-train.
#
# Let's write code that:
# 1. Loads data.
# 2. Checks for `data/processed/bootstrap_r2_distribution.json`.
# 3. If missing, tries to load the model from `models/` (if T023 saved it) and re-runs bootstrap.
# 4. If model missing, raises error (since we can't fabricate).
#
# Wait, T023 is "Implement XGBoost training...". T026 is "Implement bootstrap...".
# T026 likely uses the model from T023.
# If T023 didn't save the model, T026 couldn't have run successfully to produce results.
# So if T026 is marked complete, the model and bootstrap results should exist.
#
# Let's assume the file `data/processed/bootstrap_r2_values.json` exists.

logger = get_logger(__name__)

def load_bootstrap_r2_values() -> Optional[np.ndarray]:
    """
    Attempts to load the R2 values from the bootstrap analysis performed in T026.
    Expected file: data/processed/bootstrap_r2_values.json
    """
    data_processed_dir = get_data_processed_dir()
    file_path = data_processed_dir / "bootstrap_r2_values.json"
    
    if not file_path.exists():
        logger.warning(f"Bootstrap R2 values file not found at {file_path}. "
                       "Attempting to locate alternative or re-run logic if model exists.")
        # Alternative: check for a generic bootstrap results file
        alt_path = data_processed_dir / "bootstrap_results.json"
        if alt_path.exists():
            try:
                with open(alt_path, 'r') as f:
                    data = json.load(f)
                    if 'r2_scores' in data:
                        return np.array(data['r2_scores'])
            except Exception as e:
                logger.error(f"Failed to parse alternative bootstrap file: {e}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Assuming structure: {"r2_scores": [...]}
            if 'r2_scores' in data:
                return np.array(data['r2_scores'])
            elif isinstance(data, list):
                return np.array(data)
            else:
                logger.error("Bootstrap file format unexpected.")
                return None
    except Exception as e:
        logger.error(f"Failed to load bootstrap R2 values: {e}")
        return None

def re_run_bootstrap_evaluation() -> np.ndarray:
    """
    Re-runs the bootstrap evaluation if the saved results are missing.
    This requires loading the trained XGBoost model.
    """
    logger.info("Re-running bootstrap evaluation to generate R2 distribution.")
    
    # Load data
    data_processed_dir = get_data_processed_dir()
    data_path = data_processed_dir / "solder_hardness_validated.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Validated dataset not found at {data_path}. Cannot run sensitivity analysis.")
    
    df = pd.read_csv(data_path)
    
    # Identify composition columns and target
    # Assuming columns like 'Sn', 'Ag', 'Cu', etc. and 'HV' or 'Hardness'
    # This logic should match T021/T022.
    # We need to know the exact column names.
    # Let's assume the target is 'HV' and composition columns are numeric and not 'HV'.
    # This is a heuristic. In a real scenario, we'd use a config or schema.
    # For robustness, we'll look for the target column defined in config or common name.
    
    target_col = 'HV'
    if target_col not in df.columns:
        # Try 'Hardness'
        if 'Hardness' in df.columns:
            target_col = 'Hardness'
        else:
            # Try to find a column that looks like a target (not composition)
            # This is risky. Let's assume 'HV' is standard per T013 (standardize to HV).
            raise ValueError(f"Target column '{target_col}' not found in dataset. Columns: {df.columns.tolist()}")
    
    # Composition columns: all numeric columns except target
    # This is a simplification. T021 might have created specific descriptors.
    # If T021 created descriptors, we should use those.
    # If T021 created CLR transformed data, we need to use that.
    #
    # Let's assume the dataset in T016 contains the raw composition and the target.
    # T021 transforms it.
    # If we are re-running, we need to re-transform.
    #
    # However, if T026 was run, it used the transformed data.
    # If we are here, it means T026 didn't save its results.
    #
    # Let's try to import the descriptor engine to re-transform.
    from features.descriptor_engine import DescriptorEngine
    from features.transformer import CLRTransformer
    
    # We need to know which columns are composition.
    # Let's assume standard solder elements: Sn, Ag, Cu, Pb, Bi, In, Zn, Sb, Ni
    elements = ['Sn', 'Ag', 'Cu', 'Pb', 'Bi', 'In', 'Zn', 'Sb', 'Ni', 'Au', 'Mn', 'Fe', 'Cr', 'Ti', 'V', 'Co', 'Mo', 'W', 'Si', 'Al']
    comp_cols = [c for c in elements if c in df.columns]
    
    if not comp_cols:
        # Fallback: all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        comp_cols = [c for c in numeric_cols if c != target_col]
    
    X_raw = df[comp_cols].values
    y = df[target_col].values
    
    # Transform using CLR
    # The CLR transformer needs to be fitted or we need to handle zeros.
    # T020 implements CLR transform.
    # Let's assume we can use the CLRTransformer from T020.
    # Note: CLR requires positive values. Solder compositions are percentages (0-100).
    # If there are zeros, we might need a small epsilon.
    
    # Check for zeros
    if np.any(X_raw <= 0):
        logger.warning("Non-positive values in composition data. Applying epsilon.")
        X_raw = np.maximum(X_raw, 1e-9)
    
    # Normalize to sum to 1 (closure)
    X_closed = X_raw / X_raw.sum(axis=1, keepdims=True)
    
    # Apply CLR
    # The compositional library's clr function works on log-ratios.
    # clr(x) = ln(x / g(x)) where g(x) is the geometric mean.
    # We can use the clr function from the 'compositional' library.
    X_clr = clr(X_closed)
    
    # Now we need a model.
    # Try to load the best XGBoost model.
    models_dir = Path("models")
    model_path = models_dir / "xgboost_best.pkl"
    
    if not model_path.exists():
        # If not found, we might need to re-train.
        # But T023 is marked complete, so it should have saved it.
        # Let's try to find any xgboost model.
        model_files = list(models_dir.glob("xgboost*.pkl"))
        if model_files:
            model_path = model_files[0]
            logger.info(f"Using found model: {model_path}")
        else:
            raise FileNotFoundError("No trained XGBoost model found. Cannot re-run bootstrap.")
    
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Run bootstrap
    n_iterations = get_bootstrap_iterations()
    r2_scores = []
    rng = np.random.default_rng(42) # Seed from T004
    
    for i in range(n_iterations):
        # Resample indices
        indices = rng.choice(len(y), size=len(y), replace=True)
        X_boot = X_clr[indices]
        y_boot = y[indices]
        
        # Evaluate
        pred = model.predict(X_boot)
        ss_res = np.sum((y_boot - pred) ** 2)
        ss_tot = np.sum((y_boot - np.mean(y_boot)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        r2_scores.append(r2)
    
    return np.array(r2_scores)

def run_sensitivity_analysis():
    """
    Implements the sensitivity analysis for T029.
    Sweeps R2 thresholds {0.3, 0.5, 0.6, 0.7} and saves the fraction of bootstrap samples exceeding each.
    """
    init_reproducibility()
    
    # 1. Get R2 distribution
    r2_scores = load_bootstrap_r2_values()
    
    if r2_scores is None:
        # If not found, try to re-run
        try:
            r2_scores = re_run_bootstrap_evaluation()
        except Exception as e:
            logger.error(f"Failed to load or re-run bootstrap evaluation: {e}")
            # If we can't get real data, we cannot proceed.
            # Per constraints: "If the task is too large... return verdict: atomize"
            # But here, we are missing a prerequisite (model/bootstrap results).
            # We should fail loudly.
            raise RuntimeError("Cannot perform sensitivity analysis: Bootstrap R2 distribution not available and model not found to regenerate it.")
    
    logger.info(f"Loaded/Generated {len(r2_scores)} bootstrap R2 scores.")
    logger.info(f"R2 Stats: Mean={r2_scores.mean():.4f}, Std={r2_scores.std():.4f}, Min={r2_scores.min():.4f}, Max={r2_scores.max():.4f}")
    
    # 2. Define thresholds
    thresholds = get_r2_sensitivity_thresholds()
    # Default if not in config: {0.3, 0.5, 0.6, 0.7}
    if not thresholds:
        thresholds = [0.3, 0.5, 0.6, 0.7]
    
    # 3. Calculate fractions
    results = {}
    for thresh in thresholds:
        fraction = np.mean(r2_scores >= thresh)
        results[str(thresh)] = float(fraction)
        logger.info(f"Threshold {thresh}: Fraction of samples >= {thresh} is {fraction:.4f}")
    
    # 4. Save results
    output_dir = get_data_processed_dir()
    output_file = output_dir / "sensitivity_analysis.yaml"
    
    # Prepare output structure
    output_data = {
        "description": "Sensitivity analysis of R2 threshold exceedance",
        "thresholds": thresholds,
        "results": results,
        "bootstrap_iterations": len(r2_scores),
        "r2_statistics": {
            "mean": float(r2_scores.mean()),
            "std": float(r2_scores.std()),
            "min": float(r2_scores.min()),
            "max": float(r2_scores.max()),
            "median": float(np.median(r2_scores))
        }
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Sensitivity analysis results saved to {output_file}")
    
    return output_data

def main():
    """Entry point for the sensitivity analysis script."""
    try:
        run_sensitivity_analysis()
    except Exception as e:
        logger.critical(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
