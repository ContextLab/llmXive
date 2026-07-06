"""
Task T026b: Calculate 95% Confidence Interval for R² score from CV fold scores.

This script loads the cross-validation fold scores saved by T025
(state/cv_fold_scores.json) and computes the 95% confidence interval
for the R² score using the empirical distribution of fold scores.

Per FR-008 and task specification:
- CI is derived STRICTLY from CV fold scores.
- Do NOT use permutation distribution for CI.
- Output is saved to data/processed/ci_results.json
"""
import os
import sys
import json
import numpy as np
from pathlib import Path

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_cv_fold_scores():
    """Load CV fold scores from state/cv_fold_scores.json"""
    cv_scores_path = PROJECT_ROOT / "state" / "cv_fold_scores.json"
    
    if not cv_scores_path.exists():
        raise FileNotFoundError(
            f"CV fold scores file not found at {cv_scores_path}. "
            "Please ensure T025 has been completed successfully."
        )
    
    with open(cv_scores_path, 'r') as f:
        data = json.load(f)
    
    # Extract the list of fold R² scores
    # Expected structure: {"fold_scores": [r2_1, r2_2, ...], ...}
    if "fold_scores" not in data:
        raise ValueError(
            f"Expected 'fold_scores' key in {cv_scores_path}. "
            f"Found keys: {list(data.keys())}"
        )
    
    fold_scores = data["fold_scores"]
    
    if not isinstance(fold_scores, list) or len(fold_scores) == 0:
        raise ValueError("fold_scores must be a non-empty list of R² values")
    
    return np.array(fold_scores)

def calculate_confidence_interval(scores, confidence_level=0.95):
    """
    Calculate confidence interval for the mean of the scores.
    
    Uses the empirical percentile method on the distribution of fold scores.
    This is appropriate when the number of folds is small (e.g., 5-fold CV).
    
    Args:
        scores: Array of R² scores from CV folds
        confidence_level: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        tuple: (mean_r2, ci_lower, ci_upper)
    """
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores, ddof=1)  # Sample std
    n = len(scores)
    
    # For small sample sizes (n < 30), use t-distribution
    # For n >= 30, normal approximation is acceptable
    from scipy import stats
    
    if n < 30:
        # t-distribution for small samples
        t_critical = stats.t.ppf((1 + confidence_level) / 2, df=n-1)
        margin_of_error = t_critical * (std_r2 / np.sqrt(n))
    else:
        # Normal approximation for larger samples
        z_critical = stats.norm.ppf((1 + confidence_level) / 2)
        margin_of_error = z_critical * (std_r2 / np.sqrt(n))
    
    ci_lower = mean_r2 - margin_of_error
    ci_upper = mean_r2 + margin_of_error
    
    return mean_r2, ci_lower, ci_upper

def save_ci_results(mean_r2, ci_lower, ci_upper, fold_scores):
    """Save CI results to data/processed/ci_results.json"""
    output_path = PROJECT_ROOT / "data" / "processed" / "ci_results.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "mean_r2": float(mean_r2),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": 0.95,
        "n_folds": len(fold_scores),
        "fold_scores": [float(s) for s in fold_scores],
        "method": "t-distribution" if len(fold_scores) < 30 else "normal-approximation",
        "source": "state/cv_fold_scores.json (from T025)"
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Confidence interval results saved to {output_path}")
    return results

def main():
    """Main entry point for T026b"""
    print("Task T026b: Computing 95% Confidence Interval from CV fold scores...")
    
    try:
        # Load CV fold scores from T025
        fold_scores = load_cv_fold_scores()
        print(f"  Loaded {len(fold_scores)} fold R² scores: {fold_scores.tolist()}")
        
        # Calculate confidence interval
        mean_r2, ci_lower, ci_upper = calculate_confidence_interval(fold_scores)
        
        print(f"  Mean R²: {mean_r2:.4f}")
        print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        
        # Save results
        results = save_ci_results(mean_r2, ci_lower, ci_upper, fold_scores)
        
        print("✓ Task T026b completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print("  Ensure T025 has been completed and state/cv_fold_scores.json exists.")
        return 1
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())