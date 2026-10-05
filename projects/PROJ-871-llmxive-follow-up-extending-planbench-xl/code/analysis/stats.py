import scipy.stats
from typing import Dict, Tuple, Any
from utils.config import get_path
from analysis.log_parser import get_aggregated_counts

def calculate_statistical_significance(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
    """Calculate statistical significance between baseline and augmented agents."""
    from pathlib import Path
    
    baseline_counts, augmented_counts = get_aggregated_counts(baseline_path, augmented_path)
    
    n_baseline = baseline_counts['success'] + baseline_counts['failure']
    n_augmented = augmented_counts['success'] + augmented_counts['failure']
    
    # Total tasks
    n = n_baseline  # Assuming same tasks for both
    
    if n < 30:
        # Fisher's Exact Test
        table = [
            [baseline_counts['success'], baseline_counts['failure']],
            [augmented_counts['success'], augmented_counts['failure']]
        ]
        oddsratio, p_value = scipy.stats.fisher_exact(table)
        test_type = "Fisher's Exact Test"
    else:
        # Two-proportion z-test
        success_counts = [baseline_counts['success'], augmented_counts['success']]
        nobs = [n_baseline, n_augmented]
        stat, p_value = scipy.stats.proportions_ztest(success_counts, nobs)
        test_type = "Two-proportion z-test"
    
    # Determine conclusion
    alpha = 0.05
    significant = p_value < alpha
    conclusion = "Augmented agent performs significantly better" if significant else "No significant difference detected"
    
    return {
        'test_type': test_type,
        'p_value': p_value,
        'significant': significant,
        'conclusion': conclusion,
        'baseline_success_rate': baseline_counts['success'] / n_baseline if n_baseline else 0,
        'augmented_success_rate': augmented_counts['success'] / n_augmented if n_augmented else 0
    }

def main():
    """Main entry point for statistical analysis."""
    baseline_path = get_path('data/logs/baseline_execution.jsonl')
    augmented_path = get_path('data/logs/augmented_execution.jsonl')
    
    result = calculate_statistical_significance(baseline_path, augmented_path)
    print(f"Statistical Analysis Result: {result}")

if __name__ == "__main__":
    main()
