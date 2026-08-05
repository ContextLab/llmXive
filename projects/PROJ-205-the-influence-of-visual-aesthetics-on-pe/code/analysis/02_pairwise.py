import os
import sys
import json
from pathlib import Path
import random
import numpy as np
import pandas as pd
from scipy import stats

# Seed pinning for reproducibility (Task T031)
_SEED = 42
random.seed(_SEED)
np.random.seed(_SEED)

def get_project_root():
    """Returns the root path of the project."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_wide_data(csv_path: str) -> pd.DataFrame:
    """
    Loads the wide-format data.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Wide data file not found: {csv_path}")
    return pd.read_csv(csv_path)

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculates Cohen's d effect size for two paired samples.
    d = mean(diff) / std(diff)
    """
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for paired test.")
    
    diff = group1 - group2
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    
    if std_diff == 0:
        return 0.0
    
    return mean_diff / std_diff

def run_pairwise_tests_with_effects(df: pd.DataFrame, dv_suffix: str = '_credibility', alpha: float = 0.05) -> list:
    """
    Runs pairwise t-tests and calculates Cohen's d.
    """
    condition_names = ['professional', 'minimalist', 'low_quality', 'neutral']
    comparisons = []
    
    data_dict = {}
    for cond in condition_names:
        col_name = f"condition_{cond}{dv_suffix}"
        data_dict[cond] = df[col_name].dropna().values
    
    n_comparisons = len(condition_names) * (len(condition_names) - 1) // 2
    
    for i in range(len(condition_names)):
        for j in range(i + 1, len(condition_names)):
            cond_a = condition_names[i]
            cond_b = condition_names[j]
            
            data_a = data_dict[cond_a]
            data_b = data_dict[cond_b]
            
            if len(data_a) == 0 or len(data_b) == 0:
                continue
            
            # Paired t-test
            t_stat, p_val = stats.ttest_rel(data_a, data_b)
            
            # Cohen's d
            cohens_d = calculate_cohens_d(data_a, data_b)
            
            # Bonferroni correction
            corrected_p = p_val * n_comparisons
            if corrected_p > 1.0:
                corrected_p = 1.0
            
            comparisons.append({
                'condition_a': cond_a,
                'condition_b': cond_b,
                't_statistic': float(t_stat),
                'raw_p_value': float(p_val),
                'bonferroni_corrected_p': float(corrected_p),
                'cohens_d': float(cohens_d),
                'significant': corrected_p < alpha
            })
    
    return comparisons

def main():
    """
    Main entry point for pairwise analysis.
    """
    project_root = get_project_root()
    wide_csv = project_root / 'data' / 'processed' / 'wide_submissions.csv'
    output_json = project_root / 'data' / 'processed' / 'pairwise_results.json'
    
    if not wide_csv.exists():
        print(f"Error: Wide data not found at {wide_csv}", file=sys.stderr)
        sys.exit(1)
    
    df = load_wide_data(str(wide_csv))
    
    results = run_pairwise_tests_with_effects(df)
    
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Pairwise analysis complete. Results saved to {output_json}")

if __name__ == '__main__':
    main()
