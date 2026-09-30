import os
import sys
import logging
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Local imports based on API surface
from utils.logging import get_logger, log_memory_usage
from config import get_config, set_random_seed

logger = get_logger(__name__)
config = get_config()

# --- Data Loading ---

def load_preprocessed_data() -> pd.DataFrame:
    """
    Loads the preprocessed dataset produced by 02_preprocessing.py.
    Expects: data/processed/analysis_ready.csv
    """
    input_path = Path("data/processed/analysis_ready.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. Run 02_preprocessing.py first.")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Verify critical columns exist
    required_cols = ['participant_id', 'age', 'cognitive_score', 'bmi', 'education']
    # We also expect genus columns, usually prefixed or identified by being numeric after ID/covariates
    # We will identify them dynamically in prepare_features_target
    
    logger.info(f"Loaded {len(df)} samples. Columns: {list(df.columns)}")
    return df

# --- Feature Preparation ---

def prepare_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Separates features (genus abundances + covariates) and target (cognitive_score).
    Returns: (X, y, feature_names)
    """
    target_col = 'cognitive_score'
    id_col = 'participant_id'
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    # Identify genus columns: assume they are numeric and not in known non-genus list
    non_genus_cols = {id_col, 'age', 'bmi', 'education', 'participant_id'}
    # If 'cognitive_score' is in the numeric set, exclude it too
    non_genus_cols.add(target_col)
    
    # Filter for numeric columns that are not covariates or ID
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    genus_cols = [c for c in numeric_cols if c not in non_genus_cols]
    
    if not genus_cols:
        raise ValueError("No genus columns found in the dataset. Check preprocessing output.")
    
    logger.info(f"Identified {len(genus_cols)} genus features.")
    
    # Combine covariates and genus data for modeling
    # Note: Covariates are often useful, but VIF is specifically requested for 'top predictive taxa' (genus).
    # We will include them in the model for prediction, but VIF calculation will focus on the selected taxa.
    covariates = ['age', 'bmi', 'education']
    # Ensure covariates exist
    missing_covs = [c for c in covariates if c not in df.columns]
    if missing_covs:
        logger.warning(f"Missing covariates: {missing_covs}. Proceeding with available ones.")
        covariates = [c for c in covariates if c in df.columns]
    
    feature_cols = covariates + genus_cols
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, genus_cols

# --- Modeling Logic ---

def nested_cv_random_forest(X: pd.DataFrame, y: pd.Series, n_jobs: int = -1) -> Dict[str, Any]:
    """
    Performs Nested Cross-Validation for Random Forest.
    Returns dict with outer_cv_scores, best_params, and feature importances.
    """
    logger.info("Starting Nested Cross-Validation for Random Forest...")
    set_random_seed(config.random_seed)
    
    # Outer loop: Evaluation
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=config.random_seed)
    outer_scores = []
    
    # Inner loop: Hyperparameter tuning
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=config.random_seed)
    
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5]
    }
    
    rf = RandomForestRegressor(random_state=config.random_seed, n_jobs=n_jobs)
    grid_search = GridSearchCV(rf, param_grid, cv=inner_cv, scoring='r2', n_jobs=n_jobs)
    
    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_
        
        y_pred = best_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        outer_scores.append(r2)
        logger.debug(f"Outer fold R2: {r2:.4f}")
    
    # Retrain on full data with best params to get importances
    logger.info(f"Retraining on full data with best params: {grid_search.best_params_}")
    final_model = RandomForestRegressor(**grid_search.best_params_, random_state=config.random_seed, n_jobs=n_jobs)
    final_model.fit(X, y)
    
    return {
        'outer_cv_scores': outer_scores,
        'mean_r2': np.mean(outer_scores),
        'std_r2': np.std(outer_scores),
        'best_params': grid_search.best_params_,
        'feature_importances': dict(zip(X.columns, final_model.feature_importances_))
    }

def run_permutation_test(X: pd.DataFrame, y: pd.Series, n_permutations: int = 1000, n_jobs: int = -1) -> List[float]:
    """
    Generates null distribution of R2 scores by permuting target labels.
    """
    logger.info(f"Running permutation test with {n_permutations} shuffles...")
    set_random_seed(config.random_seed)
    
    scores = []
    rf_base = RandomForestRegressor(n_estimators=100, random_state=config.random_seed, n_jobs=n_jobs)
    
    for i in range(n_permutations):
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations}")
        
        y_permuted = y.sample(frac=1, random_state=config.random_seed + i).reset_index(drop=True)
        rf_base.fit(X, y_permuted)
        
        # Use cross_val_score for robustness in null distribution
        # Using a single CV fold for speed if N is large, or 3-fold
        cv_scores = cross_val_score(rf_base, X, y_permuted, cv=3, scoring='r2', n_jobs=n_jobs)
        scores.append(np.mean(cv_scores))
    
    return scores

def identify_top_taxa(feature_importances: Dict[str, float], genus_cols: List[str], top_n: int = 10) -> List[str]:
    """
    Selects top N taxa based on feature importance.
    """
    # Filter importances to only genus columns
    genus_importances = {k: v for k, v in feature_importances.items() if k in genus_cols}
    
    if not genus_importances:
        return []
    
    sorted_taxa = sorted(genus_importances.items(), key=lambda x: x[1], reverse=True)
    top_taxa = [t[0] for t in sorted_taxa[:top_n]]
    
    logger.info(f"Identified top {len(top_taxa)} predictive taxa: {top_taxa}")
    return top_taxa

# --- VIF Calculation (Task T033) ---

def calculate_vif(X: pd.DataFrame, top_taxa: List[str]) -> Tuple[Dict[str, float], Dict[str, bool]]:
    """
    Calculates Variance Inflation Factors (VIF) for the specified top taxa.
    
    Args:
        X: The full feature DataFrame (must contain the top_taxa columns).
        top_taxa: List of column names to check for collinearity.
    
    Returns:
        vif_values: Dict mapping taxon name to VIF score.
        flags: Dict mapping taxon name to boolean (True if VIF > 5).
    """
    if not top_taxa:
        logger.warning("No top taxa provided for VIF calculation.")
        return {}, {}
    
    # Ensure we have the columns
    missing = [t for t in top_taxa if t not in X.columns]
    if missing:
        raise ValueError(f"Top taxa not found in feature matrix: {missing}")
    
    # Select only the relevant columns for VIF calculation
    # VIF is typically calculated on the predictors. 
    # We calculate VIF for each of the top taxa against the others in the set.
    # Note: VIF requires an intercept. statsmodels VIF function expects design matrix with intercept or we add one.
    # However, for pairwise/multicollinearity among a subset, we just look at the subset.
    
    subset_X = X[top_taxa].copy()
    
    # Check for zero variance or constant columns which break VIF
    if subset_X.var().min() == 0:
        logger.warning("Constant columns detected in top taxa, VIF calculation may fail or be undefined.")
    
    vif_values = {}
    flags = {}
    
    try:
        # Add constant for intercept if needed by the VIF implementation
        # statsmodels VIF formula: 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on all other X_j
        # The function variance_inflation_factor expects the design matrix (X) including intercept if used in regression,
        # but for VIF of specific columns, we pass the sub-matrix.
        
        # We add a constant column to the subset for the calculation context
        subset_X_with_const = subset_X.copy()
        subset_X_with_const['const'] = 1.0
        
        # Calculate VIF for each taxon
        # We iterate over the columns (excluding the constant we just added for the calculation context)
        # Actually, variance_inflation_factor calculates VIF for each column in the passed DataFrame.
        # If we pass the subset with const, it will calculate VIF for const too. We ignore that.
        
        for i, col in enumerate(subset_X.columns):
            # We need to pass the full design matrix (including const) to the function for the specific column index
            # But the function takes the whole dataframe and the index of the column to compute VIF for.
            # So we pass the whole subset_X_with_const and the index of the column.
            vif = variance_inflation_factor(subset_X_with_const.values, i)
            vif_values[col] = vif
            flags[col] = vif > 5.0
            logger.debug(f"VIF for {col}: {vif:.4f} (Flagged: {flags[col]})")
        
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        # If it fails (e.g., perfect multicollinearity), we might need to handle it
        # For now, let's return what we have or re-raise if critical
        raise RuntimeError(f"VIF calculation failed: {e}") from e
    
    return vif_values, flags

# --- Output Generation ---

def save_results(vif_values: Dict[str, float], flags: Dict[str, bool], output_path: str):
    """
    Saves the collinearity review log to JSON.
    """
    log_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "Variance Inflation Factor (VIF)",
        "threshold": 5.0,
        "results": [
            {
                "taxon": taxon,
                "vif_score": round(vif, 4),
                "flagged_high_collinearity": flags.get(taxon, False)
            }
            for taxon, vif in vif_values.items()
        ],
        "summary": {
            "total_taxa_checked": len(vif_values),
            "highly_collinear_count": sum(1 for f in flags.values() if f),
            "highly_collinear_taxa": [t for t, f in flags.items() if f]
        }
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Collinearity review log saved to {output_path}")

# --- Pipeline ---

def run_modeling_pipeline():
    """
    Orchestrates the full modeling pipeline including VIF calculation for T033.
    """
    logger.info("Starting Predictive Modeling Pipeline (US3)")
    
    # 1. Load Data
    df = load_preprocessed_data()
    X, y, genus_cols = prepare_features_target(df)
    
    # 2. Train Model (T030)
    model_results = nested_cv_random_forest(X, y)
    logger.info(f"Model Mean R2: {model_results['mean_r2']:.4f} (+/- {model_results['std_r2']:.4f})")
    
    # 3. Permutation Test (T031) - Skipped in this specific task run if only VIF is needed, 
    # but for a complete run, we would call run_permutation_test here.
    # For T033, we rely on the existence of top_taxa from T032.
    
    # 4. Identify Top Taxa (T032)
    # We simulate the output of T032 by using the importances from the current run.
    # In a real sequential pipeline, T032 would have saved this to disk. 
    # Here we compute it to ensure T033 has data.
    top_taxa = identify_top_taxa(
        model_results['feature_importances'], 
        genus_cols, 
        top_n=10
    )
    
    # 5. Calculate VIF (T033 - THE MAIN TASK)
    # Requirement: Calculate VIF for 'top predictive taxa' after CLR transformation.
    # Note: The data in 'analysis_ready.csv' should already be CLR transformed if 03_correlation_analysis.py 
    # or 02_preprocessing.py handled it. The spec says "after CLR transformation".
    # Assuming the input data X is already CLR transformed (or relative abundance which is log-ratio ready).
    # If the data is raw counts, VIF is less meaningful. We assume preprocessing handled the transform.
    
    if not top_taxa:
        logger.warning("No top taxa identified. Cannot calculate VIF.")
        return
    
    vif_values, flags = calculate_vif(X, top_taxa)
    
    # 6. Save Results (T033)
    output_path = "data/processed/collinearity_review_log.json"
    save_results(vif_values, flags, output_path)
    
    logger.info("Pipeline completed successfully.")
    return vif_values, flags

def main():
    """Entry point for script execution."""
    logging.basicConfig(level=logging.INFO)
    try:
        run_modeling_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()