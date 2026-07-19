import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import hashlib
import subprocess
from pathlib import Path

# Import shared utilities from project infrastructure if available, 
# otherwise define minimal local versions to ensure standalone execution.
try:
    from infrastructure.path_utils import get_project_root, ensure_dir
except ImportError:
    def get_project_root():
        return Path(__file__).parent.parent

    def ensure_dir(path: str):
        Path(path).mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_git_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_output_directories():
    root = get_project_root()
    ensure_dir(str(root / "data" / "processed"))
    ensure_dir(str(root / "data" / "validation"))

def load_processed_data():
    root = get_project_root()
    features_path = root / "data" / "processed" / "features.csv"
    targets_path = root / "data" / "processed" / "targets.csv"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(
            f"Processed data files not found at {features_path} or {targets_path}. "
            "Please run T018 and T020 first."
        )
    
    X = pd.read_csv(features_path)
    y = pd.read_csv(targets_path)
    return X, y

def load_models():
    root = get_project_root()
    models_path = root / "data" / "processed" / "models.pkl"
    if not models_path.exists():
        raise FileNotFoundError(f"Models file not found at {models_path}. Run T021 first.")
    
    import pickle
    with open(models_path, 'rb') as f:
        models = pickle.load(f)
    return models

def calculate_metrics(y_true, y_pred):
    from sklearn.metrics import r2_score, mean_absolute_percentage_error
    r2 = r2_score(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    return {"r2": r2, "mape": mape}

def run_holdout_evaluation():
    # Placeholder for T024 logic if needed here, but T024 is separate.
    pass

def compute_permutation_p_values(X: pd.DataFrame, y: pd.Series, models: Dict[str, Any], n_permutations: int = 1000, random_state: int = 42):
    """
    Computes p-values for feature importance using permutation testing.
    
    For each feature, we:
    1. Calculate the baseline score (R2) of the model.
    2. Permute the feature values n_permutations times.
    3. Calculate the score after permutation.
    4. The p-value is the proportion of permutations where the permuted score 
       is greater than or equal to the baseline score (indicating the feature 
       is not important).
    
    Returns a dictionary of p-values for each feature across the three models.
    """
    rng = np.random.default_rng(random_state)
    feature_names = X.columns.tolist()
    results = {model_name: {feat: [] for feat in feature_names} for model_name in models}
    
    logger.info(f"Starting permutation importance for {len(feature_names)} features and {len(models)} models.")
    logger.info(f"Performing {n_permutations} permutations.")

    for model_name, model in models.items():
        # Get baseline score
        y_pred_base = model.predict(X)
        # We use R2 as the metric. Higher is better.
        # If we want to test "is this feature important?", we check if shuffling it 
        # significantly decreases performance.
        # P-value = P(Score_permuted >= Score_baseline) under the null hypothesis that the feature is irrelevant.
        # Actually, standard permutation test: 
        # Null Hypothesis: Feature Xj has no effect on Y.
        # If we permute Xj, and the model performance drops significantly, we reject null.
        # P-value = (count of permuted scores >= baseline score) / n_permutations? 
        # No, usually we look at the distribution of permuted scores. 
        # If the baseline is better than most permuted scores, the feature is important.
        # Let's define p-value as the fraction of times the permuted score is >= baseline.
        # If p is low, it means permuted scores are usually worse, so the feature is important.
        
        baseline_score = r2_score(y, y_pred_base)
        
        for i, feat in enumerate(feature_names):
            logger.debug(f"Model {model_name}: Permuting feature {feat} ({i+1}/{len(feature_names)})")
            perm_scores = []
            for _ in range(n_permutations):
                X_perm = X.copy()
                X_perm[feat] = rng.permutation(X_perm[feat])
                y_pred_perm = model.predict(X_perm)
                score = r2_score(y, y_pred_perm)
                perm_scores.append(score)
            
            # Calculate p-value: proportion of permuted scores that are >= baseline
            # If the feature is important, permuting it should hurt performance (lower score).
            # So we expect few permuted scores to be >= baseline.
            # Thus, a small p-value indicates importance.
            p_val = np.mean(np.array(perm_scores) >= baseline_score)
            results[model_name][feat] = p_val

    return results

def apply_benjamini_hochberg(p_values: Dict[str, Dict[str, float]], q: float = 0.05) -> Dict[str, Dict[str, bool]]:
    """
    Applies the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
    
    Args:
        p_values: Dictionary mapping model_name -> {feature_name -> p_value}
        q: FDR threshold (default 0.05)
    
    Returns:
        Dictionary mapping model_name -> {feature_name -> is_significant (bool)}
    """
    results = {}
    for model_name, model_pvals in p_values.items():
        # Flatten to list of (feature, p_value)
        items = list(model_pvals.items())
        m = len(items)
        if m == 0:
            continue
        
        # Sort by p-value
        sorted_items = sorted(items, key=lambda x: x[1])
        
        # BH procedure
        # We want to find the largest k such that p_(k) <= (k/m) * q
        # Then reject all hypotheses with p <= p_(k)
        
        significant = {}
        k_star = 0
        threshold = 0.0
        
        # Calculate thresholds
        # p_(i) <= (i/m) * q
        # We iterate from smallest p to largest
        # Find the largest i where condition holds
        
        indices = []
        for i, (feat, p_val) in enumerate(sorted_items):
            rank = i + 1
            if p_val <= (rank / m) * q:
                k_star = rank
                threshold = p_val
                indices.append(feat)
        
        # All features with p <= threshold are significant
        for feat, p_val in model_pvals.items():
            significant[feat] = p_val <= threshold
        
        results[model_name] = significant
        
        logger.info(f"Model {model_name}: Applied BH FDR (q={q}). Found {sum(significant.values())} significant features out of {m}.")
        
    return results

def rank_features(p_values: Dict[str, Dict[str, float]]) -> Dict[str, List[Tuple[str, float]]]:
    """
    Ranks features by p-value (ascending) for each model.
    Lower p-value = more significant.
    """
    ranked = {}
    for model_name, model_pvals in p_values.items():
        sorted_items = sorted(model_pvals.items(), key=lambda x: x[1])
        ranked[model_name] = sorted_items
    return ranked

def run_sensitivity_analysis():
    # Placeholder for T026 logic
    pass

def run_confounding_control():
    # Placeholder for T027a logic
    pass

def run_inference_analysis():
    """
    Main entry point for T025: Permutation Importance & FDR.
    """
    ensure_output_directories()
    
    try:
        X, y = load_processed_data()
        models = load_models()
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    logger.info("Computing permutation p-values...")
    # Use a sufficient number of permutations (e.g., 1000) as per task description
    p_values = compute_permutation_p_values(X, y, models, n_permutations=1000, random_state=42)
    
    logger.info("Applying Benjamini-Hochberg FDR control...")
    fdr_results = apply_benjamini_hochberg(p_values, q=0.05)
    
    logger.info("Ranking features...")
    rankings = rank_features(p_values)
    
    # Prepare output
    output_data = {
        "git_hash": get_git_hash(),
        "n_permutations": 1000,
        "fdr_threshold": 0.05,
        "p_values": p_values,
        "fdr_significant": fdr_results,
        "rankings": rankings
    }
    
    # Save results
    root = get_project_root()
    output_path = root / "data" / "processed" / "permutation_fdr_results.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Also create a summary CSV for easy viewing
    summary_rows = []
    for model_name, model_ranking in rankings.items():
        for rank, (feat, p_val) in enumerate(model_ranking, 1):
            is_sig = fdr_results[model_name].get(feat, False)
            summary_rows.append({
                "model": model_name,
                "rank": rank,
                "feature": feat,
                "p_value": p_val,
                "is_significant_fdr_005": is_sig
            })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_path = root / "data" / "processed" / "feature_influence_rankings.csv"
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"Summary rankings saved to {summary_path}")

def main():
    run_inference_analysis()

if __name__ == "__main__":
    main()
