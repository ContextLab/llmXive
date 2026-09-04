import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import (
    get_results_dir,
    get_models_dir,
    get_data_dir,
    get_literature_citation,
    get_hardcoded_baseline_ranking,
    ensure_directories,
    get_random_seed
)
from utils.logger import setup_logging

# Configure logger for this module
def setup_importance_logger() -> logging.Logger:
    """Setup logger for importance analysis."""
    return setup_logging("importance_analyzer")

def load_literature_baseline(citation_key: str) -> List[float]:
    """
    Load the literature baseline ranking from config.py.
    
    Args:
        citation_key: The key in config.py containing the citation or data.
        
    Returns:
        List of float importance values corresponding to features.
        
    Raises:
        ValueError: If the citation is missing or invalid.
    """
    # Attempt to retrieve the baseline data from config
    # The config key 'get_hardcoded_baseline_ranking' is expected to return the list
    # or 'get_literature_citation' might contain a path/ID to fetch.
    # Based on T031 spec: "load the citation key... If this key is missing... raise ValueError"
    
    # Strategy: Try to get the hardcoded ranking first (as a verified source)
    # If that returns None, try to interpret the citation as a data source (e.g., JSON path)
    # For this implementation, we assume config provides the verified list directly
    # or a path to a verified JSON file.
    
    baseline_data = get_hardcoded_baseline_ranking()
    
    if baseline_data is not None:
        if isinstance(baseline_data, list):
            return [float(x) for x in baseline_data]
        elif isinstance(baseline_data, str):
            # If it's a string, assume it's a path to a verified JSON file
            path = Path(baseline_data)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    return [float(x) for x in data.get('ranking', [])]
            else:
                # If string is not a path, it might be a citation ID, which we can't resolve without network
                # But per strict constraint: "If this key is missing or the citation cannot be verified... raise ValueError"
                # We treat a non-existent file path as a failure to verify.
                pass
    
    # Fallback: Check if the citation key itself holds the data (rare but possible)
    citation_str = get_literature_citation()
    if citation_str and isinstance(citation_str, str):
        # Check if it looks like a JSON string (unlikely for a citation)
        try:
            data = json.loads(citation_str)
            if 'ranking' in data:
                return [float(x) for x in data['ranking']]
        except json.JSONDecodeError:
            pass
    
    raise ValueError(
        "Verified Accuracy Violation: No user-provided baseline and no verified literature citation found in config.py. "
        "SC-004 cannot be satisfied. Halting."
    )

def get_hardcoded_baseline_ranking() -> Optional[List[float]]:
    """
    Wrapper to ensure we have the correct import from config.
    This is a fallback if the direct config import isn't sufficient.
    """
    # This function is already imported from config in the main import block above.
    # We define it here to satisfy the 'public names' list if needed, 
    # but the real logic is in config.py.
    return None

def load_user_baseline(file_path: str) -> List[float]:
    """
    Load user-provided baseline importance from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the baseline ranking.
        
    Returns:
        List of float importance values.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"User baseline file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    if 'ranking' not in data:
        raise ValueError("User baseline file missing 'ranking' key.")
        
    return [float(x) for x in data['ranking']]

def calculate_permutation_importance(model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                                     feature_names: List[str], n_repeats: int = 5, 
                                     random_state: Optional[int] = None) -> Dict[str, float]:
    """
    Calculate permutation importance for the trained model.
    
    Args:
        model: The trained GPR model.
        X_test: Test features.
        y_test: Test targets.
        feature_names: List of feature names.
        n_repeats: Number of times to permute a feature.
        random_state: Random seed.
        
    Returns:
        Dictionary mapping feature names to their importance scores.
    """
    if random_state is None:
        random_state = get_random_seed()
        
    np.random.seed(random_state)
    
    # Get baseline score (R2)
    from sklearn.metrics import r2_score
    baseline_score = r2_score(y_test, model.predict(X_test))
    
    importances = {}
    
    for i, feature in enumerate(feature_names):
        # Create a copy of X_test
        X_permuted = X_test.copy()
        
        # Permute the column
        perm_idx = np.random.permutation(len(X_permuted))
        X_permuted[:, i] = X_permuted[perm_idx, i]
        
        # Calculate score with permuted feature
        perm_score = r2_score(y_test, model.predict(X_permuted))
        
        # Importance is the decrease in score
        importances[feature] = baseline_score - perm_score
        
    return importances

def rank_list_to_feature_list(importance_dict: Dict[str, float]) -> Tuple[List[str], List[float]]:
    """
    Convert importance dictionary to sorted lists of features and values.
    
    Args:
        importance_dict: Dictionary of feature -> importance.
        
    Returns:
        Tuple of (feature_names_sorted, importance_values_sorted).
    """
    sorted_items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    features = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]
    return features, values

def calculate_correlation_coefficient(list1: List[float], list2: List[float]) -> float:
    """
    Calculate Spearman correlation between two lists.
    
    Args:
        list1: First list of values.
        list2: Second list of values.
        
    Returns:
        Spearman correlation coefficient.
    """
    if len(list1) != len(list2):
        raise ValueError("Lists must be of equal length for correlation.")
        
    # Use scipy if available, otherwise numpy fallback
    try:
        from scipy.stats import spearmanr
        corr, _ = spearmanr(list1, list2)
        return float(corr)
    except ImportError:
        # Fallback to numpy implementation of Spearman
        # Rank the data
        def rankdata(a):
            sorter = np.argsort(a)
            ranks = np.empty_like(sorter, dtype=float)
            ranks[sorter] = np.arange(1, len(a) + 1)
            return ranks
        
        rank1 = rankdata(np.array(list1))
        rank2 = rankdata(np.array(list2))
        
        # Pearson correlation of ranks
        mean1 = np.mean(rank1)
        mean2 = np.mean(rank2)
        
        num = np.sum((rank1 - mean1) * (rank2 - mean2))
        den = np.sqrt(np.sum((rank1 - mean1)**2) * np.sum((rank2 - mean2)**2))
        
        if den == 0:
            return 0.0
            
        return float(num / den)

def run_correlation_analysis(model_path: str, test_data_path: str, 
                             output_path: str, user_baseline_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to run the permutation importance correlation analysis.
    
    Args:
        model_path: Path to the saved GPR model.
        test_data_path: Path to the processed test CSV.
        output_path: Path to save the updated metrics JSON.
        user_baseline_path: Optional path to user-provided baseline JSON.
        
    Returns:
        Updated metrics dictionary.
    """
    logger = setup_importance_logger()
    logger.info("Starting permutation importance correlation analysis (T031).")
    
    # Load model
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Model loaded from {model_path}")
    
    # Load test data
    import pandas as pd
    df_test = pd.read_csv(test_data_path)
    
    # Identify feature columns (exclude target and non-numeric)
    # Assuming the last column is the target or we know the target name.
    # For this task, we assume 'yield_strength' or 'ductility' is the target.
    # We need to know which target the model was trained on.
    # Let's assume the model file contains metadata or we infer from column names.
    # A robust way: load the model's training features if stored, otherwise infer.
    # For this implementation, we assume the first N columns are features and the last is target,
    # or we look for specific known target names.
    
    target_candidates = ['yield_strength', 'ductility', 'fatigue_life']
    target_col = None
    for t in target_candidates:
        if t in df_test.columns:
            target_col = t
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column in test data.")
        
    feature_cols = [c for c in df_test.columns if c != target_col and df_test[c].dtype in ['float64', 'float32', 'int64', 'int32']]
    
    X_test = df_test[feature_cols].values
    y_test = df_test[target_col].values
    
    logger.info(f"Features: {feature_cols}")
    logger.info(f"Target: {target_col}")
    
    # Calculate Permutation Importance
    importance_dict = calculate_permutation_importance(model, X_test, y_test, feature_cols)
    model_features, model_importance = rank_list_to_feature_list(importance_dict)
    logger.info(f"Model Importance: {importance_dict}")
    
    # Load Baseline
    baseline_importance = []
    baseline_source = "unknown"
    
    if user_baseline_path:
        try:
            baseline_importance = load_user_baseline(user_baseline_path)
            baseline_source = f"user_file:{user_baseline_path}"
            logger.info(f"Loaded user baseline from {user_baseline_path}")
        except Exception as e:
            logger.warning(f"Failed to load user baseline: {e}. Falling back to literature.")
            baseline_importance = None
    
    if not baseline_importance:
        # Load from literature/verified source
        baseline_importance = load_literature_baseline("LITERATURE_BASELINE_CITATION")
        baseline_source = "literature_citation"
        logger.info("Loaded baseline from literature citation.")
    
    # Ensure lengths match
    if len(baseline_importance) != len(model_importance):
        # If the baseline has different features, we need to align them.
        # For simplicity in this task, we assume the order of features is the same
        # as the sorted model importance list, or the baseline is a subset.
        # However, the spec says "Spearman correlation between model ranking and baseline ranking".
        # This implies we compare the RANKS, not the raw values.
        # So we need the same set of features.
        # If baseline is a list of values corresponding to the SAME features in the SAME order:
        # We assume the baseline list corresponds to the feature order in 'feature_cols' 
        # or the sorted order.
        # Given the ambiguity, we will assume the baseline list corresponds to the 
        # features in the order they were passed to the model (feature_cols).
        # But model_importance is sorted.
        # Let's re-calculate baseline importance for the specific features if possible.
        # Since we don't have the baseline model, we assume the provided list corresponds 
        # to the features in the order of 'feature_cols' (unsorted).
        
        # If the baseline list length matches feature_cols:
        if len(baseline_importance) == len(feature_cols):
            # Re-sort baseline to match model_features order
            # We need a mapping from feature name to baseline value
            # Assuming baseline_importance is in the order of feature_cols
            baseline_map = {f: v for f, v in zip(feature_cols, baseline_importance)}
            # Now extract values in the order of model_features
            baseline_sorted = [baseline_map[f] for f in model_features]
            baseline_importance = baseline_sorted
        else:
            # If lengths still don't match, we cannot compute correlation reliably.
            # We raise an error as per strict requirements.
            raise ValueError(f"Feature count mismatch: Model has {len(model_features)}, Baseline has {len(baseline_importance)}. "
                             "Cannot compute correlation.")
    
    # Calculate Spearman Correlation
    correlation = calculate_correlation_coefficient(model_importance, baseline_importance)
    logger.info(f"Spearman Correlation: {correlation}")
    
    # Load existing metrics
    results_dir = get_results_dir()
    metrics_path = Path(output_path)
    if not metrics_path.is_absolute():
        metrics_path = Path(results_dir) / output_path
        
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    
    # Update metrics
    metrics['permutation_importance_correlation'] = float(correlation)
    metrics['baseline_source'] = baseline_source
    metrics['model_ranking'] = model_features
    metrics['model_importance_values'] = model_importance
    metrics['baseline_ranking'] = baseline_importance # Assuming sorted now
    
    # Save metrics
    ensure_directories(str(metrics_path.parent))
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Metrics saved to {metrics_path}")
    return metrics

def main():
    """Entry point for T031 execution."""
    logger = setup_importance_logger()
    logger.info("Executing T031: Permutation Importance Correlation Analysis")
    
    # Paths
    model_path = Path(get_models_dir()) / "gpr_model.pkl"
    test_data_path = Path(get_data_dir()) / "processed" / "test.csv"
    output_metrics_path = Path(get_results_dir()) / "metrics.json"
    
    # Optional user baseline
    user_baseline_path = Path(get_data_dir()) / "baseline_importance.json"
    if not user_baseline_path.exists():
        user_baseline_path = None
        
    try:
        run_correlation_analysis(
            model_path=str(model_path),
            test_data_path=str(test_data_path),
            output_path=str(output_metrics_path),
            user_baseline_path=str(user_baseline_path) if user_baseline_path else None
        )
        logger.info("T031 completed successfully.")
    except Exception as e:
        logger.error(f"T031 failed: {e}")
        raise

if __name__ == "__main__":
    main()
