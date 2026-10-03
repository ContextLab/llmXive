import os
import sys
import json
import argparse
import warnings
import numpy as np
from pathlib import Path
import pandas as pd
import pingouin as pg
from typing import Optional, Dict, Any

# Import seed enforcement from helpers
from utils.helpers import set_reproducibility_seed, get_project_root

# Set seed at the very start of the script
set_reproducibility_seed()

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_anova_results_path() -> Path:
    """Returns the path to the ANOVA results JSON file."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_pairwise_results_path() -> Path:
    """Returns the path to the pairwise results JSON file."""
    return get_project_root() / "data" / "processed" / "pairwise_results.json"

def get_cleaned_csv_path() -> Path:
    """Returns the path to the cleaned CSV file."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def load_wide_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads the wide-format data for pairwise tests."""
    if input_path is None:
        input_path = get_cleaned_csv_path()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Pivot if needed
    if 'stimulus_id' in df.columns:
        df = df.pivot_table(
            index='participant_id',
            columns='stimulus_id',
            values='rating_credibility',
            aggfunc='mean'
        ).reset_index()
    
    return df

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calculates Cohen's d for two groups."""
    mean_diff = group1.mean() - group2.mean()
    pooled_std = np.sqrt((group1.std()**2 + group2.std()**2) / 2)
    if pooled_std == 0:
        return 0.0
    return float(mean_diff / pooled_std)

def bootstrap_cohens_d(group1: pd.Series, group2: pd.Series, n_boot: int = 1000) -> Dict[str, float]:
    """Calculates bootstrapped Cohen's d with confidence intervals."""
    cohens_d_values = []
    for _ in range(n_boot):
        sample1 = group1.sample(n=len(group1), replace=True)
        sample2 = group2.sample(n=len(group2), replace=True)
        cohens_d_values.append(calculate_cohens_d(sample1, sample2))
    
    return {
        "mean": float(np.mean(cohens_d_values)),
        "ci_lower": float(np.percentile(cohens_d_values, 2.5)),
        "ci_upper": float(np.percentile(cohens_d_values, 97.5))
    }

def apply_bonferroni(p_values: List[float]) -> List[float]:
    """Applies Bonferroni correction to p-values."""
    m = len(p_values)
    return [min(p * m, 1.0) for p in p_values]

def apply_fdr_bh(p_values: List[float]) -> List[float]:
    """Applies Benjamini-Hochberg FDR correction to p-values."""
    from statsmodels.stats.multitest import multipletests
    _, corrected_p, _, _ = multipletests(p_values, method='fdr_bh')
    return corrected_p.tolist()

def run_pairwise_tests_with_effects(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs pairwise t-tests with effect sizes."""
    # Melt data for pairwise tests
    df_long = df.melt(
        id_vars=['participant_id'],
        var_name='condition',
        value_name='credibility'
    )
    
    # Run pairwise t-tests with Bonferroni correction
    pairwise_result = pg.pairwise_ttests(
        data=df_long,
        dv='credibility',
        within='condition',
        subject='participant_id',
        padjust='bonf'
    )
    
    pairwise_comparisons = []
    for _, row in pairwise_result.iterrows():
        cohen_d = float(row['cohen-d']) if pd.notna(row['cohen-d']) else 0.0
        pairwise_comparisons.append({
            "comparison": f"{row['A']}_vs_{row['B']}",
            "p_value": float(row['p-corr']),
            "cohen_d": cohen_d,
            "significant": bool(row['sig'])
        })
    
    return {
        "pairwise_comparisons": pairwise_comparisons
    }

def main():
    """Main entry point for the pairwise tests script."""
    parser = argparse.ArgumentParser(description='Run pairwise t-tests')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else get_cleaned_csv_path()
    output_path = Path(args.output) if args.output else get_pairwise_results_path()
    
    try:
        # Load data
        print(f"Loading data from {input_path}...")
        df = load_wide_data(input_path)
        
        # Run pairwise tests
        results = run_pairwise_tests_with_effects(df)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Pairwise results saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
