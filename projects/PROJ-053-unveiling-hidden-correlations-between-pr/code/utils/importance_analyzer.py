import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import requests
from pathlib import Path

from config import get_results_dir, get_models_dir, get_project_root
from utils.logger import setup_logging

def setup_importance_logger():
    """Setup logger for importance analysis."""
    return setup_logging("importance_analysis")

def load_literature_baseline(logger: logging.Logger) -> Optional[List[str]]:
    """
    Attempt to verify and load baseline rankings from literature via Crossref API.
    Returns a list of feature names in ranked order (most important first) if found.
    Returns None if not found or verification fails.
    """
    # Zenodo ID 4685643 corresponds to the dataset, but we need a specific paper
    # for baseline rankings. The spec mentions verifying existence via Crossref.
    # Since the spec does not provide a specific DOI for the baseline paper,
    # and Crossref metadata does not contain 'rankings', we cannot automatically
    # extract a ranking from Crossref.
    # We will attempt to query a generic search for the project topic to verify existence
    # of relevant literature, but we cannot extract a ranking without a specific source.
    # Therefore, this function will return None to trigger the fallback logic in the main task.
    
    logger.info("Attempting to verify literature source via Crossref API...")
    try:
        query = "additive manufacturing alloy processing parameters mechanical properties"
        url = f"https://api.crossref.org/works?query={query}&rows=1"
        headers = {"User-Agent": "llmXive-Project/1.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("message", {}).get("items"):
            logger.info("Literature source verified: Relevant papers found in Crossref.")
            # Note: Crossref does not provide feature importance rankings.
            # We cannot fabricate a ranking here.
            return None
        else:
            logger.warning("No relevant literature found in Crossref for baseline verification.")
            return None
    except Exception as e:
        logger.warning(f"Crossref verification failed: {e}. Proceeding without literature baseline.")
        return None

def get_hardcoded_baseline_ranking(logger: logging.Logger) -> Optional[List[str]]:
    """
    Return a hardcoded baseline ranking if specified in config.
    Currently returns None as per spec requirement to avoid hardcoded defaults unless verified.
    """
    # The spec says: "Do NOT use a hardcoded default" if no verified baseline is found.
    # This function exists to satisfy the API surface but returns None to enforce the logic.
    return None

def load_user_baseline(logger: logging.Logger) -> Optional[List[str]]:
    """
    Attempt to load user-provided baseline from data/baseline_importance.json.
    """
    base_path = get_project_root()
    baseline_file = base_path / "data" / "baseline_importance.json"
    
    if not baseline_file.exists():
        logger.info("User baseline file not found.")
        return None
    
    try:
        with open(baseline_file, 'r') as f:
            data = json.load(f)
            # Expected format: {"rankings": ["feature1", "feature2", ...]}
            if "rankings" in data:
                logger.info(f"Loaded user baseline from {baseline_file}")
                return data["rankings"]
            else:
                logger.warning("User baseline file found but missing 'rankings' key.")
                return None
    except Exception as e:
        logger.warning(f"Failed to load user baseline: {e}")
        return None

def calculate_permutation_importance(model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                                     feature_names: List[str], logger: logging.Logger) -> List[str]:
    """
    Calculate permutation importance and return feature names ranked by importance.
    """
    try:
        from sklearn.inspection import permutation_importance
        
        logger.info("Calculating permutation importance...")
        result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
        
        # Get mean importance
        importance_scores = result.importances_mean
        
        # Rank features (descending order of importance)
        ranked_indices = np.argsort(importance_scores)[::-1]
        ranked_features = [feature_names[i] for i in ranked_indices]
        
        logger.info(f"Top 3 features: {ranked_features[:3]}")
        return ranked_features
    except Exception as e:
        logger.error(f"Error calculating permutation importance: {e}")
        raise

def rank_list_to_feature_list(ranked_features: List[str]) -> List[int]:
    """
    Convert a list of feature names to a list of ranks (0-based index of position).
    Actually, for correlation, we need the rank of each feature.
    If input is ['A', 'B', 'C'], then A is rank 0, B is rank 1, C is rank 2.
    But correlation usually compares the rank vectors.
    Let's return the rank of each feature if we had a master list?
    No, the input IS the ranked list. So the rank of the feature at index i is i.
    We return the list of ranks corresponding to the order of features in the input list?
    Actually, for Spearman correlation, we just need the two lists of ranks.
    If we have two lists of feature names in ranked order, we can map them to ranks 0..N-1.
    """
    # The input is already a list of features in order of importance (0 = most important)
    # So the rank of the feature at index i is i.
    # We return the list of ranks [0, 1, 2, ...]
    return list(range(len(ranked_features)))

def calculate_correlation_coefficient(ranks_model: List[int], ranks_baseline: List[int]) -> float:
    """
    Calculate Spearman correlation coefficient between two rank lists.
    """
    if len(ranks_model) != len(ranks_baseline):
        raise ValueError("Rank lists must be of equal length")
    
    if len(ranks_model) == 0:
        return 0.0
        
    from scipy.stats import spearmanr
    corr, _ = spearmanr(ranks_model, ranks_baseline)
    return float(corr)

def run_correlation_analysis(model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                             feature_names: List[str], logger: logging.Logger) -> Dict[str, Any]:
    """
    Main function to run the correlation analysis for T031.
    """
    results = {
        "permutation_importance": [],
        "baseline_found": False,
        "correlation_coefficient": None,
        "message": ""
    }
    
    # 1. Calculate Permutation Importance
    try:
        model_ranked_features = calculate_permutation_importance(model, X_test, y_test, feature_names, logger)
        results["permutation_importance"] = model_ranked_features
        model_ranks = rank_list_to_feature_list(model_ranked_features)
    except Exception as e:
        logger.error(f"Failed to calculate permutation importance: {e}")
        results["message"] = f"Failed to calculate importance: {e}"
        return results

    # 2. Verify Literature Source (Crossref)
    lit_baseline = load_literature_baseline(logger)
    
    # 3. User Baseline
    user_baseline = load_user_baseline(logger)
    
    # 4. Hardcoded Baseline (if any, though spec says avoid)
    hardcoded_baseline = get_hardcoded_baseline_ranking(logger)
    
    # Determine which baseline to use
    selected_baseline = None
    baseline_source = None
    
    if lit_baseline:
        selected_baseline = lit_baseline
        baseline_source = "literature"
    elif user_baseline:
        selected_baseline = user_baseline
        baseline_source = "user"
    elif hardcoded_baseline:
        selected_baseline = hardcoded_baseline
        baseline_source = "hardcoded"
    
    if selected_baseline is None:
        logger.warning("No verified baseline found for SC-004; correlation metric skipped.")
        results["message"] = "No verified baseline found; correlation skipped."
        return results
    
    results["baseline_found"] = True
    results["baseline_source"] = baseline_source
    results["baseline_ranking"] = selected_baseline
    
    # 5. Calculate Correlation
    try:
        # We need to align the ranks.
        # We have model_ranked_features (list of names in order)
        # We have selected_baseline (list of names in order)
        # We need to find the rank of each feature in the model list relative to the baseline list?
        # Actually, Spearman correlation compares the rank of each item.
        # Let's create a mapping of feature -> rank for both lists.
        # Then we compute correlation on the ranks of the union of features?
        # Or just the intersection?
        # Let's assume the lists contain the same features.
        
        # Create rank maps
        model_rank_map = {feat: i for i, feat in enumerate(model_ranked_features)}
        baseline_rank_map = {feat: i for i, feat in enumerate(selected_baseline)}
        
        # Common features
        common_features = list(set(model_rank_map.keys()) & set(baseline_rank_map.keys()))
        
        if not common_features:
            logger.warning("No common features between model and baseline rankings.")
            results["message"] = "No common features for correlation."
            return results
        
        # Extract ranks for common features
        model_ranks_common = [model_rank_map[f] for f in common_features]
        baseline_ranks_common = [baseline_rank_map[f] for f in common_features]
        
        corr = calculate_correlation_coefficient(model_ranks_common, baseline_ranks_common)
        results["correlation_coefficient"] = corr
        results["message"] = f"Correlation calculated successfully (source: {baseline_source})."
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        results["message"] = f"Correlation calculation failed: {e}"
    
    return results

def main():
    """Entry point for T031."""
    logger = setup_importance_logger()
    logger.info("Starting T031: Permutation Importance Correlation Analysis")
    
    # Load model
    models_dir = get_models_dir()
    model_path = models_dir / "gpr_model.pkl"
    
    if not model_path.exists():
        logger.error("GPR model not found. Run T026 first.")
        return
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load test data
    # We need X_test and feature_names.
    # Assuming they are stored in a processed file or we load from the pipeline.
    # For T031, we assume the preprocessed data is available at data/processed/train_test_split.pkl
    # Or we load the test set from the same source used in metrics.
    # Let's try to load from a standard location or reconstruct.
    # Since we don't have a specific file path for test data in the API surface for T031,
    # we will assume the main pipeline saves it or we load it from the processed directory.
    # A common pattern is to save the test data split.
    processed_dir = get_project_root() / "data" / "processed"
    test_data_path = processed_dir / "test_data.pkl"
    
    if not test_data_path.exists():
        # Fallback: try to load from metrics or reconstruct?
        # If not found, we cannot proceed.
        logger.error("Test data not found. Cannot run permutation importance.")
        return
    
    with open(test_data_path, 'rb') as f:
        test_data = pickle.load(f)
        X_test = test_data['X_test']
        y_test = test_data['y_test']
        feature_names = test_data['feature_names']
    
    # Run analysis
    results = run_correlation_analysis(model, X_test, y_test, feature_names, logger)
    
    # Save results
    results_dir = get_results_dir()
    metrics_path = results_dir / "metrics.json"
    
    # Load existing metrics
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    
    # Append T031 results
    metrics["t031_correlation_analysis"] = results
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results saved to {metrics_path}")
    logger.info("T031 completed.")

if __name__ == "__main__":
    main()
