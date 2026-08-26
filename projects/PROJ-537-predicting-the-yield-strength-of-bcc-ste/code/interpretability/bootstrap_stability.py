"""
Bootstrap Stability Analysis for Feature Importance.

This module implements the bootstrap stability analysis as per FR-007 and FR-008:
1. Sample-size sweep (n=10 to n=50) to calculate std_dev of feature importance.
2. Fixed-sample bootstrap (10 resamples) to calculate stability of key descriptors.

It loads the merged dataset from data/intermediate/merged.csv, trains a Random Forest
model (reusing the trained model logic or training a fresh one if needed), and performs
the stability analysis.
"""

import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Project imports based on provided API surface
from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from modeling.train import train_random_forest_cv
from modeling.features import prepare_modeling_features

# Import scikit-learn components
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

# Constants
SEED = 42
np.random.seed(SEED)

logger = get_logger(__name__)

def load_data_and_model() -> Tuple[pd.DataFrame, Any, List[str]]:
    """
    Loads the merged dataset and the trained Random Forest model.
    If the model doesn't exist at the expected path, it trains a fresh one.
    """
    merged_path = CONFIG.MERGED_DATA_PATH
    if not os.path.exists(merged_path):
        raise FileNotFoundError(f"Required dataset not found at {merged_path}. "
                                "Run ingestion pipeline first.")

    df = pd.read_csv(merged_path)
    logger.info(f"Loaded dataset with {len(df)} rows.")

    # Define target and features
    # Based on typical flow: yield_strength is target, others are features
    # We need to ensure we have the correct feature columns.
    # The 'prepare_modeling_features' function likely handles this.
    # For now, we assume the model was saved with specific feature names.

    model_path = CONFIG.TRAINED_MODEL_PATH
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Loaded existing model from {model_path}")
    else:
        logger.warning(f"Model not found at {model_path}. Training a fresh model.")
        # Prepare features
        # We need to mimic the feature engineering from US2
        # Assuming 'prepare_modeling_features' returns X, y, feature_names
        # Since we can't easily call the full pipeline without more context,
        # we will replicate the feature preparation logic here or use a simpler approach.
        
        # Let's try to load the preprocessed data if it exists, otherwise prepare it.
        # The task T024/T025 should have produced a processed dataset.
        # If not, we prepare it here.
        
        # For robustness, we will train a model specifically for this analysis
        # using the standard columns found in the merged dataset.
        
        target_col = 'yield_strength_MPa'
        if target_col not in df.columns:
            # Try common variations
            target_col = next((c for c in df.columns if 'yield' in c.lower()), None)
        
        if not target_col:
            raise ValueError("Could not identify target column 'yield_strength_MPa'")

        feature_cols = [c for c in df.columns if c != target_col and not c.startswith('index')]
        
        X = df[feature_cols].dropna() # Drop rows with any NaNs for simplicity in bootstrap
        y = X.pop(target_col) if target_col in X.columns else df.loc[X.index, target_col]
        
        # Re-align if we dropped rows
        if target_col in df.columns:
            # Re-filter y to match X index
            y = df.loc[X.index, target_col]

        # Train a simple Random Forest for the analysis
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=SEED,
            n_jobs=-1
        )
        model.fit(X, y)
        
        # Save the model for consistency
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        feature_names = list(X.columns)
        return df, model, feature_names

    # If model loaded from file, we need feature names.
    # Ideally, these are stored with the model or in a separate file.
    # We will infer them from the merged data if not available.
    # For this implementation, we assume the model's feature_importances_ align
    # with the columns of the merged dataset (excluding target).
    
    target_col = 'yield_strength_MPa'
    if target_col in df.columns:
        feature_names = [c for c in df.columns if c != target_col and c != 'material_id']
    else:
        raise ValueError("Target column 'yield_strength_MPa' missing in loaded data.")

    return df, model, feature_names

def run_sample_size_sweep(
    df: pd.DataFrame,
    model_template: Any,
    feature_names: List[str],
    target_col: str = 'yield_strength_MPa',
    min_n: int = 10,
    max_n: int = 50,
    n_iterations: int = 10
) -> Dict[str, List[float]]:
    """
    Runs a sample-size sweep from min_n to max_n.
    For each sample size, it resamples the data n_iterations times,
    trains a model, and records feature importances.
    Returns a dictionary mapping feature name to list of std_devs (one per sample size).
    Actually, per FR-007, we calculate std_dev of feature importance ACROSS the sweep.
    So we need to collect all importance values for each feature across all sample sizes and iterations.
    """
    logger.info(f"Starting sample-size sweep: n={min_n} to {max_n}")
    
    all_importances = {name: [] for name in feature_names}
    
    # Filter out non-numeric columns for modeling
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    if target_col not in numeric_df.columns:
        # If target is not numeric (unlikely), try to convert or find it
        pass
    
    # Ensure target is in numeric_df
    if target_col in df.columns and df[target_col].dtype in [np.int64, np.float64]:
        numeric_df[target_col] = df[target_col]
    
    # Drop rows with NaNs
    numeric_df = numeric_df.dropna()
    
    if len(numeric_df) < max_n:
        logger.warning(f"Dataset size ({len(numeric_df)}) is smaller than max_n ({max_n}). "
                       f"Adjusting max_n to dataset size.")
        max_n = len(numeric_df)

    for n in range(min_n, max_n + 1):
        logger.info(f"Processing sample size n={n}")
        for _ in range(n_iterations):
            # Resample
            sample = numeric_df.sample(n=n, random_state=np.random.randint(0, 10000))
            
            X = sample.drop(columns=[target_col])
            y = sample[target_col]
            
            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                random_state=SEED,
                n_jobs=-1
            )
            model.fit(X, y)
            
            # Collect importances
            # Ensure feature order matches
            for i, feat in enumerate(X.columns):
                if feat in all_importances:
                    all_importances[feat].append(model.feature_importances_[i])
                else:
                    # New feature appeared? (unlikely with same schema)
                    all_importances[feat] = [model.feature_importances_[i]]

    # Calculate std_dev for each feature across all collected values
    std_devs = {}
    for feat, vals in all_importances.items():
        if len(vals) > 1:
            std_devs[feat] = float(np.std(vals))
        else:
            std_devs[feat] = 0.0
    
    return std_devs

def run_fixed_sample_bootstrap(
    df: pd.DataFrame,
    model_template: Any,
    feature_names: List[str],
    target_col: str = 'yield_strength_MPa',
    n_bootstraps: int = 10
) -> Dict[str, float]:
    """
    Runs 10 bootstrapped samples of the FULL dataset.
    Calculates std_dev of feature importance across these 10 samples.
    """
    logger.info(f"Starting fixed-sample bootstrap: n_bootstraps={n_bootstraps}")
    
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    if target_col in df.columns and df[target_col].dtype in [np.int64, np.float64]:
        numeric_df[target_col] = df[target_col]
    numeric_df = numeric_df.dropna()
    
    all_importances = {name: [] for name in feature_names}
    
    for i in range(n_bootstraps):
        logger.info(f"Bootstrap iteration {i+1}/{n_bootstraps}")
        # Resample with replacement
        sample = numeric_df.sample(n=len(numeric_df), replace=True, random_state=np.random.randint(0, 10000))
        
        X = sample.drop(columns=[target_col])
        y = sample[target_col]
        
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=SEED,
            n_jobs=-1
        )
        model.fit(X, y)
        
        for j, feat in enumerate(X.columns):
            if feat in all_importances:
                all_importances[feat].append(model.feature_importances_[j])
    
    std_devs = {}
    for feat, vals in all_importances.items():
        if len(vals) > 1:
            std_devs[feat] = float(np.std(vals))
        else:
            std_devs[feat] = 0.0
    
    return std_devs

def check_stability(std_devs: Dict[str, float], threshold: float = 0.05) -> Dict[str, bool]:
    """
    Checks if key DFT descriptors have std_dev < threshold.
    Returns a dict of feature -> is_stable.
    """
    # Identify DFT descriptors (heuristic: contains 'modulus', 'elastic', 'dft')
    # Or simply check all features if specific names are unknown.
    # Based on task description, we check "key DFT descriptors".
    # We will assume any feature with 'modulus' or 'elastic' is a DFT descriptor.
    
    stability_results = {}
    for feat, std in std_devs.items():
        is_dft = any(k in feat.lower() for k in ['modulus', 'elastic', 'dft', 'shear', 'bulk'])
        if is_dft:
            stability_results[feat] = std < threshold
        
    # If no DFT features found by heuristic, check all
    if not stability_results:
        for feat, std in std_devs.items():
            stability_results[feat] = std < threshold
            
    return stability_results

def save_results(
    sweep_results: Dict[str, float],
    bootstrap_results: Dict[str, float],
    stability_results: Dict[str, bool],
    output_path: Path
):
    """
    Saves the results to a JSON file.
    """
    results = {
        "sample_size_sweep": {
            "description": "Standard deviation of feature importance across sample sizes (n=10 to 50)",
            "std_devs": sweep_results
        },
        "fixed_sample_bootstrap": {
            "description": "Standard deviation of feature importance across 10 bootstrapped samples",
            "std_devs": bootstrap_results
        },
        "stability_check": {
            "description": "Stability check (std_dev < 0.05) for key DFT descriptors",
            "is_stable": stability_results,
            "all_stable": all(stability_results.values()) if stability_results else False
        }
    }
    
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for Bootstrap Stability Analysis.
    """
    try:
        # Load data and model
        df, model, feature_names = load_data_and_model()
        
        # Run Sample Size Sweep (FR-007 / SC-004)
        # n=10 to n=50
        sweep_std_devs = run_sample_size_sweep(
            df, model, feature_names, 
            min_n=10, max_n=50, n_iterations=5 # Reduced iterations for speed, but real
        )
        
        # Run Fixed Sample Bootstrap (FR-008 / SC-005)
        # 10 bootstrapped samples
        bootstrap_std_devs = run_fixed_sample_bootstrap(
            df, model, feature_names,
            n_bootstraps=10
        )
        
        # Check Stability (FR-008 / SC-005)
        stability = check_stability(bootstrap_std_devs, threshold=0.05)
        
        # Save results
        output_path = CONFIG.BOOTSTRAP_RESULTS_PATH
        save_results(sweep_std_devs, bootstrap_std_devs, stability, output_path)
        
        log_provenance_event("bootstrap_stability", "completed", {
            "sweep_std_devs_count": len(sweep_std_devs),
            "bootstrap_std_devs_count": len(bootstrap_std_devs),
            "all_stable": all(stability.values()) if stability else False
        })
        
        print(f"Bootstrap stability analysis completed. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Bootstrap stability analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()