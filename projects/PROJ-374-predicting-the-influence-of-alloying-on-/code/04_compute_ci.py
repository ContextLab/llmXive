import os
import sys
import json
import numpy as np
from pathlib import Path

def load_cv_fold_scores(filepath):
    """Load CV fold scores from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('fold_scores', [])

def calculate_confidence_interval(scores, confidence=0.95):
    """Calculate confidence interval from fold scores."""
    if len(scores) < 2:
        return None, None
    
    scores_array = np.array(scores)
    mean_score = np.mean(scores_array)
    std_score = np.std(scores_array, ddof=1)
    
    # For small samples, use t-distribution
    from scipy import stats
    n = len(scores_array)
    t_val = stats.t.ppf((1 + confidence) / 2, n - 1)
    margin = t_val * (std_score / np.sqrt(n))
    
    ci_lower = mean_score - margin
    ci_upper = mean_score + margin
    
    return ci_lower, ci_upper

def save_ci_results(ci_lower, ci_upper, r2_score, output_path):
    """Save confidence interval results to JSON."""
    results = {
        'r2_score': r2_score,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'confidence_level': 0.95
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for computing confidence intervals."""
    project_root = Path(__file__).parent.parent
    cv_scores_path = project_root / 'state' / 'cv_fold_scores.json'
    output_path = project_root / 'data' / 'processed' / 'ci_results.json'
    
    if not cv_scores_path.exists():
        print(f"Error: CV fold scores file not found at {cv_scores_path}", file=sys.stderr)
        sys.exit(1)
    
    fold_scores = load_cv_fold_scores(cv_scores_path)
    
    if len(fold_scores) == 0:
        print("Error: No fold scores found", file=sys.stderr)
        sys.exit(1)
    
    # Calculate mean R2 from fold scores
    r2_mean = np.mean(fold_scores)
    
    ci_lower, ci_upper = calculate_confidence_interval(fold_scores)
    
    if ci_lower is None:
        print("Error: Could not calculate confidence interval", file=sys.stderr)
        sys.exit(1)
    
    save_ci_results(ci_lower, ci_upper, r2_mean, output_path)
    print(f"Confidence interval saved to {output_path}")
    print(f"R²: {r2_mean:.4f} [{ci_lower:.4f}, {ci_upper:.4f}]")

if __name__ == '__main__':
    main()
