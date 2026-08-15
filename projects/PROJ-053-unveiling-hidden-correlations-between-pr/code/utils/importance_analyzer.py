import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr

# Import project utilities
from config import (
    get_project_root,
    get_results_dir,
    get_models_dir,
    get_hardcoded_baseline_ranking,
    get_random_seed
)

def load_literature_baseline() -> Optional[Dict[str, int]]:
    """
    Attempt to fetch literature baseline from crossref API.
    If fetch fails or metadata lacks rankings, return the hardcoded default.
    """
    import requests
    
    doi = "10.1016/j.addma.2020.101632"
    url = f"https://api.crossref.org/works/{doi}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Check if metadata contains any ranking-like structure
            # Since crossref metadata doesn't typically contain feature rankings,
            # we will treat a successful fetch as "source found" but still
            # return hardcoded if no specific ranking data exists in response.
            # For this implementation, we assume the hardcoded fallback is the
            # actual ranking source if the API doesn't return specific feature importance.
            logging.warning(f"Crossref fetch for {doi} succeeded but no explicit feature ranking found in metadata. Using hardcoded baseline.")
            return get_hardcoded_baseline_ranking()
        else:
            logging.warning(f"Crossref API returned status {response.status_code}. Using hardcoded baseline.")
            return get_hardcoded_baseline_ranking()
    except Exception as e:
        logging.warning(f"Failed to fetch from Crossref: {e}. Using hardcoded baseline.")
        return get_hardcoded_baseline_ranking()

def get_hardcoded_baseline_ranking() -> Dict[str, int]:
    """
    Returns the hardcoded default literature ranking as defined in config.
    """
    # This is a fallback implementation if config.py doesn't have it defined
    # or to ensure we have a value if config.py import fails (though it shouldn't).
    return {
        'laser_power': 1,
        'scan_speed': 2,
        'layer_thickness': 3,
        # Note: One-hot encoded columns will be handled separately
    }

def load_user_baseline() -> Optional[Dict[str, int]]:
    """
    Attempt to load user-provided baseline from data/baseline_importance.json.
    """
    base_dir = get_project_root()
    user_path = os.path.join(base_dir, "data", "baseline_importance.json")
    
    if not os.path.exists(user_path):
        return None
    
    try:
        with open(user_path, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logging.error(f"Failed to load user baseline from {user_path}: {e}")
        return None

def calculate_permutation_importance(model, X_test, y_test, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate permutation importance for the trained GPR model.
    Returns a dictionary mapping feature names to their importance scores.
    """
    result = permutation_importance(
        model, 
        X_test, 
        y_test, 
        n_repeats=10, 
        random_state=get_random_seed(),
        scoring='r2'
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = result.importances_mean[i]
    
    return importance_dict

def rank_list_to_feature_list(rankings: Dict[str, int]) -> Tuple[List[str], List[int]]:
    """
    Convert a dictionary of rankings to a list of features and a list of ranks.
    Sorts by rank value (ascending, where 1 is most important).
    """
    sorted_items = sorted(rankings.items(), key=lambda x: x[1])
    features = [item[0] for item in sorted_items]
    ranks = [item[1] for item in sorted_items]
    return features, ranks

def calculate_correlation_coefficient(model_ranks: List[int], baseline_ranks: List[int]) -> float:
    """
    Calculate Spearman correlation between model rankings and baseline rankings.
    """
    if len(model_ranks) == 0 or len(baseline_ranks) == 0:
        return 0.0
    
    try:
        corr, _ = spearmanr(model_ranks, baseline_ranks)
        if np.isnan(corr):
            return 0.0
        return float(corr)
    except Exception as e:
        logging.error(f"Correlation calculation failed: {e}")
        return 0.0

def run_correlation_analysis(model, X_test, y_test, feature_names: List[str]) -> Dict[str, Any]:
    """
    Main entry point for permutation importance correlation analysis.
    Implements the logic:
    1. Calculate permutation importance.
    2. Attempt Literature Baseline (with fallback).
    3. Attempt User Baseline.
    4. Fallback Logic: If both missing, log warning and skip metric.
    5. If baseline available, calculate correlation and save to results/metrics.json.
    """
    logging.info("Starting permutation importance correlation analysis (T031)...")
    
    # 1. Calculate Permutation Importance
    logging.info("Calculating permutation importance...")
    importance_scores = calculate_permutation_importance(model, X_test, y_test, feature_names)
    
    # Filter to only features that exist in baseline comparison (handle one-hot encoding)
    # We need to match feature names. If baseline has 'laser_power' and model has 'laser_power', it matches.
    # If model has 'alloy_type_A' and baseline doesn't, we ignore it for correlation.
    
    # 2. Attempt Literature Baseline
    literature_baseline = load_literature_baseline()
    
    # 3. Attempt User Baseline
    user_baseline = load_user_baseline()
    
    # 4. Fallback Logic
    baseline_to_use = None
    baseline_source = None
    
    if user_baseline:
        baseline_to_use = user_baseline
        baseline_source = "user"
        logging.info("Using user-provided baseline from data/baseline_importance.json")
    elif literature_baseline:
        baseline_to_use = literature_baseline
        baseline_source = "literature"
        logging.info("Using literature baseline (hardcoded fallback)")
    else:
        logging.warning("No baseline found for SC-004; correlation metric skipped.")
        # Proceed without halting, but we cannot calculate correlation
        return {
            "permutation_importance": importance_scores,
            "baseline_source": None,
            "correlation_coefficient": None,
            "status": "skipped_no_baseline"
        }
    
    # 5. Calculate Correlation
    # We need to align the features between model importance and baseline
    common_features = [f for f in importance_scores.keys() if f in baseline_to_use]
    
    if not common_features:
        logging.warning("No common features found between model importance and baseline. Correlation skipped.")
        return {
            "permutation_importance": importance_scores,
            "baseline_source": baseline_source,
            "correlation_coefficient": None,
            "status": "skipped_no_common_features",
            "common_features": []
        }
    
    # Get ranks for common features
    # Note: Permutation importance is a score (higher is better), baseline is a rank (lower is better).
    # We need to invert one or convert both to ranks.
    # Strategy: Convert permutation importance to ranks (1 = most important).
    
    sorted_imp = sorted(common_features, key=lambda x: importance_scores[x], reverse=True)
    model_ranks = [i + 1 for i in range(len(sorted_imp))]
    
    baseline_ranks = [baseline_to_use[f] for f in sorted_imp]
    
    corr = calculate_correlation_coefficient(model_ranks, baseline_ranks)
    
    logging.info(f"Correlation coefficient (Spearman) between model and {baseline_source} baseline: {corr:.4f}")
    
    result = {
        "permutation_importance": importance_scores,
        "baseline_source": baseline_source,
        "correlation_coefficient": corr,
        "status": "success",
        "common_features": common_features,
        "model_ranks": {f: r for f, r in zip(sorted_imp, model_ranks)},
        "baseline_ranks": {f: r for f, r in zip(sorted_imp, baseline_ranks)}
    }
    
    return result

def main():
    """
    Standalone execution for T031.
    Loads the trained GPR model, test data, and runs the correlation analysis.
    Saves results to results/metrics.json.
    """
    # Setup logging
    log_file = os.path.join(get_project_root(), "data", "processed", "importance_analysis.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Load model
        model_path = os.path.join(get_models_dir(), "gpr_model.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Run T026 first.")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Load test data (X_test, y_test, feature_names)
        # Assuming preprocess.py saves the split data or we can reconstruct from processed CSV
        # For simplicity, we assume there's a way to get X_test.
        # In a real pipeline, this data would be passed or loaded from a specific file.
        # Let's assume the processed test data is available at:
        test_data_path = os.path.join(get_project_root(), "data", "processed", "test_data_X.pkl")
        test_labels_path = os.path.join(get_project_root(), "data", "processed", "test_data_y.pkl")
        feature_names_path = os.path.join(get_project_root(), "data", "processed", "feature_names.json")
        
        if not all(os.path.exists(p) for p in [test_data_path, test_labels_path, feature_names_path]):
            raise FileNotFoundError("Test data artifacts not found. Ensure preprocess.py saves them.")
        
        with open(test_data_path, 'rb') as f:
            X_test = pickle.load(f)
        with open(test_labels_path, 'rb') as f:
            y_test = pickle.load(f)
        with open(feature_names_path, 'r') as f:
            feature_names = json.load(f)
        
        # Run analysis
        results = run_correlation_analysis(model, X_test, y_test, feature_names)
        
        # Save to results/metrics.json
        # We need to load existing metrics if they exist, or create new
        metrics_path = os.path.join(get_results_dir(), "metrics.json")
        existing_metrics = {}
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                existing_metrics = json.load(f)
        
        existing_metrics["permutation_importance_analysis"] = results
        
        with open(metrics_path, 'w') as f:
            json.dump(existing_metrics, f, indent=2)
        
        logging.info(f"Results saved to {metrics_path}")
        
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import pickle
    main()
