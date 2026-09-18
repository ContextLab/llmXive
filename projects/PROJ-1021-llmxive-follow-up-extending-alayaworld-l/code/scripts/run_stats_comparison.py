"""
Statistical test script to compare Baseline vs. Hybrid drift scores.
Implements Wilcoxon signed-rank test and Shapiro-Wilk pre-check.
Output: data/stats_comparison.json

This script expects:
- data/baseline_scores.json
- data/hybrid_scores.json
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from scipy.stats import wilcoxon, shapiro

# Add code directory to path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

def load_scores(filepath):
    """Load scores from JSON file and extract the score values."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if "scores" not in data:
        raise ValueError(f"Invalid format in {filepath}: 'scores' key missing")
    
    # Extract just the score values, maintaining order
    scores = [entry["score"] for entry in data["scores"]]
    
    if len(scores) == 0:
        raise ValueError(f"No scores found in {filepath}")
    
    return scores

def main():
    project_root = Path(__file__).parent.parent.parent
    baseline_path = project_root / "data" / "baseline_scores.json"
    hybrid_path = project_root / "data" / "hybrid_scores.json"
    output_path = project_root / "data" / "stats_comparison.json"

    print(f"Loading baseline scores from {baseline_path}...")
    try:
        baseline_scores = load_scores(baseline_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        # Create a failure report
        result = {
            "status": "FAILED",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shapiro_p_value": None,
            "wilcoxon_p_value": None,
            "mean_baseline": None,
            "mean_hybrid": None,
            "reduction_percent": None
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    print(f"Loading hybrid scores from {hybrid_path}...")
    try:
        hybrid_scores = load_scores(hybrid_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        result = {
            "status": "FAILED",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shapiro_p_value": None,
            "wilcoxon_p_value": None,
            "mean_baseline": None,
            "mean_hybrid": None,
            "reduction_percent": None
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    # Ensure paired data (same length)
    if len(baseline_scores) != len(hybrid_scores):
        print(f"WARNING: Score counts differ. Baseline: {len(baseline_scores)}, Hybrid: {len(hybrid_scores)}. Truncating to shortest.")
        min_len = min(len(baseline_scores), len(hybrid_scores))
        baseline_scores = baseline_scores[:min_len]
        hybrid_scores = hybrid_scores[:min_len]

    if len(baseline_scores) < 2:
        print("ERROR: Not enough data points for statistical testing (need at least 2).")
        result = {
            "status": "FAILED",
            "error": "Insufficient data points",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shapiro_p_value": None,
            "wilcoxon_p_value": None,
            "mean_baseline": None,
            "mean_hybrid": None,
            "reduction_percent": None
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    print(f"Running Shapiro-Wilk test on paired differences...")
    diffs = [b - h for b, h in zip(baseline_scores, hybrid_scores)]
    
    try:
        shapiro_stat, shapiro_p = shapiro(diffs)
    except Exception as e:
        print(f"ERROR in Shapiro-Wilk test: {e}")
        result = {
            "status": "FAILED",
            "error": f"Shapiro-Wilk test failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shapiro_p_value": None,
            "wilcoxon_p_value": None,
            "mean_baseline": None,
            "mean_hybrid": None,
            "reduction_percent": None
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    print(f"Shapiro-Wilk p-value: {shapiro_p:.4f}")
    
    # If p > 0.05, data is non-normal, justifying Wilcoxon (which is robust to non-normality anyway)
    # We proceed with Wilcoxon regardless as it is the specified non-parametric test.

    print(f"Running Wilcoxon signed-rank test...")
    try:
        wilcoxon_stat, wilcoxon_p = wilcoxon(baseline_scores, hybrid_scores)
    except Exception as e:
        print(f"ERROR in Wilcoxon test: {e}")
        result = {
            "status": "FAILED",
            "error": f"Wilcoxon test failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shapiro_p_value": float(shapiro_p),
            "wilcoxon_p_value": None,
            "mean_baseline": None,
            "mean_hybrid": None,
            "reduction_percent": None
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)

    print(f"Wilcoxon p-value: {wilcoxon_p:.4f}")

    # Calculate statistics
    mean_baseline = sum(baseline_scores) / len(baseline_scores)
    mean_hybrid = sum(hybrid_scores) / len(hybrid_scores)
    
    if mean_baseline != 0:
        reduction_percent = ((mean_baseline - mean_hybrid) / mean_baseline) * 100
    else:
        reduction_percent = 0.0 if mean_hybrid == 0 else None

    # Determine status based on Wilcoxon p-value
    status = "SIGNIFICANT" if wilcoxon_p < 0.05 else "NOT_SIGNIFICANT"

    result = {
        "status": status,
        "shapiro_p_value": float(shapiro_p),
        "wilcoxon_p_value": float(wilcoxon_p),
        "mean_baseline": float(mean_baseline),
        "mean_hybrid": float(mean_hybrid),
        "reduction_percent": float(reduction_percent) if reduction_percent is not None else None,
        "n_samples": len(baseline_scores),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"Writing results to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print("Done.")
    print(f"Summary: Mean Baseline={mean_baseline:.4f}, Mean Hybrid={mean_hybrid:.4f}, "
          f"Reduction={reduction_percent:.2f}%, Wilcoxon p={wilcoxon_p:.4f} ({status})")

if __name__ == "__main__":
    main()