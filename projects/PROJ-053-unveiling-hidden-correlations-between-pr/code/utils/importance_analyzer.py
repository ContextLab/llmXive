import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr

from config import get_models_dir, get_results_dir, get_data_dir, get_random_seed, get_hardcoded_baseline_ranking, ensure_directories, get_logger
from utils.logger import setup_logging

def setup_importance_logger():
    """Setup logger for importance analysis."""
    return setup_logging("importance_analysis", "data/processed/importance_analysis.log")

def load_literature_baseline(logger: logging.Logger) -> Dict[str, int]:
    """
    Load the hard-coded literature baseline from config if no user file is found.
    Returns a dict mapping feature names to rank integers (1 = most important).
    """
    logger.info("Attempting to load hardcoded literature baseline from config...")
    try:
        baseline = get_hardcoded_baseline_ranking()
        if baseline and "rankings" in baseline:
            logger.info(f"Loaded hardcoded baseline: {baseline['rankings']}")
            return baseline["rankings"]
        else:
            logger.warning("Hardcoded baseline found but missing 'rankings' key.")
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve hardcoded baseline from config: {e}")
        return None

def get_hardcoded_baseline_ranking() -> Dict[str, Any]:
    """
    Fallback to the config definition if user file is missing.
    This wraps the config function to ensure type safety here.
    """
    # This is a wrapper to ensure we get the dict from config.py
    # The actual definition is in config.py
    from config import get_hardcoded_baseline_ranking as cfg_get
    return cfg_get()

def load_user_baseline(user_path: str, logger: logging.Logger) -> Optional[Dict[str, int]]:
    """
    Load user-provided baseline from JSON file.
    Schema: {"rankings": {"feature_name": rank_int, ...}}
    """
    if not os.path.exists(user_path):
        logger.info(f"User baseline file not found at {user_path}")
        return None

    try:
        with open(user_path, 'r') as f:
            data = json.load(f)
        
        if "rankings" not in data:
            logger.error(f"User baseline file {user_path} missing 'rankings' key.")
            return None
        
        logger.info(f"Loaded user baseline from {user_path}")
        return data["rankings"]
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in user baseline file {user_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load user baseline {user_path}: {e}")
        return None

def calculate_permutation_importance(model, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str], logger: logging.Logger) -> Dict[str, float]:
    """
    Calculate permutation importance for the trained model.
    Returns a dict mapping feature names to their mean importance scores.
    """
    logger.info("Calculating permutation importance on test set...")
    try:
        result = permutation_importance(
            model, X_test, y_test, 
            n_repeats=10, 
            random_state=get_random_seed(), 
            n_jobs=1
        )
        
        importance_dict = {}
        for i, name in enumerate(feature_names):
            importance_dict[name] = result.importances_mean[i]
        
        logger.info("Permutation importance calculation complete.")
        return importance_dict
    except Exception as e:
        logger.error(f"Failed to calculate permutation importance: {e}")
        raise

def rank_list_to_feature_list(rankings: Dict[str, int], feature_names: List[str], logger: logging.Logger) -> List[float]:
    """
    Convert a ranking dict (feature -> rank) to a list of ranks aligned with feature_names.
    If a feature is missing from the ranking, assign a default rank (len(feature_names) + 1).
    """
    ranks = []
    max_rank = len(feature_names) + 1
    
    for name in feature_names:
        if name in rankings:
            ranks.append(float(rankings[name]))
        else:
            logger.warning(f"Feature '{name}' not found in baseline rankings. Assigning default rank {max_rank}.")
            ranks.append(float(max_rank))
    
    return ranks

def calculate_correlation_coefficient(model_ranks: List[float], baseline_ranks: List[float], logger: logging.Logger) -> float:
    """
    Calculate Spearman correlation between model ranks and baseline ranks.
    """
    try:
        correlation, p_value = spearmanr(model_ranks, baseline_ranks)
        logger.info(f"Spearman correlation calculated: {correlation:.4f} (p-value: {p_value:.4f})")
        return float(correlation)
    except Exception as e:
        logger.error(f"Failed to calculate correlation: {e}")
        raise

def run_correlation_analysis(model, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str], 
                             user_baseline_path: Optional[str] = None, 
                             output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main orchestration function for T031.
    1. Compute permutation importance.
    2. Load baseline (user or hardcoded).
    3. Calculate correlation.
    4. Save results.
    """
    logger = setup_importance_logger()
    logger.info("Starting permutation importance correlation analysis (T031).")

    # 1. Calculate Permutation Importance
    importance_scores = calculate_permutation_importance(model, X_test, y_test, feature_names, logger)
    
    # Sort by importance (descending) to get ranks
    sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
    model_rankings = {feat: rank + 1 for rank, (feat, _) in enumerate(sorted_features)}
    logger.info(f"Model rankings: {model_rankings}")

    # 2. Load Baseline
    baseline_rankings = None
    
    if user_baseline_path:
        baseline_rankings = load_user_baseline(user_baseline_path, logger)
    
    if not baseline_rankings:
        logger.info("No user baseline found. Attempting hardcoded literature baseline.")
        baseline_rankings = get_hardcoded_baseline_ranking()
        if baseline_rankings:
            baseline_rankings = baseline_rankings.get("rankings", {})
    
    if not baseline_rankings:
        logger.error("No baseline provided for SC-004; cannot calculate correlation. Execution halted.")
        raise FileNotFoundError("No baseline provided for SC-004; cannot calculate correlation. Execution halted.")

    # 3. Calculate Correlation
    model_ranks = rank_list_to_feature_list(model_rankings, feature_names, logger)
    baseline_ranks = rank_list_to_feature_list(baseline_rankings, feature_names, logger)
    
    correlation = calculate_correlation_coefficient(model_ranks, baseline_ranks, logger)

    # 4. Prepare Results
    results = {
        "permutation_importance": importance_scores,
        "model_rankings": model_rankings,
        "baseline_rankings": baseline_rankings,
        "permutation_importance_correlation": correlation,
        "correlation_method": "spearman"
    }

    # 5. Save Results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")

    logger.info("Correlation analysis complete.")
    return results

def main():
    """CLI entry point for T031."""
    import argparse
    parser = argparse.ArgumentParser(description="Run permutation importance correlation analysis.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to saved GPR model (.pkl)")
    parser.add_argument("--test-data-path", type=str, required=True, help="Path to processed test data CSV")
    parser.add_argument("--user-baseline", type=str, default=None, help="Optional path to user baseline JSON")
    parser.add_argument("--output", type=str, default=None, help="Output path for results JSON")
    args = parser.parse_args()

    logger = setup_importance_logger()
    ensure_directories()

    # Load Model
    logger.info(f"Loading model from {args.model_path}")
    try:
        with open(args.model_path, 'rb') as f:
            model = pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Load Test Data
    logger.info(f"Loading test data from {args.test_data_path}")
    try:
        import pandas as pd
        df = pd.read_csv(args.test_data_path)
        # Assume target is the last column or named 'yield_strength'/'ductility'
        # For T031, we assume the model was trained on specific features.
        # We need to identify features. Usually, we drop the target column.
        target_col = None
        for col in ['yield_strength', 'ductility', 'fatigue_life']:
            if col in df.columns:
                target_col = col
                break
        
        if not target_col:
            logger.error("Could not identify target column in test data.")
            sys.exit(1)

        X = df.drop(columns=[target_col]).values
        y = df[target_col].values
        feature_names = df.drop(columns=[target_col]).columns.tolist()
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        sys.exit(1)

    # Determine output path
    output_path = args.output
    if not output_path:
        output_path = os.path.join(get_results_dir(), "importance_correlation.json")

    # Run Analysis
    try:
        results = run_correlation_analysis(
            model=model,
            X_test=X,
            y_test=y,
            feature_names=feature_names,
            user_baseline_path=args.user_baseline,
            output_path=output_path
        )
        print(f"Analysis complete. Correlation: {results['permutation_importance_correlation']}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
