import json
import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from statsmodels.formula.api import mixedlm

# Import shared utilities from project structure
try:
    from utils.logging import get_logger, log_stage_start, log_stage_end
    from utils.config import validate_resource_limits
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def log_stage_start(*args, **kwargs): pass
    def log_stage_end(*args, **kwargs): pass
    def validate_resource_limits(*args, **kwargs): pass

logger = get_logger(__name__)

INPUT_PATH = Path("data/derived/results.csv")
OUTPUT_PATH = Path("data/derived/cross_val_results.json")
K_FOLDS = 5
RANDOM_SEED = 42

def load_results_csv(path: Path) -> pd.DataFrame:
    """Load the merged results CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ["task_id", "method", "time_to_pivot", "success", "failure_type"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    return df

def prepare_data_for_regression(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for mixed-effects model."""
    # Ensure categorical types for fixed effects
    df["method"] = df["method"].astype("category")
    df["failure_type"] = df["failure_type"].astype("category")
    
    # Create interaction term explicitly if not present in formula parsing
    # The formula will handle it, but we ensure types are correct
    return df

def fit_mixed_effects_model(df: pd.DataFrame, train_indices: List[int], test_indices: List[int]) -> Optional[float]:
    """
    Fit the mixed-effects model on training data and return the interaction coefficient.
    Formula: Success ~ FailureType * Method + (1|TaskID)
    """
    if len(train_indices) == 0:
        return None

    train_df = df.iloc[train_indices].copy()
    
    # Check for sufficient data in categories
    if train_df["success"].nunique() < 2:
        logger.warning("Training set has only one outcome class; cannot fit logistic model.")
        return None

    try:
        # MixedLM with binary outcome often uses Gaussian by default in statsmodels 
        # unless GLMM is used. For robustness in this cross-validation context, 
        # we fit the linear mixed model on the probability/success score.
        # Formula: success ~ C(failure_type) * C(method) + (1 | task_id)
        formula = "success ~ C(failure_type) * C(method)"
        
        # Fit model
        # random_grouping = train_df['task_id']
        # We need to handle the random effect grouping. 
        # If task_id is unique per row, the random effect is not estimable in the standard way.
        # Assuming task_id might be repeated or we treat it as a grouping factor.
        # If task_id is unique, this effectively becomes a fixed effect or we drop it.
        # Given the task description implies a mixed model, we assume task_id has structure 
        # or we fit the fixed effects part robustly.
        
        # To ensure stability in cross-validation where data splits vary:
        model = mixedlm(formula, train_df, groups=train_df["task_id"])
        result = model.fit(disp=False, maxiter=1000)
        
        # Extract interaction coefficient
        # The coefficient name will be something like 'C(failure_type)[T.Type]:C(method)[T.Method]'
        interaction_key = None
        for key in result.params.index:
            if "C(failure_type)" in key and "C(method)" in key and ":" in key:
                interaction_key = key
                break
        
        if interaction_key is None:
            # Fallback: try to find any interaction term if naming differs
            for key in result.params.index:
                if "C(failure_type)" in key and "C(method)" in key:
                    interaction_key = key
                    break

        if interaction_key and interaction_key in result.params:
            return float(result.params[interaction_key])
        else:
            logger.warning(f"Interaction term not found in params: {result.params.index.tolist()}")
            return None

    except Exception as e:
        logger.warning(f"Model fitting failed for fold: {e}")
        return None

def extract_interaction_coefficient(coefficient: float) -> float:
    """Return the coefficient as is."""
    return coefficient

def cross_validate_regression(df: pd.DataFrame, k: int = 5, seed: int = 42) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation on the mixed-effects model.
    Returns mean and std dev of the interaction coefficient.
    """
    kf = KFold(n_splits=k, shuffle=True, random_state=seed)
    coefficients = []

    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(df)):
        logger.info(f"Processing fold {fold_idx + 1}/{k}")
        
        coef = fit_mixed_effects_model(df, train_idx, test_idx)
        
        if coef is not None:
            coefficients.append(coef)
        else:
            logger.warning(f"Fold {fold_idx + 1} produced no valid coefficient.")

    if not coefficients:
        return {
            "mean_coefficient": None,
            "std_coefficient": None,
            "valid_folds": 0,
            "total_folds": k,
            "status": "failed_no_valid_folds"
        }

    mean_coef = float(np.mean(coefficients))
    std_coef = float(np.std(coefficients))

    return {
        "mean_coefficient": mean_coef,
        "std_coefficient": std_coef,
        "valid_folds": len(coefficients),
        "total_folds": k,
        "coefficients_per_fold": coefficients,
        "status": "success"
    }

def main():
    log_stage_start("Cross-Validation Regression", "T064")
    
    try:
        # Validate resource limits
        validate_resource_limits()

        # Load data
        if not INPUT_PATH.exists():
            logger.error(f"Input file {INPUT_PATH} not found. Ensure T022 (merge_results) has completed.")
            sys.exit(1)
        
        df = load_results_csv(INPUT_PATH)
        logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")

        if df.empty:
            logger.error("Input DataFrame is empty.")
            sys.exit(1)

        # Prepare data
        df = prepare_data_for_regression(df)

        # Run Cross-Validation
        results = cross_validate_regression(df, k=K_FOLDS, seed=RANDOM_SEED)

        # Save results
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Cross-validation results saved to {OUTPUT_PATH}")
        log_stage_end("Cross-Validation Regression", "T064", status="success")
        
    except Exception as e:
        logger.error(f"Cross-validation failed: {e}")
        log_stage_end("Cross-Validation Regression", "T064", status="failed")
        sys.exit(1)

if __name__ == "__main__":
    main()