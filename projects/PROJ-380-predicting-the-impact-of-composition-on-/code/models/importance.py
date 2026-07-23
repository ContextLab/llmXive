import os
import sys
import json
import logging
import argparse
import numpy as np

from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import local project utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config import get_paths
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_and_data(artifact_path: str, data_path: str) -> Tuple[Any, List[str], np.ndarray, np.ndarray]:
    """
    Load the best model and the processed feature data from artifacts.
    
    Args:
        artifact_path: Path to the saved model pickle
        data_path: Path to the processed CSV file containing features and target
        
    Returns:
        Tuple of (model, feature_names, X, y)
    """
    import pickle
    import csv

    # Load Model
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}")
    
    with open(artifact_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load Data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")

    feature_names = []
    X_list = []
    y_list = []

    with open(data_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Identify target column (usually 'shear_modulus' or similar based on spec)
        target_col = None
        for h in headers:
            if 'shear' in h.lower() or 'modulus' in h.lower() or 'target' in h.lower():
                target_col = h
                break
        
        if not target_col:
            # Fallback to last column if standard naming not found
            target_col = headers[-1]
            logger.warning(f"Target column auto-detected as '{target_col}'")

        feature_names = [h for h in headers if h != target_col]

        for row in reader:
            X_list.append([float(row[f]) for f in feature_names])
            y_list.append(float(row[target_col]))

    return model, feature_names, np.array(X_list), np.array(y_list)

def compute_permutation_importance(model, X: np.ndarray, y: np.ndarray, 
                                   feature_names: List[str], 
                                   n_permutations: int = 100, 
                                   random_state: int = 42) -> Dict[str, Any]:
    """
    Compute permutation importance for the given model.
    
    Args:
        model: Trained scikit-learn compatible model
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names corresponding to X columns
        n_permutations: Number of permutations to perform per feature
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing importance scores and metadata
    """
    from sklearn.metrics import r2_score
    from sklearn.utils import check_random_state
    
    rng = check_random_state(random_state)
    
    # Baseline score
    baseline_score = r2_score(y, model.predict(X))
    
    importance_scores = {}
    p_values = {} # Placeholder for statistical significance if needed later
    
    logger.info(f"Starting permutation importance with {n_permutations} permutations...")
    
    for i, feature in enumerate(feature_names):
        scores = []
        for _ in range(n_permutations):
            X_perm = X.copy()
            # Shuffle the column for the current feature
            idx = rng.permutation(X.shape[0])
            X_perm[:, i] = X[idx, i]
            
            score = r2_score(y, model.predict(X_perm))
            scores.append(score)
        
        # Importance is the drop in R2
        drop = baseline_score - np.mean(scores)
        importance_scores[feature] = float(drop)
        
        # Simple p-value estimation (one-sided: is drop > 0?)
        # Count how many permuted scores were better than baseline (unlikely if feature is important)
        # Actually, we test if the mean drop is significantly > 0
        # Using a simple t-test against 0 or counting how many are > baseline
        # Here we just store the mean drop and std for now, p-value logic is complex without scipy in strict envs
        # We will calculate a simple empirical p-value: proportion of permuted scores >= baseline
        p_val = np.sum(np.array(scores) >= baseline_score) / n_permutations
        p_values[feature] = float(p_val)

    return {
        "baseline_r2": float(baseline_score),
        "n_permutations": n_permutations,
        "feature_importance": importance_scores,
        "p_values": p_values
    }

def save_importance_report(report_data: Dict[str, Any], output_path: str) -> None:
    """
    Save the importance report to a JSON file.
    
    CRITICAL: Ensures results are labeled as "predictive contribution" 
    and NOT "physical significance" as per FR-009 and T036.
    """
    # Enforce the labeling constraint
    if "title" in report_data:
        report_data["title"] = "Predictive Contribution Analysis (Permutation Importance)"
    else:
        report_data["title"] = "Predictive Contribution Analysis (Permutation Importance)"
    
    if "description" in report_data:
        report_data["description"] = (
            "This report details the predictive contribution of each compositional descriptor "
            "to the model's performance. These values represent the drop in R2 score when the "
            "feature is randomly shuffled. They indicate statistical predictive power, NOT "
            "physical causality or mechanistic significance."
        )
    else:
        report_data["description"] = (
            "This report details the predictive contribution of each compositional descriptor "
            "to the model's performance. These values represent the drop in R2 score when the "
            "feature is randomly shuffled. They indicate statistical predictive power, NOT "
            "physical causality or mechanistic significance."
        )

    # Ensure the JSON is written correctly
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Importance report saved to {output_path}")

def run_permutation_analysis(model_path: str, data_path: str, output_path: str, 
                             n_permutations: int = 100, random_state: int = 42) -> None:
    """
    Main orchestration function for permutation importance analysis.
    """
    logger.info(f"Loading model from {model_path} and data from {data_path}")
    model, feature_names, X, y = load_model_and_data(model_path, data_path)
    
    logger.info("Computing permutation importance...")
    result = compute_permutation_importance(
        model, X, y, feature_names, 
        n_permutations=n_permutations, 
        random_state=random_state
    )
    
    logger.info("Saving report with explicit 'predictive contribution' labeling...")
    save_importance_report(result, output_path)
    
    logger.info("Analysis complete.")

def main():
    """
    CLI entry point for T036 / US3 importance analysis.
    """
    parser = argparse.ArgumentParser(description="Run Permutation Importance Analysis")
    parser.add_argument("--model", type=str, required=True, help="Path to trained model pickle")
    parser.add_argument("--data", type=str, required=True, help="Path to processed CSV data")
    parser.add_argument("--output", type=str, required=True, help="Path to save JSON report")
    parser.add_argument("--perms", type=int, default=100, help="Number of permutations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Validate paths exist
    if not os.path.exists(args.model):
        logger.error(f"Model file not found: {args.model}")
        sys.exit(1)
    if not os.path.exists(args.data):
        logger.error(f"Data file not found: {args.data}")
        sys.exit(1)
        
    run_permutation_analysis(
        args.model, 
        args.data, 
        args.output, 
        args.perms, 
        args.seed
    )

if __name__ == "__main__":
    main()