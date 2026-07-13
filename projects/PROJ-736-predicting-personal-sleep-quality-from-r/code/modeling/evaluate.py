"""
Evaluation script for the sleep quality prediction model.
"""
import os
import sys
import json
import signal
import time
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs, get_config

def load_predictions(path: str) -> np.ndarray:
    if os.path.exists(path):
        return np.load(path)
    return None

def bootstrap_resample_r2(y_true: np.ndarray, y_pred: np.ndarray, n_bootstrap: int = 1000) -> List[float]:
    """
    Performs bootstrap resampling to estimate confidence intervals for R2.
    """
    n = len(y_true)
    r2_scores = []
    for _ in range(n_bootstrap):
        indices = np.random.choice(n, n, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        # Calculate R2
        ss_res = np.sum((y_true_boot - y_pred_boot) ** 2)
        ss_tot = np.sum((y_true_boot - np.mean(y_true_boot)) ** 2)
        if ss_tot == 0:
            r2 = 0
        else:
            r2 = 1 - (ss_res / ss_tot)
        r2_scores.append(r2)
    
    return r2_scores

def run_permutation_test(X: np.ndarray, y: np.ndarray, pipeline, n_permutations: int = 1000) -> float:
    """
    Runs a permutation test to estimate p-value.
    """
    # Fit original
    pipeline.fit(X, y)
    orig_score = pipeline.score(X, y)
    
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y)
        pipeline.fit(X, y_perm)
        score = pipeline.score(X, y_perm)
        perm_scores.append(score)
    
    # P-value: proportion of permuted scores >= original score
    p_val = np.mean(np.array(perm_scores) >= orig_score)
    return p_val

def main() -> int:
    """
    Main entry point for evaluation.
    """
    paths = get_paths()
    ensure_dirs(paths)
    
    pred_path = os.path.join(paths["data_processed"], "predictions.npy")
    behavioral_file = os.path.join(paths["data_raw_behavioral"], "hcp1200_behavioral_data.csv")
    
    import pandas as pd
    df = pd.read_csv(behavioral_file)
    subjects_file = paths["data_raw"] / "filtered_subjects.txt"
    with open(subjects_file, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]
    
    y_true = df[df['Subject'].isin(subjects)]['Sleep_Score'].values
    y_pred = load_predictions(pred_path)
    
    if y_pred is None or len(y_true) == 0:
        print("No predictions or labels found.")
        return 1
    
    # Bootstrap
    print("Running bootstrap resampling...")
    boot_scores = bootstrap_resample_r2(y_true, y_pred, n_bootstrap=100) # Reduced for CI
    
    ci_lower = np.percentile(boot_scores, 2.5)
    ci_upper = np.percentile(boot_scores, 97.5)
    
    # Save results
    results = {
        "bootstrap_ci_95": [float(ci_lower), float(ci_upper)],
        "n_bootstrap": 100
    }
    
    results_path = os.path.join(paths["data_results"], "evaluation_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Evaluation complete. 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
