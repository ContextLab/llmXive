import os
import sys
import json
import numpy as np
from pathlib import Path

def load_json_file(filepath):
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_confidence_interval(scores, confidence=0.95):
    """Calculate confidence interval from scores."""
    if len(scores) < 2:
        return None, None
    
    scores_array = np.array(scores)
    mean_score = np.mean(scores_array)
    std_score = np.std(scores_array, ddof=1)
    
    from scipy import stats
    n = len(scores_array)
    t_val = stats.t.ppf((1 + confidence) / 2, n - 1)
    margin = t_val * (std_score / np.sqrt(n))
    
    ci_lower = mean_score - margin
    ci_upper = mean_score + margin
    
    return ci_lower, ci_upper

def main():
    """Main entry point for saving model output."""
    project_root = Path(__file__).parent.parent
    
    # Load results from training
    train_results_path = project_root / 'data' / 'processed' / 'model_metrics.json'
    ci_results_path = project_root / 'data' / 'processed' / 'ci_results.json'
    output_path = project_root / 'data' / 'processed' / 'model_output.json'
    
    if not train_results_path.exists():
        print(f"Error: Training results not found at {train_results_path}", file=sys.stderr)
        sys.exit(1)
    
    train_results = load_json_file(train_results_path)
    
    # Load CI results
    if not ci_results_path.exists():
        print(f"Error: CI results not found at {ci_results_path}", file=sys.stderr)
        sys.exit(1)
    
    ci_results = load_json_file(ci_results_path)
    
    # Combine results
    final_output = {
        'r2_score': ci_results.get('r2_score', train_results.get('r2_score', 0.0)),
        'ci_lower': ci_results.get('ci_lower', 0.0),
        'ci_upper': ci_results.get('ci_upper', 0.0),
        'p_value': train_results.get('p_value', 1.0),
        'f_statistic': train_results.get('f_statistic', 0.0),
        'f_p_value': train_results.get('f_p_value', 1.0),
        'feature_importances': train_results.get('feature_importances', [])
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    print(f"Model output saved to {output_path}")

if __name__ == '__main__':
    main()
