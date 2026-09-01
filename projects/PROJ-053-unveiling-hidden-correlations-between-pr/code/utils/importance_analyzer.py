import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr
from pathlib import Path

from config import (
    get_project_root,
    get_models_dir,
    get_results_dir,
    get_hardcoded_baseline_ranking,
    get_logger,
    ensure_directories,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir
)

def setup_importance_logger() -> logging.Logger:
    """Setup logger for importance analysis."""
    ensure_directories()
    logger = get_logger("importance_analyzer")
    return logger

def load_literature_baseline(logger: logging.Logger) -> Optional[Dict[str, int]]:
    """
    Attempt to load a user-provided baseline from data/baseline_importance.json.
    Schema: {"rankings": {"feature_name": rank_int, ...}}
    Returns None if not found.
    """
    baseline_path = os.path.join(get_data_dir(), "baseline_importance.json")
    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, 'r') as f:
                data = json.load(f)
            if "rankings" in data:
                logger.info(f"Loaded user-provided baseline from {baseline_path}")
                return data["rankings"]
            else:
                logger.warning(f"Baseline file {baseline_path} missing 'rankings' key.")
        except Exception as e:
            logger.error(f"Failed to parse baseline file {baseline_path}: {e}")
    return None

def get_hardcoded_baseline_ranking(logger: logging.Logger) -> Dict[str, int]:
    """
    Return the hard-coded literature baseline defined in config.py.
    This acts as the final fallback if no user file exists.
    """
    logger.info("Using hard-coded literature baseline from config.py")
    return get_hardcoded_baseline_ranking()

def load_user_baseline(logger: logging.Logger) -> Dict[str, int]:
    """
    Main entry to get a baseline.
    1. Try user file.
    2. If missing, return hardcoded baseline from config.
    Note: The task spec says "If neither user file nor hard-coded baseline exists, raise".
    Since we provide a hardcoded one in config, we always return something unless config is broken.
    However, strictly following the 'raise' instruction if config fails:
    """
    user_baseline = load_literature_baseline(logger)
    if user_baseline is not None:
        return user_baseline

    hardcoded = get_hardcoded_baseline_ranking(logger)
    if hardcoded:
        return hardcoded

    # If config didn't provide one, we raise as per spec
    raise FileNotFoundError("No baseline provided for SC-004; cannot calculate correlation. Execution halted.")

def calculate_permutation_importance(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Compute permutation importance for the trained GPR model.
    Returns a dict mapping feature name to mean importance score.
    """
    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring='r2' # GPR usually maximizes log likelihood, but R2 is standard for importance
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = result.importances_mean[i]
    
    return importance_dict

def rank_list_to_feature_list(
    ranking_dict: Dict[str, int],
    all_features: List[str]
) -> List[int]:
    """
    Convert a dictionary of {feature: rank} into a list of ranks 
    ordered by the `all_features` list.
    If a feature is missing in the ranking dict, assign rank 0 (or last?).
    We assume missing features are least important (rank 0 or high number).
    Let's assign rank 0 for missing to indicate 'not found' or lowest priority.
    """
    ranks = []
    for feat in all_features:
        if feat in ranking_dict:
            ranks.append(ranking_dict[feat])
        else:
            # If a feature is in the model but not in the baseline, 
            # we treat it as rank 0 (lowest) or assign a very high rank.
            # Standard Spearman handles ties. Let's use 0.
            ranks.append(0)
    return ranks

def calculate_correlation_coefficient(
    model_ranks: List[int],
    baseline_ranks: List[int]
) -> float:
    """
    Calculate Spearman correlation between two lists of ranks.
    Returns the correlation coefficient (rho).
    """
    rho, _ = spearmanr(model_ranks, baseline_ranks)
    return float(rho)

def run_correlation_analysis(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
    logger: Optional[logging.Logger] = None
) -> Tuple[Dict[str, float], float, Dict[str, int]]:
    """
    Orchestrates the full correlation analysis:
    1. Calculate permutation importance.
    2. Load baseline.
    3. Rank both.
    4. Calculate Spearman correlation.
    5. Return results.
    """
    if logger is None:
        logger = setup_importance_logger()

    # 1. Calculate Permutation Importance
    logger.info("Calculating permutation importance...")
    importance_scores = calculate_permutation_importance(model, X_test, y_test, feature_names)
    
    # Sort by importance (descending) to get ranks. 
    # Rank 1 = most important.
    sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
    model_ranking = {feat: rank + 1 for rank, (feat, score) in enumerate(sorted_features)}
    
    logger.info(f"Model Ranking: {model_ranking}")

    # 2. Load Baseline
    try:
        baseline_ranking = load_user_baseline(logger)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info(f"Baseline Ranking: {baseline_ranking}")

    # 3. Convert to rank lists for correlation
    # We need a consistent order. Use the feature_names from the model data.
    model_ranks = rank_list_to_feature_list(model_ranking, feature_names)
    baseline_ranks = rank_list_to_feature_list(baseline_ranking, feature_names)

    logger.debug(f"Model Ranks vector: {model_ranks}")
    logger.debug(f"Baseline Ranks vector: {baseline_ranks}")

    # 4. Calculate Correlation
    correlation = calculate_correlation_coefficient(model_ranks, baseline_ranks)
    logger.info(f"Spearman Correlation (Model vs Baseline): {correlation:.4f}")

    return importance_scores, correlation, model_ranking

def main():
    """
    Standalone entry point to run the analysis if called directly.
    Assumes model and data are already saved in standard locations.
    """
    logger = setup_importance_logger()
    logger.info("Starting Permutation Importance Correlation Analysis (T031)")

    # Load Model
    model_path = os.path.join(get_models_dir(), "gpr_model.pkl")
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}")
        sys.exit(1)
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info("Loaded GPR Model")

    # Load Test Data
    # We need the raw features to match the model's expectation.
    # The preprocessed data is in data/processed/test.csv
    test_csv_path = os.path.join(get_processed_data_dir(), "test.csv")
    if not os.path.exists(test_csv_path):
        logger.error(f"Test data not found at {test_csv_path}")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(test_csv_path)
    
    # Identify features and target. 
    # Based on schema: predictors are laser_power, scan_speed, layer_thickness, 
    # and encoded alloy types. Targets are yield_strength, ductility.
    # We need to know which target the model was trained on.
    # For simplicity, we assume the model file contains metadata or we try common targets.
    # However, the task implies we run this on the *trained* model.
    # Let's assume the model was trained on 'yield_strength' (common primary target).
    # We will try to infer from the model's feature names if possible, 
    # or just use all numeric columns except the known targets as features.
    
    # Better: Load the model's feature names if saved, otherwise infer.
    # Let's assume the model object has a feature_names_ attribute or similar, 
    # but sklearn GPR doesn't always store them.
    # We will assume the columns in the CSV (excluding targets) are the features.
    known_targets = ['yield_strength', 'ductility', 'fatigue_life']
    features = [c for c in df.columns if c not in known_targets]
    target = 'yield_strength' # Default assumption if not specified elsewhere
    
    if target not in df.columns:
        logger.warning(f"Target {target} not found, trying first available target...")
        for t in known_targets:
            if t in df.columns:
                target = t
                break
        else:
            logger.error("No known target column found in test data.")
            sys.exit(1)

    X_test = df[features].values
    y_test = df[target].values

    logger.info(f"Using features: {features}")
    logger.info(f"Using target: {target}")

    # Run Analysis
    try:
        importance_scores, correlation, model_ranking = run_correlation_analysis(
            model, X_test, y_test, features, logger
        )
    except FileNotFoundError as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    # Save Results
    results_path = os.path.join(get_results_dir(), "metrics.json")
    metrics = {}
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            metrics = json.load(f)
    
    metrics["permutation_importance_correlation"] = correlation
    metrics["permutation_importance_rankings"] = model_ranking
    
    with open(results_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    logger.info(f"Correlation Coefficient: {correlation}")

    return correlation

if __name__ == "__main__":
    main()
