import os
import sys
import json
import argparse
import random
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

def get_cleaned_csv_path() -> Path:
    """Returns the path to the cleaned CSV file."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_anova_results_path() -> Path:
    """Returns the path to the ANOVA results JSON file."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def load_wide_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads the wide-format data for ANOVA."""
    if input_path is None:
        input_path = get_cleaned_csv_path()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure wide format for ANOVA
    # Assuming columns are named rating_credibility_professional, rating_credibility_minimalist, etc.
    # This is a simplified version; actual implementation would depend on data structure
    
    # Pivot if needed
    if 'stimulus_id' in df.columns:
        df = df.pivot_table(
            index='participant_id',
            columns='stimulus_id',
            values='rating_credibility',
            aggfunc='mean'
        ).reset_index()
    
    return df

def calculate_partial_eta_squared(anova_result: pd.DataFrame) -> float:
    """Calculates partial eta squared from ANOVA results."""
    # Extract SS (sum of squares) values
    if 'SS' in anova_result.columns:
        ss_effect = anova_result['SS'].iloc[0]
        ss_error = anova_result['SS'].iloc[1]
        eta_sq = ss_effect / (ss_effect + ss_error)
        return float(eta_sq)
    return 0.0

def run_repeated_measures_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs a repeated-measures ANOVA on the data."""
    # Melt the wide data back to long format for pingouin
    df_long = df.melt(
        id_vars=['participant_id'],
        var_name='condition',
        value_name='credibility'
    )
    
    # Run repeated-measures ANOVA
    anova_result = pg.rm_anova(
        data=df_long,
        dv='credibility',
        within='condition',
        subject='participant_id',
        detailed=True
    )
    
    # Calculate effect sizes
    f_statistic = float(anova_result['F'].iloc[0])
    p_value = float(anova_result['p-unc'].iloc[0])
    eta_squared = calculate_partial_eta_squared(anova_result)
    
    # Calculate Cohen's d for main effect (simplified)
    # In a real implementation, this would compare means across conditions
    cohen_d_main = 0.0  # Placeholder; would need actual calculation
    
    # Get degrees of freedom
    df_num = int(anova_result['DF'].iloc[0])
    df_denom = int(anova_result['DF'].iloc[1])
    
    return {
        "f_statistic": f_statistic,
        "p_value": p_value,
        "eta_squared": eta_squared,
        "cohen_d_main": cohen_d_main,
        "degrees_of_freedom": {"numerator": df_num, "denominator": df_denom}
    }

def run_conditional_pairwise_tests(df: pd.DataFrame, anova_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Runs pairwise t-tests if ANOVA is significant."""
    if anova_results["p_value"] >= 0.05:
        return None
    
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
    """Main entry point for the ANOVA script."""
    parser = argparse.ArgumentParser(description='Run repeated-measures ANOVA')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else get_cleaned_csv_path()
    output_path = Path(args.output) if args.output else get_anova_results_path()
    
    try:
        # Load data
        print(f"Loading data from {input_path}...")
        df = load_wide_data(input_path)
        
        # Run ANOVA
        anova_results = run_repeated_measures_anova(df)
        
        # Run pairwise tests conditionally
        pairwise_results = run_conditional_pairwise_tests(df, anova_results)
        if pairwise_results:
            anova_results.update(pairwise_results)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(anova_results, f, indent=2)
        
        print(f"ANOVA results saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
